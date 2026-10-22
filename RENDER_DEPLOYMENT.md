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
   Streamlit starts before testing a fetch such as `reGicdq`.

Do not use `pilot/Dockerfile` as the web-service Dockerfile: it runs a one-shot
command-line probe and does not serve the app.

If Chromium starts but SB Solver challenges the server, the app reports that
explicitly. Use the normal-browser link and saved HTML/paste fallback; this
change cannot guarantee source access. Compare the candidate list with the
reference puzzle before treating acquisition as verified.

## Pilot limitations

The OED browser uses the same headless startup on Linux. Hosted OED access and
editorial parity are still unverified. The legacy classifier still conflates
some technical failures with rejections, so its hosted output is not ready for
publication. Use the isolated source probe to establish access before the broader
overhaul. Free Render storage/jobs are not yet durable. The Docker image has not
been built locally in this environment because Docker is unavailable; a successful
Render build and hosted smoke test are still required.

Official setup references: [Docker deployment](https://render.com/docs/docker)
and [changing an existing runtime](https://render.com/docs/native-runtimes#changing-a-services-runtime).
