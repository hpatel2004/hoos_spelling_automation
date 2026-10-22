# Hosting pilot results

Status: **USER-CONFIRMED OED OUTPUT MATCH — repeatability pending.**

## Latest hosted test — October 22, 2026

The user reports that automatic SB Solver fetching did not work, but importing
the saved SB Solver HTML did, and the OED classification step worked on Render.
This supports feasibility of the intended HTML-import → hosted OED workflow.
The user subsequently supplied the SB Solver error: `SB Solver did not load a
readable word table within the hosted timeout.` The user suspects Cloudflare.
This establishes a timeout, not a confirmed challenge. Local diagnostics now
also check challenge titles and known challenge elements, including after a
navigation timeout. The change has not yet been tested on Render.

The user subsequently identified the tested query as `aNoyigq` (the ANOYIG
reference letter set, center N, placeholder Q) and confirmed that everything
turned out as expected in response to the accepted/removed-word and rejection-
reason comparison question. This is a user-confirmed output match for one hosted
run. Deployed revision, exact counts, and first-result evidence were not supplied;
repeatability and broader representative metadata checks remain pending.
Preserve manual levels and editorial overrides when comparing; those are separate
from OED evidence.

Automatic SB Solver acquisition remains unverified. Saved HTML import is the
demonstrated acquisition route; do not promise automatic fetching at launch.

## Earlier browser startup failure

The user provisioned a free Render service at
https://hoos-spelling-automation-software.onrender.com/ and reported on October 22,
2026: `Could not fetch words from SB Solver: Could not start the Chrome browser
used by SB Solver.` The deployed revision/runtime/region have not been confirmed.
Repository inspection confirms the old SB Solver path launches macOS Chrome using
`open -na Google Chrome`, which is incompatible with Render's Linux environment.

A Linux headless startup fix and root web-service Dockerfile were prepared.
All 26 offline regression checks pass. Docker is unavailable locally, so image
build remains unverified locally. The later user report above supplies hosted
workflow evidence but does not establish source permissions or reproducibility.
The isolated probe has not been reported as run against the sources. See
`RENDER_DEPLOYMENT.md` for deployment configuration.

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
