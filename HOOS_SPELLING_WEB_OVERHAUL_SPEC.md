# Hoo's Spelling — Web Application Overhaul Specification

**Status:** Implementation-ready requirements draft; hosted proof of concept NOT YET RUN  
**Date:** October 22, 2026  
**Repository:** https://github.com/hpatel2004/hoos_spelling_automation  
**Baseline reviewed:** Public `release` branch, especially `README.md`, `REPOSITORY_REVIEW.md`, `app.py`, `sbsolver_parser.py`, `sbsolver_import.py`, and `oed_parser.py`. This document specifies proposed work; it is not evidence that production hosting or cloud scraping has succeeded.

## Confirmed editorial decisions — October 22, 2026

These decisions supersede conflicting proposed requirements below.

- **Acquisition UI (latest decision):** Saved SB Solver HTML import is the primary and only candidate-input path in the main editor UI. Show its uploader directly, outside any expander. Remove automatic-fetch and candidate-list paste controls; retain the normal-browser puzzle link, clear saving instructions, and a read-only imported-word preview. This supersedes earlier fetch-first and candidate-edit/paste requirements below. Editorial included/excluded list inputs remain supported.
- **Budget:** Prefer free hosting or very low cost. No paid hosting commitment or platform has been selected; measure feasibility and cost in Milestone 0.
- **Access:** Public site, no user accounts. Low expected distribution does not remove the need for bounded resource use and per-draft isolation. Draft recovery mechanism remains to be chosen.
- **Overrides:** Existing included/excluded lists may explicitly resolve technical OED lookup failures for candidate words; exclusion wins. Preserve the underlying unresolved lookup status separately from the final editorial decision and attribute resolution to the list. Do not require a separate per-word manual verification when an existing list supplies the resolution.
- **Access gate:** If hosted OED access is unavailable, pause implementation until supported access is available. A manual-only OED workflow is not an approved substitute. Individual failures during otherwise viable access may still be resolved through editorial lists.
- **Levels:** Wa, Wahoo, Wahoowa, and Average are chosen manually. Do not calculate them or silently clamp them using the current formulas. WahooWOW may default to the final accepted-word count. Manual level edits belong to the reviewed snapshot and invalidate prior exports.
- **Reference puzzles:** See `reference_puzzles/editorial_examples.json`. REGICD has 33 accepted words (the blank item 34 was an error), EGER is editorially excluded, and its historical no-results/missing-frequency rejections were manually verified. ANOYIG has 35 accepted words, with NONAGON and ONIONY editorially included. Both examples have manually chosen levels. Building an editorial word database is deferred; retain pasted/uploaded lists.
- **Launch reliability:** Durable progress and per-editor isolation are required for launch, regardless of their P1 checklist labels.

## 1. Product objective (non-negotiable)

Turn the current locally installed Hoo's Spelling automation into **a hosted website that an editor can open by URL and use immediately**. Visitors must not need to clone the repository, install Python, Chrome drivers, a browser extension, or run terminal commands. Scraping and classification run on the hosted application's infrastructure, not on the visitor's laptop.

The end product must **retain the existing formatted editorial output and functioning hyperlinks**. A user should be able to:

1. Open the site in a normal desktop browser.
2. Enter the puzzle letters, selected center, variable SB Solver placeholder, and optional creator/editorial metadata.
3. Fetch candidate words from SB Solver **when hosted access succeeds**, or import its words through a simple in-browser fallback when access is challenged.
4. Classify candidates according to the **existing OED first-result rules**, without requiring the editor to log in to OED for the level of public search-result information currently used.
5. Review and adjust editorial selections.
6. **Copy a fully formatted result into Google Docs/Word with clickable OED links**, or download `.html` and `.docx` documents containing working hyperlinks.

**Visualizing the controlled browser is NOT a requirement.** A simple status such as `Queued`, `Running`, `Needs input`, `Needs review`, `Complete`, or `Failed` is sufficient. A running percentage or current word is optional. Reliability and accurate output matter more than animation.

**Definition of success:** Multiple editors can use a single shared URL, complete the workflow without local setup, and produce the same editorially correct, richly formatted, hyperlinked document as the current tool.

## 2. Scope and implementation constraints

### Must retain

- Streamlit/Python is acceptable, and preferred for the first release to minimize rewriting.
- **SB Solver remains the source of candidate words.** Do not silently swap to another word generator or dictionary.
- **OED remains the classification source.** Do not substitute a generic dictionary API.
- Inspect **only the first OED search result** for a candidate, keeping the present ordering behavior.
- Preserve the **minimum of three OED usage bars** and the existing rejection logic for hyphenated/accented forms, variants, proper nouns, slang, low frequency, and genuinely absent frequency data.
- Preserve the **six actual puzzle letters + one variable seventh placeholder** needed by SB Solver. The actual center letter is explicitly selected (currently indicated in uppercase). Do **not** automatically remove words containing the placeholder; that was explicitly ruled out in the earlier review.
- Preserve editorial included/excluded lists (pasted or uploaded UTF-8 `.txt` files). Overrides affect only candidate words; exclusion wins on conflicts.
- Preserve puzzle levels (`Wa`, `Wahoo`, `Wahoowa`, `WahooWOW`, `Average`): manual editor inputs except WahooWOW, which may default to accepted count.
- Preserve the present output structure, headings, reasons, source links, and the special **“Editorially Removed Words — FLAG FOR COPY”** treatment.

