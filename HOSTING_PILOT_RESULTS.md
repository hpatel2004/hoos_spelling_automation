# Hosting pilot results

Status: **BROWSER STARTUP FAILED — hosted OED access gate remains closed.**

The user provisioned a free Render service at
https://hoos-spelling-automation-software.onrender.com/ and reported on October 22,
2026: `Could not fetch words from SB Solver: Could not start the Chrome browser
used by SB Solver.` The deployed revision/runtime/region have not been confirmed.
Repository inspection confirms the old SB Solver path launches macOS Chrome using
`open -na Google Chrome`, which is incompatible with Render's Linux environment.

A Linux headless startup fix and root web-service Dockerfile are prepared locally.
All 26 offline regression checks pass. Docker is unavailable locally, so image
build and hosted startup remain unverified. This is not evidence that either
provider permits or supports hosted access. The new isolated probe has not run
against the sources. See `RENDER_DEPLOYMENT.md` for the required redeployment.

## Evidence required before proceeding

- Platform, plan, region, monthly budget and measured resource use.
- Run date, image digest, Chromium/driver/Python versions and revision.
- Source terms/permissions review and permitted evidence-retention policy.
- Two reference puzzle comparisons, including candidate counts/completeness.
- Representative first-OED-result metadata comparisons at multiple times.
- Blocked/incomplete behavior and sanitized probe reports.
- Explicit go/no-go decision. If OED access fails, pause implementation until
  supported access is available; do not ship manual-only classification instead.

See `pilot/README.md` for the reproducible probe. An `OBSERVED` result is evidence
to inspect, not an automatic pass of the hosting gate.
