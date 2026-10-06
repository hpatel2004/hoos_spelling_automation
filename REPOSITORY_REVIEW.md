# Hoos Spelling repository review

Reviewed October 5, 2026. The initial review covered the working tree, including existing uncommitted changes in `app.py`, `browser_import.py`, and `sbsolver_parser.py`. After clarification, optional editorial-list uploads and word-processing progress were added to `app.py`, a progress callback and guaranteed browser cleanup were added to `oed_parser.py`, and staff instructions were updated in `README.md`. Existing source integrations and OED classification rules were retained.

Updated after the user's clarification: Hoo's Spelling uses six actual puzzle letters. A seventh variable placeholder is supplied only to satisfy SB Solver's input format. The user explicitly requested no automatic placeholder removal. SB Solver's source list, OED as the dictionary, the first OED search result, and the existing stringent editorial criteria are requirements. Recommendations to substitute another word list/dictionary or evaluate multiple OED results have been withdrawn. The earlier one-word level example was an artificial diagnostic case, not a description of the puzzle, and has been removed from the recommendations.

The user subsequently chose to retain the current OED timeout handling. Recommendations below concerning separate failure outcomes remain optional future work; they are not part of this implementation. OED first-result selection, exclusions, frequency threshold, and timeout decisions are unchanged.

## Recommendation

The user prefers a shared website and accepts a locally run Streamlit app as a fallback. Preserve the required workflow: six actual letters and their center, plus a separate seventh placeholder for the SB Solver request; SB Solver's word list; and classification using only the first OED search result under the existing editorial criteria, including at least three usage bars. University OED browser access is available, but API credentials or an automation agreement have not been established.

Keep Streamlit and repair acquisition, state management, and parsing around those requirements. Document the six-letter puzzle and seven-letter SB Solver input accurately; preserve the current variable-placeholder handling. Give editors a separate queue for lookups interrupted by access or parsing failures, with saved progress and explicit retries. Preserve paste/upload of the SB Solver list as a fallback. Do not introduce a different candidate generator or dictionary.

For a shared website, confirm supported access to both required sources, including the same OED first-result ordering, usage bars, and labels. An OED API is relevant only if that exact behavior can be preserved; otherwise it is not an equivalent implementation. A shared website cannot use a visitor's local Chrome window through the repository's existing server-side Selenium code. A repaired local app with a dedicated persistent browser session for both providers is a practical interim option, with staff completing security checks when needed and the app preserving progress.

