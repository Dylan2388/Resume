#!/usr/bin/env python3
"""Crawl and normalize a job-description URL into a JD workspace."""

from __future__ import annotations

import argparse
import datetime as dt
import html
import json
import re
import shutil
import sys
from dataclasses import asdict, dataclass, field
from html.parser import HTMLParser
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import parse_qs, urlparse
from urllib.request import Request, urlopen


DEFAULT_USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"
)

LOGIN_TITLES = {"sign in", "login", "linkedin login", "join linkedin"}
LOGIN_MARKERS = {
    "sign in with apple",
    "sign in with a passkey",
    "new to linkedin",
    "join now",
    "cookie policy",
    "user agreement",
    "we've emailed a one-time link",
}
JOB_SIGNAL_PATTERNS = (
    r"\brequirements?\b",
    r"\bresponsibilit(?:y|ies)\b",
    r"\bqualifications?\b",
    r"\bemployment type\b",
    r"\bseniority level\b",
    r"\bprimary location\b",
    r"\bexperience\b",
    r"\bci/cd\b",
    r"\bmlops\b",
    r"\btehtävä\b",
    r"\bosaajaa\b",
    r"\bkokemusta\b",
    r"\bteknologiat\b",
)
LINKEDIN_DROP_LINES = {
    "skip to main content",
    "apply",
    "save",
    "report this job",
    "show more",
    "show less",
    "sign in with email",
    "or",
    "new to linkedin?",
    "join now",
    "sign in to access ai-powered advices",
    "sign in to evaluate your skills",
    "sign in to tailor your resume",
    "am i a good fit for this job?",
    "tailor my resume",
    "use ai to assess how you fit",
    "get ai-powered advice on this job and more exclusive features.",
}
LINKEDIN_STOP_LINES = {
    "similar jobs",
    "referrals increase your chances",
    "get notified about new",
}
TECH_KEYWORDS = (
    "AWS",
    "Azure",
    "GCP",
    "Snowflake",
    "Terraform",
    "Kubernetes",
    "Docker",
    "PyTorch",
    "TensorFlow",
    "Kubeflow",
    "MLflow",
    "DVC",
    "Jenkins",
    "CI/CD",
    "MLOps",
    "DevOps",
    "HPC",
    "GPU",
    "CPU",
    "Python",
    "Golang",
    "SQL",
)


@dataclass
class JobPosting:
    source_url: str
    fetched_url: str
    title: str
    company: str
    description: str
    location: str = ""
    employment_type: str = ""
    seniority: str = ""
    date_posted: str = ""
    valid_through: str = ""
    technologies: list[str] = field(default_factory=list)
    quality_warnings: list[str] = field(default_factory=list)


@dataclass
class CrawlAttempt:
    url: str
    status: str
    title: str = ""
    company: str = ""
    warnings: list[str] = field(default_factory=list)
    error: str = ""


@dataclass
class WorkspaceResult:
    status: str
    folder: str = ""
    jd_file: str = ""
    metadata_file: str = ""
    title: str = ""
    company: str = ""
    fetched_url: str = ""
    warnings: list[str] = field(default_factory=list)
    attempts: list[CrawlAttempt] = field(default_factory=list)