### Not required in the initial release

- A React/Next.js rewrite, mobile-native application, browser extension, or separately deployed REST API.
- Watching a browser window live, per-word streaming logs, or an elaborate dashboard.
- An OED account/login flow for the currently used public search results. **Assumption to validate:** The same first-result metadata and usage bars are accessible from the production host without login.
- A general-purpose word database, bulk OED definition storage, or an alternative source when OED fails.
- User accounts or a complex authentication system. The site must remain easy to open; lightweight abuse prevention or staff-only access may be added if operationally needed.

### Critical external dependency

A no-login OED experience in a normal browser does **not** prove that automated requests from a hosting provider will work. Similarly, SB Solver may present Cloudflare verification. The overhaul must test live access from the chosen host early and never disguise a blocked lookup as an editorial rejection. This project does **not** attempt to bypass anti-bot protections. Use permitted access methods and retain browser-only manual import if automatic SB Solver access is not supported.

## 3. Required editor workflow

### Step A — Create puzzle

- Enter six actual, distinct letters and explicitly select the center letter; enter a **distinct seventh SB Solver placeholder** separately or through the existing seven-character format.
- Display the selected center and actual six-letter set clearly; show the exact seven-letter SB Solver query and its clickable URL.
- Validate letters before any fetch and explain errors next to the input.
- Enter creator, supply manual editorial levels before finalization, and add optional included/excluded editorial word lists.
- Retain current title/filename convention unless a format change is explicitly approved.

### Step B — Acquire candidates

- Primary action: **Fetch from SB Solver** through a server-side provider adapter when it works from the host.
- Confirm fetched content belongs to the requested puzzle, is the expected word table, and is not an access challenge, unrelated page, or partial result.
- Show imported word count, allow users to inspect/edit the canonical list, and deduplicate without silently enforcing new editorial criteria.
- Fallback: **Open this puzzle in SB Solver** in the editor's regular browser and then either:
  - Upload an HTML page saved after the word table loads (reuse `sbsolver_import.py`); or
  - Paste one candidate word per line.
- The fallback works entirely through the website: no server-side visible browser, local code, extension, or driver is required.
- On a blocked automatic fetch, give explicit guidance and preserve the user's inputs; do not repeatedly retry Cloudflare challenges or pretend the fetch succeeded.

### Step C — OED classification

- Launch hosted classification as a background job so the UI can refresh or disconnect safely; at a minimum, completed decisions must not vanish when the browser tab reloads.
- For each candidate, preserve the existing form-screening and first-OED-result evaluation. Base classification on **search-result metadata**, including usage bars; full dictionary entry text is not a requirement.
- Use explicit result statuses rather than collapsing technical failures into `Removed Words`:
  - `ACCEPTED` — passed existing OED checks.
  - `REJECTED` — genuine editorial-rule rejection with reason.
  - `UNRESOLVED` — blocked/challenged, timed out, network error, missing required selector because of parser failure, or otherwise indeterminate.
  - `CONFIRMED_NOT_FOUND` — a confidently identified normal OED no-results state; apply the documented editorial treatment without conflating it with a timeout.
- Distinguish a genuine OED record with no frequency data (the existing rule rejects it) from a page on which the frequency field failed to load or could not be parsed (unresolved).
- Preserve the OED query URL for every word and, when permissible, the first-result evidence needed to explain decisions.
- Do not scan subsequent results or relax the three-bar threshold.
- Apply editorial includes/excludes **after** OED classification, with clear attribution to the editor's override.
- Allow user-initiated retries of unresolved items. Do not auto-classify an error as a rare word.
- If unresolved items remain, prominently mark the output as **draft/incomplete** and prevent an unqualified *final* export; support an explicit editorial resolution path rather than silently dropping words.

### Step D — Review and output

- Display accepted words, removed words with reasons, editorially removed words, and unresolved words in a readable review interface.
- Default WahooWOW to the final accepted count after editorial overrides; retain manually chosen Wa, Wahoo, Wahoowa, and Average. Preserve the **user-selected** center letter rather than inferring it from surviving words.
- Present a **rendered, copyable formatted document**, not just raw text or raw HTML source.
- Provide: **Copy formatted output**, **Download HTML**, and **Download Word (.docx)**.
- The resulting document must preserve clickable OED links attached to word text and a clickable SB Solver puzzle link. For the final Word file, the metadata's SB Solver link must be a real DOCX hyperlink, not merely a printed URL.
- Maintain numbered word lists, metadata table, blue/underlined editorial-removal label, yellow `FLAG FOR COPY` highlight, and level values.
- No hidden local files, Word installation, or third-party conversion sites are required to obtain the downloadable files.