A shared site does not inherently require an API or routine viewing of Chrome. The preferred design runs Streamlit and a background browser worker on a persistent Linux server or university VM, while staff see a progress bar and current-word status. Chrome supports [headless operation without visible UI](https://developer.chrome.com/docs/automation-and-testing/headless); successful access to these specific protected sites must still be tested on the chosen host. A background browser with a virtual display is another implementation option if needed. Streamlit documents [Docker deployment on a server](https://docs.streamlit.io/deploy/tutorials/docker).

Viewing Chrome is needed only as a possible fallback when a site explicitly requires human verification. An authenticated viewer such as [noVNC](https://novnc.com/info.html) could expose that server browser on demand, but it is not a required normal step. A progress indicator cannot complete an interactive security check. The hosted worker should distinguish blocked access from editorial rejection and pause with an actionable status; whether an interactive fallback is actually necessary depends on the host-access pilot. Headless access and such pause/resume handling have not been implemented or tested in this repository yet.

The current working tree already removes the extension from the active app: `app.py` calls `fetch_words_sbsolver` directly and does not start the import server. Deleting the remaining extension files alone will not solve the failures.

## Confirmed findings, in priority order

### 1. Failed OED lookups become editorial rejections — high priority

Evidence: `oed_parser.py:220` (`classify_words`), `oed_parser.py:257`, `oed_parser.py:261`, `oed_parser.py:271`, `oed_parser.py:314`.

OED opens in a new Chrome session, separate from SB Solver's persistent profile and from a staff member's existing university login. There is no login implementation, and the parser reads search-result metadata rather than authenticated full definitions. The absence of a login prompt in successful past runs does not establish reliable automated access or API entitlement. The code waits six seconds for a result element. Any failure during that wait becomes `No results`; other lookup failures become `Error fetching`. Both enter `rare`, which is exported under Removed Words. Missing frequency data is also an automatic rejection, even when the issue could be an incomplete page or changed selector.

A mocked challenge-page timeout for RICE produced no accepted words and one removed word with reason `No results`. No explicit no-results page had been observed.

Change: return separate lookup outcomes such as found, confirmed-not-found, blocked, authentication-required, rate-limited, timeout, and parse-error. Apply the existing editorial rules only after the first result is fully loaded and its required fields have been read. A genuine confirmed absence of frequency data should retain the existing editorial treatment; an interrupted lookup or failed extraction is not evidence of that absence. Incomplete lookups belong in Needs review and should be retryable. Pause a batch when access fails systematically. Final export should require successful classification or an explicitly permitted editorial decision for unresolved words. Browser cleanup is now wrapped in `finally`; distinct lookup outcomes remain pending.

### 2. Word-list transfer repaired; metadata snapshot work remains

Evidence: `app.py:115`, `app.py:124`, `app.py:241`, `app.py:248`, `app.py:318`, `app.py:344`.

Two independently keyed text areas compete with `word_list_text`. Updating a widget's default `value` does not synchronize an already-created widget. Both tabs execute on a rerun, so Step 2 can overwrite the canonical list using its old value. Editing words, metadata, or editorial filters does not invalidate classification results. Export uses current puzzle metadata alongside earlier classification data.

This describes the original defect. The SB Solver challenge-loop follow-up repaired two-way word-list synchronization and clears classification results when words or valid puzzle letters change. New puzzle letters clear the previous list, and automatic imports update both editors. Editorial filter edits already clear results. Metadata edits and immutable export snapshots still need work.

Streamlit AppTest reproduction, with network calls and downloads mocked:

- Initial fetch returned RICE and PRICE; Step 1 showed them, but Step 2 and the canonical list remained empty.
- After editing and classifying, changing the input left the earlier classification result present.
- A second fetch returned PLAN and PLANE, but Step 2 and the canonical list still contained PRICE.

Change: use one authoritative puzzle draft and one word-list editor, or synchronize through explicit callbacks before rendering widgets. Store the six actual letters, center, placeholder, SB Solver query, words, creator, filters, and rules version with each classification snapshot. Invalidate dependent results on edits and disable final export until inputs match that snapshot. A failed import should not attach a new puzzle to an old list.

### 3. Extraction must faithfully apply the first-result policy — medium priority

Evidence: `oed_parser.py:169`, `oed_parser.py:172`, `oed_parser.py:198`, `oed_parser.py:201`, `oed_parser.py:246`.

Using only the first search result is intentional and must be retained. The current code reads usage from `frequencyIndicator`'s `aria-valuenow` and rejects values of two or fewer, which implements the minimum-three-bars rule. It also applies the existing form, variant, proper-noun, slang, missing-frequency, and editorial-override checks. These are policy, rather than opportunities to broaden acceptance by scanning other results.

The reliability concern is whether the first result and its required fields have finished loading and whether the selectors still extract what editors see. Missing-title exceptions currently fall through as an empty title; other field failures similarly become missing/default data. That can change a decision without recording an extraction failure. The earlier synthetic unrelated-headword test described a possible behavior, but does not establish a defect under the user's intentionally first-result policy.

Change: continue to inspect only the first result. Validate that the page and required fields are ready, distinguish extraction failures from genuine missing data, and preserve the observed result, usage bars, rejection reason, and source link for review where permitted. Check representative first-result pages against staff decisions. Do not add exact-headword rejection, scan alternative results/senses, change the three-bar threshold, or change exclusions/overrides without an explicit editorial requirement.

### 4. Chrome automation does not fit a shared staff website — architectural blocker

Evidence: `sbsolver_parser.py:16`, `sbsolver_parser.py:34`, `sbsolver_parser.py:76`, `oed_parser.py:228`, `README.md:30`.

The SB Solver launcher executes macOS's `open -na Google Chrome`. Selenium runs on the machine hosting Streamlit. On a hosted deployment, the Chrome window would be on that server, rather than on a staff member's laptop; a typical Linux host also lacks this launcher. OED launches another visible browser. The extension sends to the visitor's `127.0.0.1:8765`, so the original pipeline also assumes local installation.

The fixed debug port, browser profile, and module-global pending verification state are shared within a host/process, rather than isolated per Streamlit session. This becomes a cross-user interference risk if deployed for multiple editors.

Change: for a shared website, replace the macOS launcher with a background server browser worker and send processing progress to the Streamlit UI. Staff do not need to watch Chrome during normal processing. Retain browser sessions, isolate each editor's browser/profile, and queue work if the host should run only one active browser job at a time. Pause on blocked access; add an authenticated remote viewer only if human verification is needed. Protect the app and any viewer with staff access controls, and keep browser-control ports internal. Any API or source-provided export alternative must reproduce the required behavior; substitute datasets do not satisfy the task. A local managed browser remains a transitional option. Neither hosting approach guarantees uninterrupted access to protected sites.

### 5. SB Solver can resume the wrong puzzle — high priority

Evidence: `sbsolver_parser.py:83`, `sbsolver_parser.py:88`, `sbsolver_parser.py:91`, `sbsolver_parser.py:111`.

Any current SB Solver `/cdn-cgi/` URL qualifies as a resumable verification session, even if the requested letters differ. The importer does not verify that the eventual page represents the requested puzzle, or validate extracted words against its letters and center. All selector timeouts are described as Cloudflare checks, even though a selector change, empty result, or failed load can produce the same timeout.

With a mocked unrelated challenge URL and pending letters unset, requesting pRincej returned BEET without navigating to the requested puzzle.

The challenge-loop follow-up removed the broad any-challenge shortcut. Resumption now requires a challenge URL and matching pending query letters; switching to different letters navigates to the requested puzzle. Offline regression verification passed. Final returned-page identity and complete-data checks remain pending.

Change: bind an import attempt to its requested puzzle and session, verify the destination puzzle identity after verification, and validate the extracted list. Distinguish blocked pages, confirmed empty results, and parser failures. Do not infer a complete response merely from finding the first matching element.

### 6. Clarify the six-letter puzzle and preserve its selected center — medium priority

Evidence: `oed_parser.py:29`, `oed_parser.py:60`, `oed_parser.py:82`, `oed_parser.py:124`, `app.py:104`, `app.py:147`, `oed_parser.py:338`.

The app calls the entire seven-character SB Solver input `puzzle_letters` and uses it as the puzzle title. The parser correctly requires seven distinct query letters, because this is six actual letters plus a placeholder. The placeholder varies, and the user requested that automatic removal not be introduced. Documentation should reflect this distinction without changing the existing query or source list. The README has now been corrected accordingly.

Manual lists also retain duplicates and arbitrary lines, and no central validator enforces the actual puzzle alphabet or center. A failed fetch can leave invalid query input stored as puzzle metadata. The center is inferred from the surviving words instead of retained from input; a diagnostic list of RICE and PRICE yields `C, E, I, R`. Word export independently performs the same inference.

Change: keep the existing seven-letter SB Solver input and variable-placeholder workflow, with the actual center uppercase. Do not automatically remove placeholder-containing words. Preserve the selected center throughout classification and export rather than deriving it from surviving words; keep the existing title/filename convention. Normalize and deduplicate pasted lists without adding new editorial restrictions. Focus on complete classification and the existing level policy for real six-letter puzzles.

### 7. The center-matrix utility mistakes unavailable data for zero words — medium priority

Evidence: `verify/sbsolver.py:64`, `verify/sbsolver.py:70`.

The utility waits for document readiness, not verified puzzle results. A fully loaded security page has no word elements and returns 0. This was reproduced with a fake complete document and no matching elements.

Change: reuse the same SB Solver access as the main app. Display unavailable/blocked distinctly from a verified count of zero. If this utility is intended for Hoo's Spelling, its UI should distinguish six actual centers from the placeholder. If it intentionally supports separate seven-letter puzzles, label and keep that mode distinct; confirm its intended use before changing it. Do not introduce automatic placeholder-word removal.

### 8. Exports overwrite shared server files — medium priority before shared deployment

Evidence: `app.py:188`, `app.py:189`, `app.py:206`, `oed_parser.py:393`.

Every results rerun writes a Word document in the server's current directory using the puzzle title as its filename. Editors generating the same letters can overwrite each other's file between saving and opening it for download. Files also accumulate, and the filename depends on metadata that the manual workflow does not reliably validate.

Change: build Word bytes with an in-memory buffer and generate both exports from the same immutable reviewed snapshot. Use a validated display filename, preserve source links, and regenerate only when the reviewed snapshot changes.

### 9. Progress is now visible; durable recovery remains pending — medium priority

Evidence: `oed_parser.py:220` (`classify_words`), `app.py:322`, `app.py:20`.

Each ordinary OED lookup sleeps 4–7 seconds before navigation. For 100 such words, intentional sleeps alone take about 7–12 minutes; network and result waits add time. The requested progress bar now shows completed word-processing attempts, total words, and the current word. It counts form rejections and unsuccessful lookup attempts as processed, rather than claiming every processed word has verified OED evidence. Cancellation, durable partial results, and resumption are still absent. Results live only in session memory; editorial lists can now be uploaded or pasted.

Change: retain the new progress indicator and save drafts, editorial decisions, and completed lookup outcomes independently of the UI rerun. For a shared app, use a background job with cancel/resume, bounded timeouts, backoff for transient errors, and an access-failure circuit breaker. Cache provider evidence only where the access agreement permits it; always distinguish stored editorial decisions from source data. Keep technical diagnostics available to maintainers while giving editors an actionable message.

### 10. Setup and repository hygiene need cleanup — lower priority

Evidence: `README.md:25`, `README.md:38`, `README.md:54`, `.gitignore:1`, `requirements.txt`, tracked file inventory.

The README's Windows virtual-environment path differs from the actual `my_venv` name, its sample `words.txt` is absent, and the active browser workflow is not explained. The repository tracks bytecode and `.DS_Store`; `.gitignore` does not ignore `my_venv` or `__pycache__`. No automated tests or deployment configuration are present in the tracked inventory. The inactive extension/import-server files obscure which path is supported, and `webdriver-manager` is declared but not imported.

Change: document one supported staff workflow, move any developer setup instructions out of that flow, retire the inactive extension once its replacement works, clean generated files from tracking, and add focused regression coverage for the failures above. Keep Selenium only if an optional local browser adapter still needs it.

## Data-access options verified against primary sources

- **Exact OED:** Oxford publishes an [OED Researcher API page](https://languages.oup.com/oed-researcher-api/) describing a prototype, registration of interest, and endpoints for words, surface forms, lemmatization, frequency values, and usage categories. This is a possible access route to investigate with UVA/OUP. It does not establish that newspaper production qualifies, that credentials are immediately available, that frequency values map directly to the UI's bars, or that first-result ordering can be reproduced. Verify all of these points and permitted storage before proposing it as equivalent to the required browser workflow.
- **Alternative sources are out of scope:** SB Solver and OED are mandatory. Oxford's [API FAQ](https://developer.oxforddictionaries.com/faq) distinguishes Oxford Dictionaries from OED, so it is not a replacement here. Recommendations for SCOWL/ESDB or another local candidate list have been withdrawn.
- **SB Solver:** A read-only web request to its home page received 403 in this review environment. I could not verify a supported API or export agreement from the accessible primary material. Treat provider-supported access as an open question, not as proof that no API exists. Normal browser copy/paste or permitted file import can provide a fallback, but that remains a manual step.

## Proposed staff workflow

1. **Create puzzle:** enter the six actual letters plus the chosen variable placeholder in the existing seven-character format, with the actual center uppercase. Enter the creator once and explain invalid input beside the field.
2. **Import from SB Solver:** fetch or paste/upload the SB Solver list. Retain its provenance and the current placeholder handling. Show the imported count and duplicate entries explicitly.
3. **Classify and review:** inspect only the first OED search result and apply the established criteria, including at least three usage bars. Apply the optional included/excluded lists as a final filter. Show accepted, rejected, and incomplete lookups with source, reason, and lookup state. Preserve the existing editorial override behavior and flag contradictory lists. Save evidence/decisions only as permitted and retry interrupted lookups without rerunning completed work.
4. **Finalize:** show the selected center, final count, levels, and review status. Export HTML/Word only from that reviewed snapshot. Allow a draft to be reopened by another editor.

Keep the first release small: Streamlit UI, accurate six-letter/placeholder documentation, fixed SB Solver and OED integrations, the existing editorial rules, optional final editorial filters, export functions returning bytes, and a modest draft/decision store. Access adapters can separate local browser versus supported hosted access to those same sources; they do not imply interchangeable dictionaries or word lists. SQLite can work for one persistent app instance; choose storage appropriate to the actual hosting model. Multi-instance or ephemeral hosting needs shared durable storage. Staff access control is appropriate for a shared editing tool.

## Suggested implementation order and acceptance checks

1. **Repair correctness first:** separate interrupted lookups from rejections; consolidate input state; document six letters plus the variable placeholder; preserve the actual center; read the first OED result reliably under the existing criteria; generate downloads in memory. Acceptance: a blocked response never silently removes a word and changing any dependent input prevents stale export. No automatic placeholder removal is added.
2. **Confirm existing behavior:** record representative real six-letter puzzles, their SB Solver lists, and staff classifications using the first OED result. Exercise frequency 2 versus 3, existing exclusions, missing data, and final editorial overrides. Acceptance: successful-page classifications match the established workflow, included words can override OED rejection within the candidate list, and excluded words are removed even if otherwise approved.
3. **Ship an extension-free workflow:** manage browser access to the same two sources, provide clear verification instructions and resumable progress, and support paste/upload of SB Solver words. For shared deployment, verify access to both sites and parity with OED's first-result order and criteria. If that cannot be established, retain the accepted local app path rather than substituting sources or changing rules.
4. **Add persistence and hosted operation:** saved drafts/decisions, access control, background progress where needed, and session isolation. Acceptance: disconnecting does not lose a completed review, and two editors' drafts/downloads cannot overwrite each other.
5. **Retire unused components and document:** remove the extension/import server and obsolete dependencies only after their replacement is verified; update staff instructions and add focused tests.

## Verification and limitations

The existing virtual environment was usable (Python 3.14.3, Streamlit 1.53.0, Selenium 4.39.0, python-docx 1.2.0). Offline checks exercised the real parser/rules functions using mocked Selenium objects, and Streamlit AppTest exercised the actual app with mocked lookup/export functions. No live OED login, CAPTCHA completion, Chrome launch, hosted deployment, or provider API integration was tested. This review distinguishes reproduced defects from code-inspection deployment risks and external access questions.

Confirmed requirements: six actual letters plus a variable seventh SB Solver placeholder, without new automatic removal; SB Solver's source list; OED as the dictionary; first-result-only classification; the established stringent editorial rules including at least three usage bars; and optional uploaded editorial inclusion/exclusion lists applied as a final filter. Shared staff access is preferred, and a local command-line Streamlit app is acceptable. University browser access is available; API credentials are not confirmed. Remaining questions are whether the center-matrix utility targets this six-letter workflow and whether supported hosted access preserves the exact existing source behavior.

## Requested upload feature implemented

Step 2's existing optional editorial-filter section now accepts one included-list `.txt` upload and one excluded-list `.txt` upload. Files use UTF-8, including UTF-8 files with a byte-order mark, with one word per line. Uploaded lists combine with the existing pasted lists and feed the existing `apply_editorial_filters` stage after OED classification. Inclusion overrides a rejection only for a word already in the candidate list; exclusion wins when lists conflict. Upload/paste changes clear earlier results so the next classification uses the current filters. Invalid text encoding produces an actionable error and disables classification until corrected. No source, placeholder-removal, first-result, or OED threshold changes were made.

Verification passed for optional/empty/BOM/invalid uploads, candidate-list preservation, post-OED inclusion/exclusion, conflict precedence, and the unchanged frequency-two versus frequency-three decision boundary. Streamlit AppTest exercised the actual UI path with upload returns and lookup/export mocked; it confirmed that filter edits clear results and invalid encoding disables classification. Broader stale-input defects documented above remain pending, and hosted browser access has not been tested.

## Requested progress feature implemented

`classify_words` accepts an optional progress callback reporting processed count, total count, and current word before and after each candidate. Existing first-result classification and editorial criteria are preserved. Streamlit displays this progress and a completed-processing message. Starting a new classification clears the previous output; a startup-level exception produces an error instead of leaving stale results. Browser cleanup runs in `finally`.

Offline checks passed for successful lookups, missing results, navigation errors, form rejections, empty input, final editorial uploads, invalid-file blocking, and startup failures. AppTest verified that progress reaches 100% on completion. This change adds a visible progress indicator; it does not enable headless hosting or repair the pre-existing treatment of blocked lookups as rejections.

## SB Solver repeating-checkbox follow-up

The user reported that clicking the security checkbox repeatedly returns to the checkbox. The app attaches Selenium before loading/solving the challenge. Cloudflare's [supported-browser documentation](https://developers.cloudflare.com/cloudflare-challenges/reference/supported-browsers/) explicitly says automated browsers and frameworks such as Selenium are unsupported for solving production challenges. This makes automation a plausible contributor, but the cause of this particular loop has not been confirmed. Cloudflare also lists browser configuration, network issues, and detection errors in its [challenge-loop troubleshooting guide](https://developers.cloudflare.com/cloudflare-challenges/troubleshooting/challenge-solve-issues/).

Step 1 now presents a validated normal-browser puzzle link. Staff can open the same SB Solver puzzle in their usual browser and paste the site's words into Step 1, without an extension or another Selenium fetch. The source list, variable-placeholder handling, first OED result, and existing editorial criteria are retained. The automatic fetch remains available, but its timeout now recommends the normal-browser path rather than repeated retries. No browser profiles were deleted and no anti-detection or CAPTCHA-solving mechanism was added.

Offline tests passed for query validation, puzzle-bound retries, actionable timeouts, preserving the browser on timeout, normal-browser link creation, manual import without Selenium, two-way word-list transfer, classification invalidation, repeated fetches, and clearing the old list on a new puzzle. Actual challenge completion has not been verified. The next diagnostic is whether the exact puzzle URL succeeds in the user's normal browser. A shared site can support these manual SB Solver imports; dependable automated shared access is still unproven, and a remote viewer or progress bar does not make an unsupported automated challenge solvable.

## Saved-page import implemented

The user confirmed SB Solver access worked, but copying its formatted hyperlinks is inconvenient. A new offline importer, `sbsolver_import.py`, extracts only the links matched by the existing `table.bee-set td.bee-hover a` selector from a saved SB Solver HTML page. It preserves source order and word labels, removes duplicate words just as the automatic fetch does, and reads nested labels, HTML entities, UTF-8/BOM, and declared Latin-1/Windows-1252 content. It ignores unrelated navigation links and rejects files without the required word table. No alternative dictionary, generated word list, or placeholder removal is introduced.

The intended workflow is to save the successfully loaded puzzle with Chrome's **Save page as**, then upload its `.html` file in Step 1. The app will fill both word-list editors with plain words, eliminating manual formatting cleanup. Any accompanying asset folder is unnecessary. Chrome documents [saving pages to a file](https://support.google.com/chrome/answer/7343019?hl=en&co=GENIE.Platform%3DDesktop).

The UI integration was prepared separately while the user's OED test ran, then activated after the user authorized the changes. Step 1 now offers **Import a saved SB Solver page**, with an HTML upload and an explicit import button. Both editors receive the imported plain words, and previous classification results are cleared. Parser and Streamlit AppTest checks passed, including exact-selector extraction, nested formatting, order/deduplication, text encodings, unrelated-link exclusion, rejection of challenge pages, import into both steps without Selenium, and preservation of existing words on an invalid upload. A real user-saved SB Solver page has not yet been tested.