class JobHTMLParser(HTMLParser):
    """Small, dependency-free parser for common posting metadata and page text."""

    SKIP_TAGS = {"style", "noscript", "svg", "nav", "header", "footer", "form", "aside"}

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.title_text = ""
        self.h1_text = ""
        self.meta: dict[str, str] = {}
        self.json_ld_blocks: list[str] = []
        self.visible_text: list[str] = []
        self._skip_depth = 0
        self._in_title = False
        self._title_parts: list[str] = []
        self._heading_tag = ""
        self._heading_parts: list[str] = []
        self._in_json_ld = False
        self._json_ld_parts: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attrs_dict = {name.lower(): value or "" for name, value in attrs}

        if tag == "meta":
            key = (attrs_dict.get("property") or attrs_dict.get("name") or "").lower()
            content = attrs_dict.get("content", "").strip()
            if key and content:
                self.meta[key] = content
            return

        if tag == "script":
            script_type = attrs_dict.get("type", "").lower()
            if "ld+json" in script_type:
                self._in_json_ld = True
                self._json_ld_parts = []
            else:
                self._skip_depth += 1
            return

        if tag in self.SKIP_TAGS:
            self._skip_depth += 1
            return

        if tag == "title":
            self._in_title = True
            self._title_parts = []
            return

        if tag in {"h1", "h2"} and not self._heading_tag:
            self._heading_tag = tag
            self._heading_parts = []

    def handle_endtag(self, tag: str) -> None:
        if tag == "script" and self._in_json_ld:
            block = "".join(self._json_ld_parts).strip()
            if block:
                self.json_ld_blocks.append(block)
            self._in_json_ld = False
            self._json_ld_parts = []
            return

        if tag == "script" and self._skip_depth:
            self._skip_depth -= 1
            return

        if tag in self.SKIP_TAGS and self._skip_depth:
            self._skip_depth -= 1
            return

        if tag == "title" and self._in_title:
            self.title_text = normalize_space(" ".join(self._title_parts))
            self._in_title = False
            return

        if tag == self._heading_tag:
            heading = normalize_space(" ".join(self._heading_parts))
            if tag == "h1" and not self.h1_text:
                self.h1_text = heading
            self._heading_tag = ""
            self._heading_parts = []

    def handle_data(self, data: str) -> None:
        if self._in_json_ld:
            self._json_ld_parts.append(data)
            return

        if self._skip_depth:
            return

        if self._in_title:
            self._title_parts.append(data)

        if self._heading_tag:
            self._heading_parts.append(data)

        text = normalize_space(data)
        if text:
            self.visible_text.append(text)


class TextHTMLParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.parts: list[str] = []

    def handle_data(self, data: str) -> None:
        text = normalize_space(data)
        if text:
            self.parts.append(text)


def normalize_space(value: str) -> str:
    return re.sub(r"\s+", " ", html.unescape(value or "")).strip()


def normalize_multiline(value: str) -> str:
    lines = [normalize_space(line) for line in re.split(r"[\r\n]+", value or "")]
    return "\n".join(line for line in lines if line)


def html_fragment_to_text(value: str) -> str:
    parser = TextHTMLParser()
    parser.feed(value or "")
    text = "\n".join(parser.parts)
    return normalize_multiline(text or normalize_space(value))


def compact_page_text(parts: list[str], max_chars: int) -> str:
    text = normalize_multiline("\n".join(parts))
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text[:max_chars].rstrip()


def load_json_ld(blocks: list[str]) -> list[dict[str, Any]]:
    loaded: list[dict[str, Any]] = []
    for block in blocks:
        try:
            value = json.loads(block)
        except json.JSONDecodeError:
            continue
        loaded.extend(flatten_json_ld(value))
    return loaded


def flatten_json_ld(value: Any) -> list[dict[str, Any]]:
    if isinstance(value, list):
        items: list[dict[str, Any]] = []
        for entry in value:
            items.extend(flatten_json_ld(entry))
        return items
    if not isinstance(value, dict):
        return []

    items = [value]
    graph = value.get("@graph")
    if isinstance(graph, list):
        for entry in graph:
            items.extend(flatten_json_ld(entry))
    return items


def find_job_posting(items: list[dict[str, Any]]) -> dict[str, Any] | None:
    for item in items:
        item_type = item.get("@type", "")
        if isinstance(item_type, list):
            types = {str(entry).lower() for entry in item_type}
        else:
            types = {str(item_type).lower()}
        if "jobposting" in types:
            return item
    return None


def as_text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return normalize_space(value)
    if isinstance(value, (int, float)):
        return str(value)
    if isinstance(value, list):
        return ", ".join(filter(None, (as_text(entry) for entry in value)))
    if isinstance(value, dict):
        for key in ("name", "text", "value", "addressLocality", "addressCountry"):
            if key in value:
                text = as_text(value[key])
                if text:
                    return text
    return ""


def extract_company(job: dict[str, Any]) -> str:
    org = job.get("hiringOrganization") or job.get("organization")
    if isinstance(org, list):
        org = org[0] if org else {}
    if isinstance(org, dict):
        return as_text(org.get("name"))
    return as_text(org)


def extract_location(job: dict[str, Any]) -> str:
    locations = job.get("jobLocation") or job.get("applicantLocationRequirements")
    if not locations:
        return ""
    if not isinstance(locations, list):
        locations = [locations]

    rendered: list[str] = []
    for location in locations:
        if isinstance(location, dict):
            address = location.get("address", location)
            if isinstance(address, dict):
                parts = [
                    as_text(address.get("addressLocality")),
                    as_text(address.get("addressRegion")),
                    as_text(address.get("addressCountry")),
                ]
                rendered.append(", ".join(part for part in parts if part))
            else:
                rendered.append(as_text(address))
        else:
            rendered.append(as_text(location))
    return ", ".join(part for part in rendered if part)


