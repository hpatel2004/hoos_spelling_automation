# Render browser startup fix

The previous SB Solver path launched macOS Chrome using `open -na Google Chrome`
and a shared debug port. That cannot work on Render's Linux server. Linux now
launches an isolated headless Chromium session and closes it after every fetch.
The root Dockerfile installs Chromium and the matching driver together. Merely
deploying with Render's Python runtime is insufficient.

## Update the existing service

1. Push the reviewed changes to the GitHub `overhaul` branch.
2. In the existing Render service, open **Settings → Build → Source → Edit**.
3. Keep the same repository, set **Branch** to `overhaul`, and set **Runtime**
   (or Language) to **Docker**. Set Dockerfile Path to `./Dockerfile` and keep
   the build context at the repository root.
4. Leave the Docker Command override empty so the image starts Streamlit using
   Render's `PORT`. Keep the **Free** instance plan. No disk or paid worker is
   required for this startup test.
5. Deploy. Verify the build installs `chromium` and `chromium-driver` and that
   Streamlit starts before opening a puzzle such as `reGicdq` and importing its saved HTML page.

Do not use `pilot/Dockerfile` as the web-service Dockerfile: it runs a one-shot
command-line probe and does not serve the app.

## Current editor workflow

SB Solver challenged the hosted browser in testing. The user approved saved HTML
as the primary acquisition route, so the main app now shows the normal-browser
puzzle link, saving instructions, an always-visible HTML uploader, and an **Import
words** button. Imported words are shown read-only and carried into OED
classification. Automatic fetching and candidate-list paste controls have been
removed from the main app. Editorial inclusion/exclusion inputs remain available.

Compare the imported list with the source puzzle before classification. Importing
another page or changing puzzle letters clears prior classification results.
The automatic acquisition module remains available to the separate developer
pilot/verifier; it is not part of the editor-facing acquisition flow.

## Pilot limitations

The OED browser uses the same headless startup on Linux. The user reports a
successful hosted OED run after saved SB Solver HTML import on October 22, 2026.
Reference-result parity and repeatability still need verification; automatic
SB Solver fetching did not work in that test. See `HOSTING_PILOT_RESULTS.md`.
The legacy classifier still conflates
some technical failures with rejections, so its hosted output is not ready for
publication. Use the isolated source probe to establish access before the broader
overhaul. Free Render storage/jobs are not yet durable. The Docker image has not
been built locally in this environment because Docker is unavailable. The user
report is hosted smoke-test evidence, not a completed production acceptance test.

Official setup references: [Docker deployment](https://render.com/docs/docker)
and [changing an existing runtime](https://render.com/docs/native-runtimes#changing-a-services-runtime).