## 4. Rich formatting and hyperlink acceptance contract (highest priority)

The export format is **part of the product**, not an optional enhancement. Preserve the existing `build_output_html`, `render_copyable_output`, and DOCX hyperlink behavior while refactoring.

The generated result must contain, in this order:

1. Puzzle title.
2. Metadata table: `Creator`, `Center Letter`, `Link` (clickable SB Solver puzzle link).
3. **Words** — numbered list of accepted candidates, each clickable to that word's OED search URL.
4. **Removed Words** — numbered list with the clickable word and the existing rejection reason.
5. **Editorially Removed Words** — existing blue-underlined/flagged heading with **yellow `FLAG FOR COPY`** styling and clickable entries.
6. **Levels** — `Wa`, `Wahoo`, `Wahoowa`, `WahooWOW`, and `Average`.

Implementation details:

- Generate output from **one reviewed, immutable puzzle/result snapshot**, shared by preview, copy, HTML, and DOCX; exports must not combine old classifications with new metadata.
- Preserve real HTML `<a href="...">` anchors. URL-encode search terms and HTML-escape user text; never use a Markdown link as the actual HTML export.
- Rich clipboard should write **both `text/html` and `text/plain`** on a user-initiated click, using the browser's Clipboard API on the HTTPS site. Provide a selectable rendered-content fallback if rich clipboard support is unavailable.
- Verify pasting into **Google Docs and Microsoft Word**: typography, numbered lists, and links must survive. No assumption that pasting raw HTML code will be rendered by the target editor.
- Build `.docx` in memory (`io.BytesIO`) rather than writing shared per-puzzle filenames to the server. Use external hyperlink relationships for the word links **and** the SB Solver link in document metadata.
- `.html` download should open by itself in a browser with correct encoding, formatting, lists, and anchors. It must not depend on Streamlit's iframe or a live server.
- Changes to puzzle letters, center, words, creator, overrides, or levels must update the reviewed snapshot or invalidate old exports.

### Output acceptance tests

- [ ] Open the hosted site, finish one puzzle, click **Copy formatted output**, paste into Google Docs: metadata table/list numbering remain readable and clicking a word opens its OED URL.
- [ ] Repeat the paste test in Microsoft Word (web or desktop) and confirm hyperlinks remain clickable.
- [ ] Download HTML: open locally, inspect each section, follow one OED link and the SB Solver link.
- [ ] Download DOCX: open in Word, confirm actual external hyperlinks on every word **and on the SB Solver metadata link**; the correct center letter and levels appear.
- [ ] Accepted, rejected, and editorially removed lists retain their headings, reasons, order, and link destinations.
- [ ] Two simultaneous users can export the same puzzle title without replacing or exposing each other's document.
- [ ] A failed OED lookup never appears as an authoritative editorial rejection.

## 5. Recommended MVP architecture

**Keep the Python/Streamlit frontend and deploy it as a Dockerized web service on a persistent Linux host** (for example Railway, Render, or an equivalent university-managed service). Pick the host only after a live-source access pilot.

```text
Editors' browsers (only need HTTPS URL)
         |
         v
Hosted Streamlit UI (puzzle entry, uploads, review, rich copy/download)
         |
         +----> Drafts / immutable results / job states (persistent storage)
         |
         v
Background job queue / single controlled worker initially
         |
         +----> SB Solver provider adapter -> fetched words OR blocked status
         |
         +----> OED provider adapter -> first result / usage bars / evidence status
         |
         v
Pure Python classification + editorial override + levels
         |
         v
One canonical result model -> HTML / rich clipboard / DOCX bytes
```

Design decisions:

- **Web UI:** Existing Streamlit app, reorganized into Create / Import / Review / Export. A separate frontend/API is unnecessary for MVP.
- **Scrapers:** Server-side, headless-capable Chromium/Selenium *if permitted and reliable on the host*. The macOS-specific `open -na Google Chrome`, fixed debug port, and shared browser profile must not appear in the deployed path.
- **Worker:** Background execution independent of a Streamlit button's single request; one active browser job at a time is acceptable for MVP. Enqueue rather than launch competing browser sessions.
- **State:** Store puzzle draft, candidate list, job state, per-word decision/evidence, and reviewed result snapshot. A persistent SQLite database can support a **single persistent instance with an attached volume**; if deploying multiple replicas or ephemeral containers, use managed shared storage (e.g., PostgreSQL). Do not use Streamlit session state as the only durable storage.
- **Storage:** Prefer temporary/in-memory export bytes; no shared filenames, no unbounded file buildup. Keep source caching only when permitted and for an appropriate lifetime.
- **Service reliability:** Healthcheck, bounded retries, timeout handling, provider-specific error codes, structured logs with job IDs, and graceful restart/resume for incomplete jobs.
- **Security:** HTTPS, server-only browser ports, validation and size limits on uploads, HTML escaping, safe hyperlinks, per-job isolation, resource limits, and rate limiting to protect a publicly reachable service. If staff-only use is desired, a simple access gate may be added without requiring users to install anything.