def clean_title(title: str) -> str:
    title = normalize_space(title)
    title = re.sub(r"\s*\|\s*.*$", "", title)
    title = re.sub(r"\s+[-–—]\s+Careers?.*$", "", title, flags=re.IGNORECASE)
    return title.strip(" -–—|")


def infer_company_from_url(url: str) -> str:
    host = urlparse(url).netloc.lower()
    host = host.removeprefix("www.")
    if not host:
        return "Unknown Company"
    name = host.split(".")[0]
    return name.replace("-", " ").title()


def linkedin_direct_url(url: str) -> str:
    parsed = urlparse(url)
    if "linkedin.com" not in parsed.netloc:
        return ""
    query = parse_qs(parsed.query)
    job_ids = query.get("currentJobId") or query.get("jobId")
    if job_ids and job_ids[0].isdigit():
        return f"https://www.linkedin.com/jobs/view/{job_ids[0]}/"
    match = re.search(r"/jobs/view/(\d+)", parsed.path)
    if match:
        return f"https://www.linkedin.com/jobs/view/{match.group(1)}/"
    return ""


def candidate_urls(url: str) -> list[str]:
    direct = linkedin_direct_url(url)
    urls = [direct, url] if direct and direct != url else [url]
    deduped: list[str] = []
    for candidate in urls:
        if candidate and candidate not in deduped:
            deduped.append(candidate)
    return deduped


def fetch_url(url: str, *, timeout: int, user_agent: str) -> str:
    request = Request(url, headers={"User-Agent": user_agent})
    try:
        with urlopen(request, timeout=timeout) as response:
            charset = response.headers.get_content_charset() or "utf-8"
            return response.read().decode(charset, errors="replace")
    except HTTPError as exc:
        raise RuntimeError(f"HTTP {exc.code} while fetching {url}") from exc
    except URLError as exc:
        raise RuntimeError(f"Could not fetch {url}: {exc.reason}") from exc


def infer_linkedin_company(text: str, title: str) -> str:
    first_line = text.splitlines()[0] if text.splitlines() else ""
    hiring_match = re.match(r"(.+?) hiring .+? \| LinkedIn$", first_line, flags=re.IGNORECASE)
    if hiring_match:
        return normalize_space(hiring_match.group(1))

    lines = [line.strip() for line in text.splitlines() if line.strip()]
    for index, line in enumerate(lines[:-1]):
        if line.lower() == "role at":
            return lines[index + 1]
        if line == title and index + 1 < len(lines):
            candidate = lines[index + 1]
            if candidate.lower() not in LOGIN_TITLES and len(candidate) <= 80:
                return candidate
    return ""


def extract_line_after(text: str, label: str) -> str:
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    for index, line in enumerate(lines[:-1]):
        if line.lower() == label.lower():
            return lines[index + 1]
    return ""


def extract_apply_by(text: str) -> str:
    patterns = [
        r"viimeist[aä]{2}n\s+(\d{1,2}\.\d{1,2}\.\d{4})",
        r"apply by[:\s]+([A-Za-z0-9 .,/-]+)",
        r"valid through[:\s]+([A-Za-z0-9 .,/-]+)",
    ]
    for pattern in patterns:
        match = re.search(pattern, text, flags=re.IGNORECASE)
        if match:
            return normalize_space(match.group(1))
    return ""


def clean_linkedin_text(text: str) -> str:
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    primary_index = next((index for index, line in enumerate(lines) if line.lower() == "primary location:"), None)
    if primary_index is not None:
        lines = lines[primary_index:]

    cleaned: list[str] = []
    skip_next = 0
    for line in lines:
        lowered = line.lower()
        if skip_next:
            skip_next -= 1
            continue
        if lowered in LINKEDIN_STOP_LINES or any(lowered.startswith(stop) for stop in LINKEDIN_STOP_LINES):
            break
        if lowered in LINKEDIN_DROP_LINES:
            continue
        if lowered in {", and", "cookie policy", "role at"}:
            continue
        if lowered.startswith("join or sign in") or lowered.startswith("join to apply"):
            continue
        if lowered.startswith("by clicking continue"):
            skip_next = 3
            continue
        if lowered.startswith("see who ") or lowered.startswith("be among the first"):
            continue
        cleaned.append(line)
    return "\n".join(cleaned)


