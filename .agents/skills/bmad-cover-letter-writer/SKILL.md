---
name: bmad-cover-letter-writer
description: 'Write or tailor a cover letter in this repo using BMad-style structural and prose editing. Use when the user says write my cover letter, tailor a cover letter, create cover letter from my resume, or adapt a cover letter to a job description.'
---

# BMad Cover Letter Writer

**Goal:** Write or tailor a cover letter in this repository so it is credible, targeted, concise, and consistent with the resume.

**Primary sources:** `resume/resume_Dylan.tex`, `resume/sections/*.tex`, `coverletters/*.tex`, `JDs/*/jd-information.md`, and existing cover letters inside matching `JDs/*/` workspaces

**Default output location:** the matching `JDs/<Job Name> - <Company>/` folder when a JD workspace exists; `coverletters/` only when no JD workspace exists.

## Core rules

- Preserve factual truth. Do not invent employers, projects, metrics, degrees, visas, locations, referrals, or outcomes.
- Derive claims from the resume source unless the user gives newer facts.
- Tailor to the target role and company when provided.
- When a matching JD workspace exists under `JDs/`, read its `jd-information.md` and use it as the primary source for job-specific targeting.
- Prefer concrete evidence over generic enthusiasm.
- Keep the tone professional and specific, not flattering or theatrical.
- Preserve valid LaTeX syntax and existing Awesome CV macros.

## Inputs

- `target_role` (optional): the job title being pursued
- `company` (optional): employer name
- `jd_folder` (optional): a specific folder under `JDs/` whose `jd-information.md` should drive the letter
- `job_description` (optional): posting text or requirements
- `hiring_manager` (optional): recipient name
- `focus` (optional): examples include `new draft`, `opening`, `evidence paragraph`, `shorten`, `tailor existing draft`
- `constraints` (optional): geography, work authorization, page length, tone, keywords to include or avoid

## Workflow

### 1. Gather evidence from the repo first

- Read `resume/resume_Dylan.tex` and the currently included files in `resume/sections/`.
- Treat the resume as the default source of truth for identity, experience, and skills.
- If the request refers to an existing JD-specific application, locate the matching folder under `JDs/` and read `jd-information.md` from that folder before drafting.
- If `jd_folder` is provided, use `JDs/<jd_folder>/jd-information.md` as the primary job-targeting source.
- If a matching JD folder exists for the target role and company, prefer its `jd-information.md` over a separately pasted `job_description` unless the user provides newer information in the current message.
- Read `coverletters/example.tex` first when present; use it as the main local example for tone, layout, and macro usage.
- Use existing files in `coverletters/` as style and structure references, not as reusable factual content.

### 2. Choose the target file path

- For JD-specific applications with a matching `JDs/<Job Name> - <Company>/jd-information.md`, store the cover letter `.tex` and generated PDF in that same JD folder.
- If `jd_folder` is provided, store the cover letter beside `JDs/<jd_folder>/jd-information.md`.
- If no JD workspace exists, store new and edited cover letters under `coverletters/`.
- If the user names a target company, prefer a descriptive filename such as `Cover Letter <Company>.tex` inside the selected output folder.
- If editing an existing letter for the same company in the selected output folder, update that file instead of creating a duplicate.
- Do not write new cover letters under `examples/`.

### 3. Determine the persuasion strategy

- If `jd-information.md` is available, extract the top requirements, domain signals, company context, and likely screening keywords from that file first.
- If a job description is provided directly and no relevant `jd-information.md` exists, extract the top requirements, domain signals, and likely screening keywords from the provided text.
- Match those requirements against verifiable evidence from the resume.
- Select 2 to 4 strongest proof points; a cover letter should curate, not restate the whole resume.
- If no job description is provided, write a general-purpose letter for data scientist, software engineer, or machine learning engineer roles based on the strongest evidence in the resume.

### 4. Build structure before prose

- Use a tight structure:
  - opening: role, reason for writing, top-fit summary
  - evidence: 1 or 2 compact paragraphs with the strongest matching experience
  - closing: motivation, availability or next-step framing, polite close
- Remove filler sections that do not improve hiring signal.
- Keep the letter concise enough to scan quickly.

### 5. Write in BMad editorial style

- Apply the spirit of `bmad-editorial-review-structure` first, then `bmad-editorial-review-prose`.
- Prefer explicit fit statements backed by evidence.
- Avoid empty phrases such as "I am passionate", "I am excited", or "I believe I am a great fit" unless followed immediately by proof.
- Use direct, simple sentences.
- Reuse terminology from the job description only when the resume evidence supports it.

### 6. Respect Awesome CV letter conventions

- Keep or correctly set the letter metadata macros: `\recipient`, `\letterdate`, `\lettertitle`, `\letteropening`, `\letterclosing`, `\letterenclosure`.
- Keep content inside `\begin{cvletter}` and `\end{cvletter}`.
- Use `\lettersection{...}` only when it improves clarity; otherwise a continuous letter is acceptable.
- Keep personal details aligned with the resume unless the user provides updated contact information.

### 7. Verify before finishing

- Check the letter against the resume for unsupported claims or contradictions.
- Re-read for company-name mistakes, role-title mistakes, stale recruiter names, and leftover template placeholders.
- If feasible, run the LaTeX build for the cover letter and fix syntax issues before claiming completion.

## Writing guidance

### Opening

- State the target role quickly.
- Give one sharp reason the candidate fits.
- Avoid long self-introductions.

### Evidence paragraphs

- Use only the strongest, most relevant evidence.
- Prefer ownership, shipped systems, technical depth, measurable impact, or unusual domain fit.
- Do not turn the letter into a bullet list unless the user asks for that format.

### Closing

- Keep it brief.
- Reinforce fit or motivation with one concrete line.
- End with a normal professional close.

## Output expectations

- For JD-specific applications, create or edit the LaTeX cover letter source in the same folder as the matching `jd-information.md`.
- Place the generated cover letter PDF in that same JD folder.
- Use `coverletters/` only for general-purpose cover letters or when no JD workspace exists.
- In the final report, state:
  - which file was created or changed
  - which `jd-information.md` file was used, if any
  - how the letter was tailored
  - any facts, names, or placeholders that still need user confirmation
