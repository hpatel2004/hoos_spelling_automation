# Hosted source-access pilot

This isolated command-line probe is a development tool, not the editor website.
It does not modify the existing app, classify words, or claim hosting feasibility.
The larger overhaul is gated on permitted, reproducible OED access from the actual host.

Before a network run, review applicable source terms/permissions. Choose the
lowest-cost suitable host within the agreed budget; no paid resources have been
provisioned by the agent. The user has now created a free Render service; see
`RENDER_DEPLOYMENT.md` for the browser startup fix and current limitations.

Build from the repository root on a Docker-capable machine:

```sh
docker build -f pilot/Dockerfile -t hoos-access-pilot .
docker run --rm hoos-access-pilot --access-reviewed --host-label 'platform/plan/region' \
  --query reGicdq --query gaiNoqy --word DEGREE --word CIERGE \
  --word DIRIGE --word GREEGREE --word REGIE --word GRICED \
  --word DERIG --word NONAGON --word ONIONY --word AGONY
```

Run on the actual candidate host and save the JSON output as sanitized pilot
evidence. A local run cannot establish hosted access. The image installs Chromium
and its compatible driver together; OS package versions are not frozen yet.
Record the image digest and package versions for each run before comparing results.

The probe uses one headless browser, limits each run to two puzzles/ten OED words,
paces requests, stops a provider on its first unsuccessful observation, and closes
the browser. It does not retry or solve challenges. Missing frequency/result
selectors remain unresolved, including known historical no-result words. Observed
SB Solver tables still require manual completeness checks. No cookies, full page
HTML, or browser profiles are retained; only selected metadata and words appear
in the report. Confirm permitted retention before saving it.

Compare at least two runs with normal unauthenticated editor-browser observations.
Verify first-result ordering, labels, frequency, candidate completeness, resource
use and cost. Record the decision in `HOSTING_PILOT_RESULTS.md`. This probe alone
does not exercise the future hosted UI, rich clipboard, or durable jobs.