def extract_technologies(text: str) -> list[str]:
    found: list[str] = []
    for tech in TECH_KEYWORDS:
        if re.search(rf"(?<![A-Za-z0-9+#]){re.escape(tech)}(?![A-Za-z0-9+#])", text, flags=re.IGNORECASE):
            found.append(tech)
    return found


def validate_posting(posting: JobPosting, *, min_chars: int) -> list[str]:
    warnings: list[str] = []
    title_lower = posting.title.lower()
    description_lower = posting.description.lower()
    login_hits = [marker for marker in LOGIN_MARKERS if marker in description_lower]
    signal_hits = [
        pattern for pattern in JOB_SIGNAL_PATTERNS if re.search(pattern, posting.description, flags=re.IGNORECASE)
    ]

    if title_lower in LOGIN_TITLES or title_lower.startswith("sign in"):
        warnings.append("extracted title is a login/sign-in page")
    if len(posting.description) < min_chars:
        warnings.append(f"job description is too short ({len(posting.description)} characters)")
    if len(login_hits) >= 3 and len(signal_hits) < 2:
        warnings.append("page appears to be login chrome rather than a job posting")
    if "linkedin.com" in urlparse(posting.fetched_url).netloc and posting.company.lower() == "linkedin":
        warnings.append("company could not be inferred from LinkedIn posting")
    if not posting.company or posting.company == "Unknown Company":
        warnings.append("company could not be inferred")
    if not posting.title or posting.title == "Job Description":
        warnings.append("role title could not be inferred")
    return warnings


def extract_posting_from_html(
    body: str,
    source_url: str,
    fetched_url: str,
    *,
    fallback_title: str = "",
    fallback_company: str = "",
    max_chars: int = 60000,
) -> JobPosting:
    parser = JobHTMLParser()
    parser.feed(body)

    job = find_job_posting(load_json_ld(parser.json_ld_blocks)) or {}
    meta_title = parser.meta.get("og:title") or parser.meta.get("twitter:title")
    title = fallback_title or as_text(job.get("title")) or parser.h1_text or meta_title or parser.title_text
    title = clean_title(title) or "Job Description"

    raw_description = html_fragment_to_text(as_text(job.get("description")))
    if not raw_description:
        raw_description = compact_page_text(parser.visible_text, max_chars=max_chars)

    description = clean_linkedin_text(raw_description) if "linkedin.com" in urlparse(fetched_url).netloc else raw_description
    company = fallback_company or extract_company(job)
    if not company and "linkedin.com" in urlparse(fetched_url).netloc:
        company = infer_linkedin_company(raw_description, title) or infer_linkedin_company(description, title)
    if not company:
        company = infer_company_from_url(fetched_url)

    location = extract_location(job) or extract_line_after(raw_description, "Primary location:") or extract_line_after(description, title)
    employment_type = as_text(job.get("employmentType")) or extract_line_after(description, "Employment type")
    seniority = extract_line_after(description, "Seniority level")
    valid_through = as_text(job.get("validThrough")) or extract_apply_by(description)

    posting = JobPosting(
        source_url=source_url,
        fetched_url=fetched_url,
        title=title,
        company=company,
        description=description[:max_chars].rstrip(),
        location=location,
        employment_type=employment_type,
        seniority=seniority,
        date_posted=as_text(job.get("datePosted")),
        valid_through=valid_through,
        technologies=extract_technologies(description),
    )
    return posting


def fetch_best_posting(
    url: str,
    *,
    fallback_title: str,
    fallback_company: str,
    timeout: int,
    user_agent: str,
    max_chars: int,
    min_chars: int,
) -> tuple[JobPosting | None, list[CrawlAttempt]]:
    attempts: list[CrawlAttempt] = []
    for fetched_url in candidate_urls(url):
        try:
            body = fetch_url(fetched_url, timeout=timeout, user_agent=user_agent)
            posting = extract_posting_from_html(
                body,
                url,
                fetched_url,
                fallback_title=fallback_title,
                fallback_company=fallback_company,
                max_chars=max_chars,
            )
            warnings = validate_posting(posting, min_chars=min_chars)
            posting.quality_warnings = warnings
            attempts.append(
                CrawlAttempt(
                    url=fetched_url,
                    status="failed_quality_gate" if warnings else "success",
                    title=posting.title,
                    company=posting.company,
                    warnings=warnings,
                )
            )
            if not warnings:
                return posting, attempts
        except RuntimeError as exc:
            attempts.append(CrawlAttempt(url=fetched_url, status="fetch_failed", error=str(exc)))
    return None, attempts


