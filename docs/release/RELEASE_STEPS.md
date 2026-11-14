# Release steps: GitHub and Zenodo (v1.0)

The authors approved the public release on 9 Nov 2026. Everything below is prepared. The two steps that need you are
marked **YOU**. Nothing is public until you do them.

**What v1.0 contains.** The committed project, exported with `git archive`.

**What v1.0 leaves out:**
- the course's assignment briefs (`docs/source_documents/`), which are not ours to publish;
- until the label audit is scored, the rater kit, the sealed LLM rater, the hidden execution-label key and the two
  older audit sheets. These go out in v1.1.

The secrets scan, which covers every staged file and any `.env`, is clean.

Prepared files:

| What | Full path |
|---|---|
| GitHub folder (5,202 files, about 550 MB) | `C:\Users\huzai\Downloads\Fast\Advance AI\Phase 3 and 4\dist\release\github\` |
| List of every file in it | `C:\Users\huzai\Downloads\Fast\Advance AI\Phase 3 and 4\dist\release\FILE_LIST.txt` |
| Zenodo upload (everything above, plus the two files too big for GitHub) | `C:\Users\huzai\Downloads\Fast\Advance AI\Phase 3 and 4\dist\release\zenodo_<commit>.zip` |

The zip is rebuilt after the DOI is filled in, so its name changes. Upload the newest one.

## Step 1 — YOU: reserve the DOI on Zenodo (about 5 minutes)

1. Go to https://zenodo.org and sign in. *Log in with GitHub* or ORCID both work.
2. Click **New upload** (top right; on some layouts it is under **Upload**).
3. In **Basic information**, at "Do you already have a DOI for this upload?", choose **No**. Then click
   **Get a DOI now!**. Zenodo shows a DOI of the form `10.5281/zenodo.NNNNNNN`.
4. Fill in the form. It is only saved as a draft, so nothing is public yet:
   - **Resource type:** Software.
   - **Title:** `Program Fault or Test Fault? Evaluating LLM Triage of Generated Unit Tests Against Buggy/Fixed Ground Truth (code and data)`.
   - **Creators:** Ahmed, Hafiz Huzaifa and Ilyas, Saad. Affiliation: FAST - National University of Computer and
     Emerging Sciences, Islamabad.
   - **Description:** paste the paper's abstract.
   - **Licence:** MIT, matching `LICENSE`.
   - **Version:** `1.0.0`.
   - **Keywords:** failure triage, LLM-based test generation, test oracle, multi-agent debate, self-consistency,
     Defects4J.
5. Click **Save draft**. **Do not click Publish yet.**
6. Send me the DOI.

## Step 2 — YOU: create the empty GitHub repository (about 2 minutes)

1. Go to https://github.com/new while signed in to the account that will own it.
2. Repository name: for example `llm-failure-triage`. Visibility: **Public**.
3. Leave **every** "Initialize this repository" box unticked: no README, no .gitignore, no licence. The repository
   must be empty.
4. Click **Create repository** and send me its URL (`https://github.com/<owner>/<name>`).

## Step 3 — me: fill in, rebuild, push

When I have the DOI and the URL, I:
1. Fill every URL and DOI placeholder:
   - in the paper (Data availability, Code availability);
   - in the Phase 3 report;
   - in `CITATION.cff` (`repository-code`, `doi`, `date-released`);
   - in the README.
2. Rebuild both PDFs and the deck, then run the numbers check and the tests.
3. Re-stage the release and re-run the secrets scan.
4. Push the folder to your repository with plain git:
   ```
   cd "C:\Users\huzai\Downloads\Fast\Advance AI\Phase 3 and 4\dist\release\github"
   git init -b main
   git add -A -f .
   git commit -m "Release v1.0.0"
   git remote add origin https://github.com/<owner>/<name>.git
   git push -u origin main
   ```
   The first push opens a **Git Credential Manager** window. **YOU** sign in to GitHub there. I never see or store the
   credential.
5. Tag the release (`git tag v1.0.0 && git push origin v1.0.0`).

## Step 4 — YOU: upload the zip and publish on Zenodo (about 5 minutes)

1. Open the draft from Step 1 (**Zenodo → My dashboard → Uploads**).
2. Under **Files**, upload the newest `dist\release\zenodo_<commit>.zip`. It is about 100 MB.
3. Under **Related works**, add the GitHub URL with relation "Is supplemented by" and resource type Software.
4. Click **Publish**. The DOI starts resolving within a few minutes. After this the record cannot be deleted, only
   versioned.

## v1.1, after the label audit is scored

I re-stage with the audit material included (`python scripts/release/stage_release.py --with-audit --zenodo`) and push
to the same repository. On Zenodo, open the record and click **New version** (it gets its own DOI under the same
concept DOI), upload the new zip and publish.