**Important:** A hosted site still cannot guarantee automated SB Solver access; Cloudflare does not support Selenium for completing production challenges. The HTML-upload/paste path remains a first-class supported fallback, not a temporary error dialog. Do not add CAPTCHA bypass or anti-detection tactics. OED being readable without login does not, by itself, establish permission for automated, repeated retrieval. Check terms, rate limits, and any applicable institution/owner guidance before enabling production access.

**Hosting distinction:** Streamlit Community Cloud can deploy a Streamlit application from GitHub, but it is not a user-managed Docker host. The default production recommendation for this browser-automation workload is a Linux **Docker-capable platform** (e.g. Railway or Render), with a persistent state store and a bounded browser worker. Community Cloud is an optional limited-resource experiment, *not* the assumed long-running job infrastructure. Test quotas, app sleep/idle behavior, cold starts, storage persistence, and any cost limits before committing.

## 6. Proposed component boundaries and repository migration

| Current code | Target responsibility | Required action |
|---|---|---|
| `app.py` | Hosted Streamlit pages and user interactions | Thin UI; remove local-Chrome assumptions, prevent stale inputs/exports, display jobs/results and copy buttons |
| `sbsolver_parser.py` | `SBSSolverProvider.fetch(query) -> AcquisitionResult` | Replace Mac debug Chrome launch; isolate sessions; check page identity; distinguish complete/blocked/empty/parser error |
| `sbsolver_import.py` | `import_saved_sbsolver_html(bytes) -> words` | Reuse existing saved-HTML parser as fallback; validate upload safely |
| `oed_parser.py` | OED adapter + pure rule evaluator + level logic | Split network/browser I/O from first-result parsing and editorial rules; separate genuine rejections from unavailable evidence |
| `oed_parser.py` export functions | `export_html(snapshot)`, `export_docx_bytes(snapshot)` | Preserve exact editorial layout and links; DOCX in memory, correct selected center |
| `REPOSITORY_REVIEW.md` | Reference for prior decisions and regressions | Keep historical notes; implement prioritized unresolved findings |
| `tests/` | Offline fixtures and regression tests | Keep old tests; add output/link/copy/server/job/integration tests |
| New `storage.py` / `jobs.py` | Persistent state and background processing | Add only enough complexity for disconnect-safe jobs and isolation |
| New `Dockerfile`, `.dockerignore`, optional deployment config | Reproducible Linux server | Install compatible browser + driver, pin dependencies, expose Streamlit service |

An illustrative target layout (names are flexible):

```text
hoos_spelling_automation/
  app.py
  core/
    models.py
    puzzle_rules.py
    editorial_filters.py
    levels.py
    exports.py
  providers/
    sbsolver.py
    oed.py
  services/
    jobs.py
    storage.py
  imports/
    saved_sbsolver.py
  tests/
    fixtures/
    test_puzzle_rules.py
    test_provider_parsing.py
    test_failed_lookups.py
    test_exports_and_hyperlinks.py
    test_jobs_and_isolation.py
  Dockerfile
  .dockerignore
  requirements.txt
  README.md
  WEB_OVERHAUL_SPEC.md
```

## 7. Data contract and state handling

Use typed internal models rather than passing HTML-anchor strings around as application data. Example conceptual shapes (not final framework-specific schemas):

```python
PuzzleDraft = {
    "id": "uuid",
    "actual_letters": "ABCDEF",       # six actual letters, canonical order
    "center_letter": "A",          # explicit, not inferred
    "placeholder": "g",            # variable 7th letter, not an actual letter
    "sbsolver_query": "Abcdefg",   # case convention preserved
    "creator": "...",
    "candidate_words": ["..."],
    "editorial_include": ["..."],
    "editorial_exclude": ["..."],
    "wahoowa_override": None,
    "revision": 1,
}
WordDecision = {
    "word": "EXAMPLE",
    "oed_url": "https://...",
    "lookup_status": "FOUND | CONFIRMED_NOT_FOUND | BLOCKED | TIMEOUT | PARSE_ERROR",
    "first_result_headword": "... | None",
    "usage_bars": None,            # integer when conclusively observed
    "rule_result": "ACCEPTED | REJECTED | UNRESOLVED",
    "reason": "...",
    "editorial_override": "INCLUDE | EXCLUDE | NONE",
    "final_result": "ACCEPTED | REJECTED | UNRESOLVED",
}
ResultSnapshot = {
    "draft_id": "uuid",
    "source_revision": 1,
    "review_status": "DRAFT | FINAL",
    "decisions": ["..."],
    "levels": {"wa": 0, "wahoo": 0, "wahoowa": 0, "wahoo_wow": 0, "average": 0},
}
```

Requirements:

- A puzzle draft has **one authoritative list of candidate words**. Editing it in any interface updates the same source of truth.
- A job records the draft revision used at launch and never overwrites newer editor changes.
- Editing any dependent field marks previous results stale; final copy/download is disabled until reviewed against the current revision.
- Save each finished lookup so a crash or reconnect does not force all already completed words through OED again, subject to source-data retention permissions.
- Keep the source URL separate from rendered `<a>` markup; render and escape links only at export time.
- Give each user/job separate IDs and data; two editors must not share a Chrome profile or overwrite a download.