def sanitize_path_component(value: str, *, fallback: str) -> str:
    value = normalize_space(value) or fallback
    value = re.sub(r"[/:\\]+", " ", value)
    value = re.sub(r"[^A-Za-z0-9 .,&()+_-]", "", value)
    value = normalize_space(value).strip(". ")
    return (value or fallback)[:90].rstrip()


def unique_folder(path: Path, *, overwrite: bool) -> Path:
    if overwrite or not path.exists():
        return path

    for index in range(2, 100):
        candidate = path.with_name(f"{path.name} {index}")
        if not candidate.exists():
            return candidate
    raise RuntimeError(f"Could not find an unused folder name for {path}")


def render_jd_markdown(posting: JobPosting) -> str:
    generated_at = dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%d %H:%M:%S %Z")
    details = [
        ("Company", posting.company),
        ("Role", posting.title),
        ("Location", posting.location),
        ("Employment Type", posting.employment_type),
        ("Seniority", posting.seniority),
        ("Date Posted", posting.date_posted),
        ("Apply By", posting.valid_through),
        ("Source URL", posting.source_url),
        ("Fetched URL", posting.fetched_url),
        ("Crawled At", generated_at),
    ]
    detail_lines = [f"- {label}: {value}" for label, value in details if value]
    technologies = "\n".join(f"- {tech}" for tech in posting.technologies) or "- Review JD text manually"
    warnings = "\n".join(f"- {warning}" for warning in posting.quality_warnings) or "- None"
    description = posting.description or "No readable job description text was extracted."
    return (
        f"# {posting.title} - {posting.company}\n\n"
        "## Role\n\n"
        f"{posting.title} at {posting.company}."
        + (f" Location: {posting.location}." if posting.location else "")
        + "\n\n"
        "## Application Details\n\n"
        + "\n".join(detail_lines)
        + "\n\n"
        "## Technologies Mentioned\n\n"
        f"{technologies}\n\n"
        "## Extracted Job Description\n\n"
        f"{description}\n\n"
        "## Tailoring Notes Draft\n\n"
        "- Refine this section before CV and cover-letter tailoring.\n"
        "- Extract priority requirements, nice-to-haves, and unsupported requirements from the JD text.\n"
        "- Preserve factual truth from the resume; do not invent tools, locations, metrics, language fluency, or eligibility details.\n\n"
        "## Crawler Notes\n\n"
        f"{warnings}\n"
    )


