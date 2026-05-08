<h1 align="center">
  <a href="https://github.com/posquit0/Awesome-CV" title="AwesomeCV Documentation">
    <img alt="AwesomeCV" src="https://github.com/posquit0/Awesome-CV/raw/master/icon.png" width="200px" height="200px" />
  </a>
  <br />
  Dylan Awesome CV
</h1>

<p align="center">
  LaTeX template for your outstanding job application
</p>

<div align="center">
  <a href="https://github.com/posquit0/Awesome-CV/actions/workflows/main.yml">
    <img alt="GitHub Actions" src="https://github.com/posquit0/Awesome-CV/actions/workflows/main.yml/badge.svg" />
  </a>
  <a href="https://raw.githubusercontent.com/posquit0/Awesome-CV/master/examples/resume.pdf">
    <img alt="Example Resume" src="https://img.shields.io/badge/resume-pdf-green.svg" />
  </a>
  <a href="https://raw.githubusercontent.com/posquit0/Awesome-CV/master/examples/cv.pdf">
    <img alt="Example CV" src="https://img.shields.io/badge/cv-pdf-green.svg" />
  </a>
  <a href="https://raw.githubusercontent.com/posquit0/Awesome-CV/master/examples/coverletter.pdf">
    <img alt="Example Coverletter" src="https://img.shields.io/badge/coverletter-pdf-green.svg" />
  </a>
</div>

<br />

## What is Awesome CV?