## 8. Deployment requirements

- [ ] Docker image builds on Linux with pinned/supported Python, Python packages, Chromium, and compatible driver.
- [ ] Streamlit is served on the host-provided port, bound to `0.0.0.0`, with HTTPS supplied by the hosting platform.
- [ ] No macOS `open`, desktop window, or visitor-local `127.0.0.1` dependency is used in production.
- [ ] One public HTTPS site URL is usable from macOS and Windows without installs.
- [ ] Restart/redeploy does not erase completed jobs or corrupt user drafts; if using a single instance, attach a persistent volume.
- [ ] Headless SB Solver/OED accessibility, selector behavior, and license/site-terms constraints are validated from the **actual deployment host** with a representative puzzle.
- [ ] Server browser sessions have concurrency limits and are cleaned up after success/failure.
- [ ] Unexpected source changes show actionable error messages, not blank pages or silently empty lists.
- [ ] App provides a compact user-facing README: URL, puzzle steps, fallback, output instructions. Developer-only setup moves to separate contributor docs.
- [ ] Secrets, if any, live in hosting environment configuration rather than Git or exported documents.

## 9. Testing plan

### Unit tests (must be offline and deterministic)

- Input validation: six actual letters, selected center, variable placeholder, seven distinct query letters; do not strip placeholder words automatically.
- SB Solver HTML parser: expected table, duplicate elimination, wrong/empty/partial pages, invalid encodings.
- OED parser with fixture HTML: first result only, frequency bars 2 vs 3, variant/proper noun/slang/hyphen/accent, true missing-frequency record vs parser failure.
- Editorial final filters: include and exclude rules; exclusion precedence; no injection of noncandidate words.
- Manual levels retained exactly; WahooWOW defaults to final accepted count; selected center retained even after many rejected words.
- Output: valid anchors, escaped text, correct section order, highlighted editorial flag, hyperlink XML in DOCX, consistent metadata across outputs.
- State: revise an input after classification => old export blocked; two concurrent drafts and identically named files stay independent.
- Job failure: blocked source, timeout, restart and retry retain completed, valid decisions.

### Hosted smoke tests (run on the chosen actual service)

1. Open site on a second device with **no Python installed** and finish a sample run.
2. Confirm SB Solver automatic fetch behavior from the server; separately test the HTML import fallback after an access challenge.
3. Confirm **public OED first-result metadata** and three-bar read from the hosting provider without OED login; compare several known words and staff classifications.
4. Start a long classification, refresh/close/reopen the tab, then recover the result.
5. Run two editors concurrently and confirm no browser/session/job leakage.
6. Copy results to Google Docs and Word; download and manually inspect both HTML and DOCX links.
7. Stop/restart a worker during a job, then confirm a recoverable incomplete state.
8. Verify mobile browser readability as a bonus; desktop editing is the primary target.

## 10. Implementation sequence (ordered; do not skip source pilot)

**Milestone 0 — Hosting feasibility spike (go/no-go before rewriting everything)**

**Purpose:** Answer whether a no-install website can actually collect the required SB Solver list and public OED first-result/usage-bar information **from the cloud host**, before spending time on a major refactor. This is a test plan, not a claim that the sources have been tested successfully.

1. Provision a minimal Linux **Docker-capable host** with Python, pinned Chromium/driver, Streamlit (or a one-route test interface), server logs, and a strict browser-session limit. Railway or Render are candidate hosts; choose based on actual test results, reliability, and cost rather than branding.
2. **SB Solver test:** For at least two known six-letter puzzles (each with the correct seventh variable placeholder), request the exact SB Solver URL. Confirm the response is the right puzzle, contains the complete expected word list, and is not a challenge, a stale session, or an unrelated table. Record word counts and a small sample to compare with a normal editor browser. Separately simulate a blocked/403/challenge state and confirm it is identified as `BLOCKED`, not as an empty puzzle.
3. **OED test:** Check at least 8–10 representative words selected with the Puzzle Desk: accepted usage >=3, rejected usage <=2, variant/proper-name/slang cases, a genuine no-result case if obtainable, and an ambiguous/missing-metadata case. Compare the *first* search result, headword, label and frequency indicator with the editor's ordinary unauthenticated browser. A successfully loaded page must not be mistaken for sufficient evidence if the frequency indicator is absent or delayed.
4. Run the two provider tests more than once, at different times if practical, using modest request rates compliant with provider terms. Observe loading, timeouts, rate limits, IP blocks, browser crashes, latency, and memory use. **Do not automate solving Cloudflare or other interactive security checks.**
5. Prove the fallback on the *hosted UI*: editor opens the source in their normal browser, imports saved SB Solver HTML or pastes candidate words, and can proceed without local Python or drivers.
6. Run a small end-to-end export smoke test: valid candidate decisions -> preview -> copy to Google Docs and Word -> HTML/DOCX downloads, verifying live **OED word hyperlinks** and the **SB Solver metadata hyperlink**. If OED automation fails, test the editor-review alternative only as an explicitly incomplete/manual workflow.
7. Record outcomes in `HOSTING_PILOT_RESULTS.md`: date, provider/plan/region, app/image versions, approximate request volume and duration, source URL/puzzle ID, pass/fail and observed reason, expected-versus-observed count/usage, evidence screenshots or sanitized logs, fallback performance, source-terms review, and rough monthly hosting estimate. Do not store challenge tokens or personal browser cookies.