def create_workspace(posting: JobPosting, *, output_dir: Path, overwrite: bool) -> WorkspaceResult:
    title = sanitize_path_component(posting.title, fallback="Job Description")
    company = sanitize_path_component(posting.company, fallback="Unknown Company")
    folder = unique_folder(output_dir / f"{title} - {company}", overwrite=overwrite)
    folder.mkdir(parents=True, exist_ok=True)

    jd_file = folder / "jd-information.md"
    metadata_file = folder / "jd-crawl-result.json"
    jd_file.write_text(render_jd_markdown(posting), encoding="utf-8")

    result = WorkspaceResult(
        status="success",
        folder=folder.as_posix(),
        jd_file=jd_file.as_posix(),
        metadata_file=metadata_file.as_posix(),
        title=posting.title,
        company=posting.company,
        fetched_url=posting.fetched_url,
        warnings=posting.quality_warnings,
    )
    metadata_file.write_text(json.dumps(result_to_dict(result), indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return result


def result_to_dict(result: WorkspaceResult) -> dict[str, Any]:
    data = asdict(result)
    data["attempts"] = [asdict(attempt) for attempt in result.attempts]
    return data


def display_path(path: str, *, root: Path) -> str:
    path_obj = Path(path)
    try:
        return path_obj.relative_to(root).as_posix()
    except ValueError:
        return path_obj.as_posix()


def is_failed_generated_folder(path: Path) -> bool:
    metadata = path / "jd-crawl-result.json"
    if metadata.exists():
        try:
            data = json.loads(metadata.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return False
        return data.get("status") != "success"

    jd_file = path / "jd-information.md"
    if not jd_file.exists():
        return False
    text = jd_file.read_text(encoding="utf-8", errors="ignore").lower()
    has_outputs = any(path.glob("*.pdf")) or (path / "tex").exists()
    return not has_outputs and (
        "# sign in - linkedin" in text
        or "linkedin login, sign in" in text
        or "company: linkedin" in text and "role at" not in text
    )


def cleanup_failed(output_dir: Path, *, dry_run: bool) -> list[str]:
    removed: list[str] = []
    if not output_dir.exists():
        return removed
    for child in sorted(output_dir.iterdir()):
        if not child.is_dir() or not is_failed_generated_folder(child):
            continue
        removed.append(child.as_posix())
        if not dry_run:
            shutil.rmtree(child)
    return removed


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Crawl, validate, and normalize JD URL(s) into JDs/<Role> - <Company>/."
    )
    parser.add_argument("urls", nargs="*", help="Job-description URL(s) to crawl.")
    parser.add_argument("--output-dir", default="JDs", help="Directory for generated JD workspaces.")
    parser.add_argument("--title", help="Override the extracted role title. Only valid with one URL.")
    parser.add_argument("--company", help="Override the extracted company. Only valid with one URL.")
    parser.add_argument("--timeout", type=int, default=20, help="Fetch timeout in seconds.")
    parser.add_argument("--max-chars", type=int, default=60000, help="Maximum extracted JD text characters.")
    parser.add_argument("--min-chars", type=int, default=500, help="Minimum description length for quality gate.")
    parser.add_argument("--overwrite", action="store_true", help="Write into an existing matching JD folder.")
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON only.")
    parser.add_argument("--cleanup-failed", action="store_true", help="Remove failed generated JD folders.")
    parser.add_argument("--cleanup-dry-run", action="store_true", help="List failed generated folders without removing.")
    parser.add_argument("--user-agent", default=DEFAULT_USER_AGENT, help="HTTP User-Agent for crawling.")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])
    if len(args.urls) > 1 and (args.title or args.company):
        print("--title and --company overrides are only supported with one URL.", file=sys.stderr)
        return 2

    repo_root = Path.cwd()
    output_dir = Path(args.output_dir)
    if not output_dir.is_absolute():
        output_dir = repo_root / output_dir

    if args.cleanup_failed:
        removed = cleanup_failed(output_dir, dry_run=args.cleanup_dry_run)
        payload = {"status": "cleanup", "dry_run": args.cleanup_dry_run, "removed": removed}
        if args.json:
            print(json.dumps(payload, indent=2, ensure_ascii=False))
        else:
            action = "Would remove" if args.cleanup_dry_run else "Removed"
            for path in removed:
                print(f"{action}: {display_path(path, root=repo_root)}")
            if not removed:
                print("No failed generated JD folders found.")
        return 0

    if not args.urls:
        print("At least one JD URL is required unless --cleanup-failed is used.", file=sys.stderr)
        return 2

    final_results: list[WorkspaceResult] = []
    exit_code = 0
    for url in args.urls:
        posting, attempts = fetch_best_posting(
            url,
            fallback_title=args.title or "",
            fallback_company=args.company or "",
            timeout=args.timeout,
            user_agent=args.user_agent,
            max_chars=args.max_chars,
            min_chars=args.min_chars,
        )
        if not posting:
            result = WorkspaceResult(
                status="failed",
                warnings=["no candidate URL passed the quality gate"],
                attempts=attempts,
            )
            final_results.append(result)
            exit_code = 1
            continue

        result = create_workspace(posting, output_dir=output_dir, overwrite=args.overwrite)
        result.attempts = attempts
        Path(result.metadata_file).write_text(
            json.dumps(result_to_dict(result), indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
        final_results.append(result)

    if args.json:
        payload: dict[str, Any] = {"status": "success" if exit_code == 0 else "failed"}
        payload["results"] = [result_to_dict(result) for result in final_results]
        print(json.dumps(payload, indent=2, ensure_ascii=False))
    else:
        for result in final_results:
            if result.status != "success":
                print("error: no candidate URL passed the quality gate", file=sys.stderr)
                for attempt in result.attempts:
                    detail = "; ".join(attempt.warnings) or attempt.error or "unknown error"
                    print(f"- {attempt.url}: {attempt.status}: {detail}", file=sys.stderr)
                continue
            print(f"Created JD workspace: {display_path(result.folder, root=repo_root)}")
            print(f"JD information: {display_path(result.jd_file, root=repo_root)}")
            print(f"Crawl metadata: {display_path(result.metadata_file, root=repo_root)}")
            print(f"Fetched URL: {result.fetched_url}")

    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