**Awesome CV** is LaTeX template for a **CV(Curriculum Vitae)**, **Résumé** or **Cover Letter** inspired by [Fancy CV](https://www.sharelatex.com/templates/cv-or-resume/fancy-cv). It is easy to customize your own template, especially since it is really written by a clean, semantic markup.


## Donate

Please help keep this project alive! Donations are welcome and will go towards further development of this project.

    PayPal: paypal.me/posquit0

*Thank you for your support!*

## Preview

#### Résumé

You can see [PDF](https://raw.githubusercontent.com/posquit0/Awesome-CV/master/examples/resume.pdf)

| Page. 1 | Page. 2 |
|:---:|:---:|
| [![Résumé](https://raw.githubusercontent.com/posquit0/Awesome-CV/master/examples/resume-0.png)](https://raw.githubusercontent.com/posquit0/Awesome-CV/master/examples/resume.pdf)  | [![Résumé](https://raw.githubusercontent.com/posquit0/Awesome-CV/master/examples/resume-1.png)](https://raw.githubusercontent.com/posquit0/Awesome-CV/master/examples/resume.pdf) |

#### Cover Letter

You can see [PDF](https://raw.githubusercontent.com/posquit0/Awesome-CV/master/examples/coverletter.pdf)

| Without Sections | With Sections |
|:---:|:---:|
| [![Cover Letter(Traditional)](https://raw.githubusercontent.com/posquit0/Awesome-CV/master/examples/coverletter-0.png)](https://raw.githubusercontent.com/posquit0/Awesome-CV/master/examples/coverletter.pdf)  | [![Cover Letter(Awesome)](https://raw.githubusercontent.com/posquit0/Awesome-CV/master/examples/coverletter-1.png)](https://raw.githubusercontent.com/posquit0/Awesome-CV/master/examples/coverletter.pdf) |


## Quick Start

* [**Edit Résumé on OverLeaf.com**](https://www.overleaf.com/latex/templates/awesome-cv/tvmzpvdjfqxp)
* [**Edit Cover Letter on OverLeaf.com**](https://www.overleaf.com/latex/templates/awesome-cv-cover-letter/pfzzjspkthbk)

**_Note:_ Above services do not guarantee up-to-date source code of Awesome CV**


## How to Use

#### Requirements

A full TeX distribution is assumed.  [Various distributions for different operating systems (Windows, Mac, \*nix) are available](http://tex.stackexchange.com/q/55437) but TeX Live is recommended.
You can [install TeX from upstream](https://tex.stackexchange.com/q/1092) (recommended; most up-to-date) or use `sudo apt-get install texlive-full` if you really want that.  (It's generally a few years behind.)

If you don't want to install the dependencies on your system, this can also be obtained via [Docker](https://docker.com).

#### Usage

At a command prompt, run

```bash
xelatex {your-cv}.tex
```

Or using docker:

```bash
docker run --rm --user $(id -u):$(id -g) -i -w "/doc" -v "$PWD":/doc texlive/texlive:latest make
```

In either case, this should result in the creation of ``{your-cv}.pdf``

## AI-Assisted Application Workflow

This repository includes BMad skills for turning a job description into an application-specific package. Use them from Codex by invoking the skill name in chat.

The application workflow keeps canonical resume sources under `resume/` separate from job-specific outputs under `JDs/`. For JD-specific applications, agents should edit only copied files in `JDs/<Job Name> - <Company>/` and leave `resume/resume_Dylan.tex` and `resume/sections/*.tex` unchanged.

### Available BMad agents

| Skill | Use it for |
| --- | --- |
| `$bmad-job-application-workflow` | End-to-end flow from job-posting URL to refined JD notes, tailored resume, and tailored cover letter. |
| `$bmad-cv-editor` | Resume/CV editing, rebuilding, or JD-specific tailoring. |
| `$bmad-cover-letter-writer` | Cover-letter drafting or tailoring from the resume and a JD workspace. |

> Note: this repo currently installs `$bmad-cover-letter-writer`, not `$bmad-cover-letter-editor`. If you ask for "cover letter editor", use `$bmad-cover-letter-writer`.

### From a JD URL with BMad

Ask Codex to run:

```text
$bmad-job-application-workflow
```

Then provide the job-posting URL when prompted. You can include title or company overrides if the posting is ambiguous:

```text
$bmad-job-application-workflow
https://example.com/job-posting
Title: Senior AI/ML Engineer
Company: Example Company
```

The skill crawls and validates the posting with `scripts/jd_from_url.py`, retries LinkedIn search URLs through their direct job URL when possible, creates and refines `JDs/<Job Name> - <Company>/jd-information.md`, then runs `$bmad-cv-editor` and `$bmad-cover-letter-writer` for that JD workspace.

Expected outputs:

- `JDs/<Job Name> - <Company>/jd-information.md`
- `JDs/<Job Name> - <Company>/jd-crawl-result.json`
- `JDs/<Job Name> - <Company>/tex/resume_Dylan.tex`
- `JDs/<Job Name> - <Company>/tex/sections/*.tex`
- `JDs/<Job Name> - <Company>/resume_Dylan.pdf`
- `JDs/<Job Name> - <Company>/Cover Letter <Company>.tex`
- `JDs/<Job Name> - <Company>/Cover Letter <Company>.pdf`

If the crawler cannot access a posting because it is private, blocked, dynamic, or behind a login page, paste the full JD text into chat and continue with the pasted-JD flow.

### From pasted JD text

1. Copy the full job description into the chat.
2. Ask `$bmad-cv-editor` to create a new CV version for that JD.
3. The CV editor should create `JDs/<Job Name> - <Company>/`, save the JD as `jd-information.md`, copy the resume source into that workspace, tailor only the copied files, and place the generated CV PDF in the same JD folder.
4. Ask `$bmad-cover-letter-writer` to create the cover letter for the same JD.
5. The cover letter writer should use `JDs/<Job Name> - <Company>/jd-information.md` as the targeting source and place both the `.tex` cover letter and generated PDF in that same JD folder.

The canonical resume under `resume/` should remain unchanged during JD-specific tailoring.

### Resume-only work

Use `$bmad-cv-editor` directly when you want to edit or rebuild the resume without a specific job posting:

```text
$bmad-cv-editor rebuild resume
```

For a general resume improvement request, the skill may edit canonical files under `resume/`. For a job-specific request, it should create or use a folder under `JDs/` and edit only the copied LaTeX files there.

Useful requests:

- `$bmad-cv-editor rebuild resume`
- `$bmad-cv-editor improve my resume for machine learning engineer roles`
- `$bmad-cv-editor tailor my resume for JDs/<Job Name> - <Company>/`

### Cover-letter-only work

Use `$bmad-cover-letter-writer` when a JD folder already exists and you only need the letter:

```text
$bmad-cover-letter-writer create a cover letter for JDs/<Job Name> - <Company>/
```

The writer reads `jd-information.md`, checks claims against the resume, creates or updates the cover-letter `.tex` file in the same JD folder, and builds the PDF when feasible.

### Verification checklist

After any application workflow, confirm:

- The JD folder exists under `JDs/`.
- `jd-information.md` has clean role details, priority requirements, tailoring notes, and unsupported requirements.
- The JD-specific resume PDF builds successfully.
- The cover-letter PDF builds successfully.
- Canonical resume files were not modified for JD-specific tailoring.
- Unsupported requirements are reported instead of claimed.


## Credit

[**LaTeX**](https://www.latex-project.org) is a fantastic typesetting program that a lot of people use these days, especially the math and computer science people in academia.

[**FontAwesome6 LaTeX Package**](https://github.com/braniii/fontawesome) is a LaTeX package that provides access to the [Font Awesome 6](https://fontawesome.com/v6/icons) icon set.

[**Roboto**](https://github.com/google/roboto) is the default font on Android and ChromeOS, and the recommended font for Google’s visual language, Material Design.

[**Source Sans Pro**](https://github.com/adobe-fonts/source-sans-pro) is a set of OpenType fonts that have been designed to work well in user interface (UI) environments.


## Contact

You are free to take my `.tex` file and modify it to create your own resume. Please don't use my resume for anything else without my permission, though!

If you have any questions, feel free to join me at [`#posquit0` on Freenode](irc://irc.freenode.net/posquit0) and ask away. Click [here](https://kiwiirc.com/client/irc.freenode.net/posquit0) to connect.

Good luck!


## Maintainers
- [posquit0](https://github.com/posquit0)
- [OJFord](https://github.com/OJFord)


## See Also

* [Awesome Identity](https://github.com/posquit0/hugo-awesome-identity) - A single-page Hugo theme to introduce yourself.