**Go/no-go rules:**

- **Both sources pass reproducibly:** proceed with the planned hosted automatic workflow.
- **SB Solver automatic fetch fails but OED passes:** ship the website only if staff accept **SB Solver browser HTML/paste import** as the supported acquisition route; automatic SB Solver claims must be removed from launch messaging.
- **OED hosted automation fails:** do **not** advertise fully automatic classification. Pause implementation until supported access preserving existing OED first-result behavior is available. A manual-only classification workflow is not an approved replacement.
- **Frequent blocks, rule mismatch, or unstable extraction:** stop the automation portion of the overhaul and resolve the access/accuracy question first; do not bypass protections or silently change dictionaries, threshold, or editorial rules.

**Deliverable:** A small, reproducible hosted proof of concept and its decision record. **No hosted-access promises until this milestone passes.**

**Milestone 1 — Preserve correctness and exports**

- Extract pure models, classification rules, levels, and HTML/DOCX builders from browser concerns.
- Freeze existing successful-output behavior as regression fixtures.
- Fix selected-center handling, Word metadata hyperlink, shared filesystem exports, and export invalidation.
- Make HTML/Word links a tested acceptance requirement.

**Milestone 2 — Hosted acquisition and robust decisions**

- Refactor SB Solver and OED into server-compatible adapters.
- Remove Mac Chrome launcher from production; implement headless operation if source permits it.
- Add explicit blocked/unresolved states; keep HTML/paste import fully functional.
- Keep first OED result and all established editorial decisions unchanged.

**Milestone 3 — Editor-facing website and durable jobs**

- Simplify to Create -> Import -> Classify/Review -> Copy/Download.
- Add single-worker queue, persistent drafts, statuses, retry of unresolved items, and per-editor isolation.
- No live browser view or per-word animation required.

**Milestone 4 — Deploy and hand off**

- Add Docker deployment, logs/healthcheck, hosted smoke tests, and straightforward editor instructions.
- Test rich clipboard and both downloadable formats in browsers used by the Puzzle Desk.
- Remove obsolete local extension/setup paths only after the website is working.

## 11. Prioritized delivery checklist

| Priority | Deliverable | Acceptance criterion |
|---|---|---|
| **P0** | Site opens by URL with zero local setup | An editor on another laptop needs only a browser |
| **P0** | Hosted OED access feasibility verified | First-result metadata/usage bars match normal-browser review |
| **P0** | SB Solver candidate acquisition + browser-only fallback | Successful fetch or saved-HTML/paste import; never invent results |
| **P0** | Original editorial behavior preserved | Tests match first-result rules, usage >= 3, override precedence |
| **P0** | Correct formatted output with real hyperlinks | Copy to Docs/Word; HTML and DOCX links work |
| **P0** | Incomplete/error states are safe | Blocked/timeout != rejected; reviewer sees unresolved items |
| **P0** | Browser-independent server deployment | No Mac Chrome launcher, extension, localhost bridge, or displayed browser needed |
| **P1** | Durable jobs and results | Refresh/reconnect preserves progress; concurrent editors isolated |
| **P1** | Review and retry | Unresolved items can be retried without rerunning successful lookups |
| **P1** | Automated deployment and regression suite | Linux Docker deployment + CI/offline fixtures |
| **P2** | Saved drafts/collaboration/history | Useful after the first viable hosted workflow works |
| **P2** | Advanced job progress, analytics, prettier UI | Not a prerequisite for shipping |

## 12. Explicit out-of-scope / engineering guardrails

Do **not** spend the first iteration rebuilding the UI framework, generating substitute word lists, trying to automate challenge-solving, adding accounts and roles, ingesting whole OED definitions, or polishing real-time animations. Do **not** trade away the finished formatted/hyperlinked document to simplify development.

Where production access is not available, display the limitation and use the agreed editor-supplied fallback. The site itself should always remain accessible and useful even when a particular upstream service fails.

## 13. FUTURE ISSUES — anticipated risks and planned mitigations

These are **anticipated issues**, not a list of bugs proven in the hosted version. `P0` means a release/accuracy/access blocker; `P1` means important reliability or operational work for a shared service; `P2` means a later usability or maintenance enhancement. Source access and output integrity come before interface polish. Track whether each risk is `Open`, `Mitigated`, or `Verified` in the development issue tracker; **do not call a risk resolved solely because the app deploys**.

### A. P0 — Address before declaring the website production-ready

