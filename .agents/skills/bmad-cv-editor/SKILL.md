---
name: bmad-cv-editor
description: 'Edit and tailor the CV or resume in this repo using BMad-style structural and prose review. Use when the user says edit my cv, improve my resume, tailor my resume, rewrite resume bullets, or adapt the CV to a role.'
---

# BMad CV Editor

**Goal:** Edit the LaTeX CV/resume in this repository so it is sharper, more targeted, and still factually true.

**Default scope:** `resume/resume_Dylan.tex`, `resume/sections/*.tex`, and job-specific working copies under `JDs/`

## Core rules

- Preserve factual truth. Do not invent employers, titles, dates, metrics, degrees, or skills.
- Prefer stronger selection and phrasing over adding content.
- Tailor to a target role or job description when provided. If none is provided, make the resume stronger for general data/software roles.
- Keep the existing Awesome CV structure unless there is a clear reason to change section order or inclusion.
- For general resume improvements with no job description, edit the source `.tex` files directly.
- For job-specific tailoring, never modify `resume/resume_Dylan.tex` or the canonical `resume/sections/*.tex`. Create and edit a job-specific `.tex` copy instead so the original resume remains intact.
- Preserve valid LaTeX syntax and existing macros.

## Inputs

- `target_role` (optional): desired job title or direction
- `job_name` (optional): role title used for the JD workspace folder name
- `company` (optional): company name used for the JD workspace folder name
- `job_description` (optional): posting text or requirements to optimize for
- `focus` (optional): examples include `summary`, `experience bullets`, `skills`, `entire resume`
- `constraints` (optional): page limit, tone, geography, seniority, keywords to emphasize or avoid

## Workflow

### 1. Create the JD workspace when tailoring for a specific role

- When the request includes a new job description or asks to fine-tune the CV for a specific job, create `JDs/<Job Name> - <Company>/`.
- If `JDs/` does not exist yet, create it.
- Derive `<Job Name>` and `<Company>` from the request or the job description. Keep the folder name human-readable.
- Save the job description or extracted JD notes inside that folder as `jd-information.md`.
- Store all JD-specific PDF outputs for that application inside the same folder.

### 2. Create the editable LaTeX working copy

- For JD-specific tailoring, copy the active resume entrypoint and the section files it depends on into the JD folder before editing.
- Prefer a self-contained layout such as `JDs/<Job Name> - <Company>/tex/resume_Dylan.tex` plus copied section files under `JDs/<Job Name> - <Company>/tex/sections/`.
- Edit only those copied `.tex` files for the JD version.
- Do not modify `resume/resume_Dylan.tex` when producing a JD-specific resume.

### 3. Locate the active resume files

- Start with `resume/resume_Dylan.tex`.
- Read the included files under `resume/sections/` to find the sections currently compiled.
- If the user asks for a CV instead of the shorter resume and the repo has an alternate active entrypoint, follow that file's include graph.

### 4. Determine the editing target

- If the user provided a target role or job description, extract the priority themes, skills, and keywords.
- If not, assume the target is a concise, professional resume for data scientist / software engineer roles.
- Decide which sections matter most for the request before editing.

### 5. Run a structural pass first

- Apply the spirit of `bmad-editorial-review-structure` before line editing.
- Check whether the current section order and section inclusion serve the target role.
- Cut or condense low-signal material before rewriting bullets.
- Prefer recent, relevant, and outcome-oriented content.
- For resumes, aim for density and scanability; summary and top experience should carry the strongest signal.

### 6. Run a prose pass second

- Apply the spirit of `bmad-editorial-review-prose` within the chosen structure.
- Rewrite bullets to be direct, specific, and easy to scan.
- Prefer action + scope + result when the source supports it.
- Remove filler, hedging, weak self-descriptions, and awkward grammar.
- Replace vague claims with concrete language already supported by the source text.

### 7. Respect LaTeX and repo conventions

- Keep existing macros such as `\cvsection`, `\cventry`, `\cvitems`, `\cvskill`, and `\cvparagraph`.
- Keep comments only when they help preserve structure.
- Do not add dependencies or new build steps.
- If a section is not currently included by `resume/resume_Dylan.tex`, only edit it when the user asks or when it is necessary for the requested outcome.
- For JD-specific versions, preserve the original include structure when copying files so the variant can still compile cleanly.

### 8. Verify before finishing

- Re-read the edited sections for factual consistency and internal contradictions.
- Confirm the edited wording still matches the original evidence in the file.
- If feasible, run the relevant LaTeX build command and fix syntax issues before claiming completion.
- For JD-specific work, build the PDF from the copied JD-specific `.tex` entrypoint and place the output PDF in the same JD folder.

## Section-specific guidance

### Summary

- Avoid generic personality statements.
- Lead with present role, domain strengths, and what the candidate delivers.
- Keep it compact.

### Experience

- Prioritize bullets that show ownership, technical depth, shipped work, scale, business impact, or uncommon strength.
- Prefer bullets that open with a short bolded label when it improves scanability, for example `\item \textbf{ML Application Development:} ...`.
- Drop obvious tool lists from bullets when they are better expressed in `skills.tex`.
- Normalize tense and grammar.

### Skills

- Keep only skills the rest of the resume can support.
- Group skills so the target role is obvious in under five seconds.
- Remove stale, weak, or redundant entries when they dilute positioning.

## Output expectations

- For general resume improvements, make the edits directly in the canonical LaTeX source.
- For JD-specific tailoring, create a new folder under `JDs/`, save the JD information there, edit only the copied JD-specific `.tex` files, and place the resulting PDF CV files in that folder.
- In the final report, state:
  - what sections changed
  - which JD folder was created, if any
  - how the resume was repositioned
  - any facts or metrics that still need user confirmation
