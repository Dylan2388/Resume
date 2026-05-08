---
name: bmad-job-application-workflow
description: 'Automate a job-application workflow from a pasted job-description link: ask for the JD URL, crawl and validate it with the local Python helper, refine jd-information.md, then invoke bmad-cv-editor and bmad-cover-letter-writer for the generated application workspace.'
---

# BMad Job Application Workflow

**Goal:** Turn a job-description URL into a complete JD-specific application package: clean JD notes, tailored CV, and tailored cover letter.

**Primary helper:** `scripts/jd_from_url.py`

**Downstream skills:** `$bmad-cv-editor`, then `$bmad-cover-letter-writer`

## Workflow

### 1. Ask for the JD link on init

- If the user did not provide a URL in the request, ask for the JD link and stop until they provide it.
- If the user provided multiple URLs, process them one at a time unless they explicitly ask for batch processing.
- Accept optional user overrides for `title` and `company` when the crawler cannot infer them cleanly.

### 2. Crawl, retry, and validate

Run the local helper from the repo root and prefer JSON output:

```bash
python3 scripts/jd_from_url.py --json "<JD_URL>"
```

Use overrides only when needed:

```bash
python3 scripts/jd_from_url.py --json --title "<Role>" --company "<Company>" "<JD_URL>"
```

The helper should:

- Retry LinkedIn search URLs with `currentJobId` as `https://www.linkedin.com/jobs/view/<id>/`.
- Reject login pages, empty pages, and low-quality extraction before creating a JD folder.
- Create `JDs/<Job Name> - <Company>/jd-information.md` only after the quality gate passes.
- Write `JDs/<Job Name> - <Company>/jd-crawl-result.json` with status, folder, JD path, fetched URL, warnings, and attempts.
- Avoid writing redundant workflow prompt files.

If all crawl attempts fail because the posting is blocked, dynamic, private, or low-quality, ask the user to paste the JD text. Then create `JDs/<Job Name> - <Company>/jd-information.md` manually from the pasted text and continue.

### 3. Refine `jd-information.md`

Before invoking CV or cover-letter skills, edit the generated JD notes into this structure:

- `Role`
- `Application Details`
- `Priority Requirements`
- `Technologies Mentioned`
- `Nice To Have`
- `Tailoring Notes`
- `Unsupported / Do Not Claim`
- `Crawler Notes`

Remove crawler residue such as sign-in text, cookie banners, duplicated headers, unrelated suggested jobs, and raw search-result chrome.

In `Unsupported / Do Not Claim`, list requirements that are not supported by the resume unless the user confirms them. Examples: unverified tools, cloud providers, language fluency, work authorization, management scope, or domain experience.

### 4. Invoke `$bmad-cv-editor`

Use the refined JD folder as the target. The CV step must:

- Read `JDs/<Job Name> - <Company>/jd-information.md`.
- Create or update the JD-specific resume workspace under `JDs/<Job Name> - <Company>/tex/`.
- Tailor only copied JD-specific `.tex` files.
- Avoid modifying `resume/resume_Dylan.tex` or canonical `resume/sections/*.tex`.
- Build the JD-specific resume PDF into the JD folder when feasible.

### 5. Invoke `$bmad-cover-letter-writer`

Use the same JD folder as the target. The cover-letter step must:

- Read `JDs/<Job Name> - <Company>/jd-information.md`.
- Create or update the cover letter `.tex` in the JD folder.
- Build the cover letter PDF into the JD folder when feasible.
- Preserve factual truth from the resume.
- By default, do not put gap disclosures directly in the cover letter. Report unsupported JD requirements in the final response unless the user explicitly asks for transparent gap language in the letter.

### 6. Cleanup

After the CV and cover letter are done:

- Remove failed folders created during the same workflow run.
- Remove redundant `bmad-workflow-prompt.md` files created by older helper versions when they are in the active JD folder or failed folders.
- You may run `python3 scripts/jd_from_url.py --cleanup-failed` to remove failed generated folders detected by metadata or legacy login-page notes.
- Do not delete unrelated existing application folders.

### 7. Finish with evidence

Report:

- JD folder created or updated
- CV files and PDF created or changed
- Cover letter files and PDF created or changed
- Verification performed
- Confirmation that canonical `resume/resume_Dylan.tex` and `resume/sections/*.tex` were not modified
- Any crawler limitations, unsupported JD requirements, or facts needing user confirmation