| Anticipated issue | Why it matters | Required mitigation / verification |
|---|---|---|
| **Cloudflare, 403s, bot screening, or hosting-IP restrictions** | The hosted browser may be shown a challenge or refused even when an editor's browser succeeds. A headless page can also return a challenge instead of data. | Detect challenges/403/429, distinguish from empty results, cap retries, show an actionable error, and use staff-supplied SB Solver HTML/paste import. No challenge solving, stealth-browser tactics, proxy rotation, or access-control evasion. Validate on the actual production host. |
| **Public OED page ≠ permitted/reliable automated data source** | Unauthenticated human viewing does not establish a right or technical ability to run repeated cloud lookups. Host egress may be rate-limited or source policy may prohibit the planned access. | Verify applicable site terms/permissions and representative cloud queries in Milestone 0. Stop rather than bypass restrictions. If automation is unavailable, require supported access or explicit editor-verified OED decisions with links; never claim the batch was automatically checked. |
| **Incomplete OED page silently rejects words** | `oed_parser.py` can conflate timeout, missing selector, and a genuine rare/absent entry; this directly changes published copy. | Separate `BLOCKED`, `RATE_LIMITED`, `TIMEOUT`, `PARSE_ERROR`, `CONFIRMED_NOT_FOUND`, and valid `FOUND`. Treat technical errors as `UNRESOLVED`; make final export conditional on explicit resolution. Fixture-test frequency 2 vs 3 and truly missing frequency. |
| **Source layout / client-side loading / first-result ordering changes** | A changed CSS selector or delayed search results may silently read the wrong OED entry, label, or usage indicator. SB Solver may likewise change its word-table HTML. | Keep selectors isolated in provider adapters, wait for required fields, compare against fixtures and periodic manual samples, and surface parser failures without manufacturing candidates or decisions. Preserve the **first-result-only** editorial policy. |
| **Wrong puzzle, stale verification session, or malformed pasted list** | A previous SB Solver browser session, uploaded HTML, or stale Streamlit widget could attach the wrong words to the current letters. | Bind fetch/import to puzzle ID, exact six actual letters, explicit center, and seventh placeholder. Validate page identity where possible; show list/count/preview for manual confirmation. Deduplicate; do **not** silently reject placeholder-containing words or change editorial rules. |
| **Formatting or links lost on clipboard/DOCX exports** | The final deliverable is a copy-ready editorial document. Text-only paste, relative URLs, iframe restrictions, or incorrect DOCX relationships would defeat the redesign. | Test **real rich HTML clipboard** (`text/html` + `text/plain`) from an HTTPS user click; provide rendered selection and HTML/DOCX alternatives. Confirm OED links on each word and the SB Solver metadata link in Google Docs and Word. Make export regression tests release-blocking. |
| **Cross-user data leaks or overwritten downloads** | A single server may serve multiple editors. The repository currently has shared browser-state/file risks. | Per-job IDs, strict ownership/unguessable result links, isolated browser contexts, no shared debug port/profile, in-memory unique exports, validated file names, and concurrency tests with two editors using the same puzzle title. |
| **Untrusted uploads or generated HTML** | Saved SB Solver HTML, free-text metadata, and rich preview markup could expose the hosted app to oversized inputs or script/link injection. | Impose upload byte limits, parse saved HTML as **data only** (never execute user scripts), sanitize/escape user values, validate HTTP(S) link destinations against intended source domains, and do not allow arbitrary URL fetches or local file paths. Test hostile sample HTML/metadata. |
| **No viable production-host pathway** | A Streamlit page can deploy while the actual Chromium scraper cannot start, or host memory/cost limits prevent it from working. | Linux Docker build and real hosted provider smoke tests are gating. Community Cloud is optional for light experiments, not a substitute for verifying Chromium, persistent jobs, and limits. If full automation cannot be supported, document the scope of the manual workflow before release. |

### B. P1 — Engineer for reliable day-to-day desk use

| Anticipated issue | Why it matters | Required mitigation / verification |
|---|---|---|
| **Long-running OED batches** | The repository review estimates that for 100 words, its 4–7-second per-word sleeps alone take roughly 7–12 minutes, before network delays. Streamlit reruns, browser closes, or server restarts could lose an entire batch. | Background queue, persistent per-word decisions/job status, resume/cancel, sensible request pacing within provider rules, circuit breaker after systemic failures, no automatic hammering of blocked providers. Test close-tab/reopen and worker restart. |
| **Chromium/driver incompatibility or crashes** | Headless Chrome may fail on Linux due to dependencies, sandbox, executable paths, architecture, memory, or browser/driver version drift. | Pin/test an appropriate browser image and Python dependencies, use container health checks, isolate jobs, bound Chrome processes, close them in `finally`, and test image rebuilds in CI. Avoid OS-specific desktop launch commands. |
| **Exhausted CPU/RAM/disk and rising hosting cost** | Each headless Chrome instance consumes resources; overlapping editors and retries can exhaust a small/free host. Free services may sleep, throttle, or reset local state. | One browser worker initially, queue limits, bounded concurrency, per-job max runtime, usage metrics, cost alerts/budgets, and persistent external state where needed. Reevaluate host tier based on measured pilot timings, not guessed throughput. |
| **Ephemeral storage, redeploys, app sleep, and state loss** | A deployment may restart or discard local files; `st.session_state` alone does not preserve a desk's work. | Persist puzzle drafts, source revision, completed classifications, overrides and results; use SQLite only on a supported single instance with persistent disk, otherwise PostgreSQL/shared store. Test redeploy/restart and recovery. Never store source pages beyond permitted retention. |
| **Duplicate jobs, stale results, and race conditions** | Repeated clicks or changing the letters during classification could merge old results with new metadata. | Idempotent job creation for a given draft revision, one canonical candidate list, revision-tagged immutable results, clear `stale` state, cancel/recompute controls, and export invalidation after edits. |
| **Rate limits / caching versus editorial freshness** | Rapid repeated OED lookups can trigger throttling; cached results might be out of date or impermissible to retain. | Use conservative request budgets, clear backoff on transient 429s only when appropriate, optional per-word cache with explicitly permitted retention/TTL, rule/selector version stamps, and manual refresh. Do not save dictionary content wholesale. |
| **Unauthenticated public use and accidental abuse** | A publicly reachable URL lets strangers trigger expensive browser work and may cause provider blocks or runaway bills. | Decide public versus editorial-only access before launch. If access-limited, use a simple staff sign-in/access gate; either way use request limits, job quotas, upload limits, and safe error/log handling. Avoid exposing cookies, credentials, or staff data. |
| **Maintenance ownership and observability** | If a source changes during a Puzzle Desk deadline, no one may know whether results are incomplete or why. | Structured provider errors, small admin diagnostics, health and failure alerts, a documented manual fallback, pinned deploy branch, owner/on-call contact, rollback procedure, and a monthly sample audit of accepted/rejected decisions. |

### C. P2 — Improvements after the hosted workflow is dependable

- **Browser compatibility and accessible editing:** Test Safari/Chrome/Firefox and keyboard-based copy/review. Rich clipboard permissions differ by browser; keep alternate download paths.
- **Collaboration conflicts:** If two editors revise one puzzle concurrently, add optimistic locking/revision notices, named review status, and a change history. Keep MVP jobs isolated first.
- **Source downtime during publication windows:** Add a visible service status and a staff runbook, including where to find the manual SB Solver import and how to flag OED items requiring human confirmation.
- **Future rule/HTML format drift:** Version editorial rules and export templates with result snapshots; maintain gold-standard sample outputs and verify that new code does not silently change levels, threshold, special highlighting, links, or word ordering.
- **Repository/hosting handoff:** Keep a single documented production branch, `.dockerignore`/`.gitignore`, license/access notes, dependency updates, backup/restore instructions, and credentials owned by the editorial organization rather than one developer's laptop.

### Future-issue resolution gates (definition of 'done')

1. **Availability:** An editor with a fresh browser can open the shared URL and either fetch verified candidates or complete the explicit browser-only SB Solver fallback.
2. **Classification:** Every candidate has a verified rule decision **or** a conspicuous, editor-resolved OED exception; a challenged/missing page is never represented as a normal OED rejection.
3. **Persistence/isolation:** Two simultaneous editors, a refresh, and a server restart cannot cause cross-user leakage, lost completed work, or stale export.
4. **Publishing output:** The same reviewed result generates preview, rich copy, HTML, and DOCX with intact Word/Google Docs hyperlinks and the correct six-letter/center/placeholder metadata.
5. **Operations:** Host limits and costs have been measured, source access restrictions reviewed, and staff given a documented failure/recovery process.

## 14. Working references

- Existing repository: https://github.com/hpatel2004/hoos_spelling_automation/tree/release
- Existing architecture and identified defects: https://github.com/hpatel2004/hoos_spelling_automation/blob/release/REPOSITORY_REVIEW.md
- Existing workflow: https://github.com/hpatel2004/hoos_spelling_automation/blob/release/README.md
- Existing rich copy and download UI: https://github.com/hpatel2004/hoos_spelling_automation/blob/release/app.py
- Existing HTML/DOCX and OED rules: https://github.com/hpatel2004/hoos_spelling_automation/blob/release/oed_parser.py
- Existing saved-page import: https://github.com/hpatel2004/hoos_spelling_automation/blob/release/sbsolver_import.py
- Streamlit Docker deployment: https://docs.streamlit.io/deploy/tutorials/docker
- Streamlit Community Cloud resource limits, hibernation and operational differences: https://docs.streamlit.io/deploy/streamlit-community-cloud/manage-your-app
- Streamlit Community Cloud status and limitations: https://docs.streamlit.io/deploy/streamlit-community-cloud/status
- Cloudflare automated-browser restrictions: https://developers.cloudflare.com/cloudflare-challenges/reference/supported-browsers/

---

**Approval target:** A hosted Hoo's Spelling editor that users can just open, that preserves SB Solver + OED editorial decisions, and that reliably returns a **copyable or downloadable, fully formatted result with working hyperlinks**. All other architecture decisions serve that goal.
