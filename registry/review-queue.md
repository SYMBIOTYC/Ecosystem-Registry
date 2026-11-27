# Review queue — 2026-11-27

## Highest-priority verification
1. Inspect `SYMBIOTYC/SYMBIOTYC-CLOUD`, `CLOUD`, `CLOUD-COMPUTE`, `CLOUD-CPU`, `CLOUD-VPS`, `Worker-Registry` and the private Cloud Wiki. Record PR and workflow evidence, but do not infer production deployment from CI.
2. Reconcile `SYMBIOTYC/cy-cli` and `SYMBIOTYC/CY_CLI`: determine canonical CLI, whether one is a mirror, and release/package names.
3. Inspect `SYMBIOTYC/CY-cyborg_model`, `CYIDE`, `cy-api-worker` and private `SpineAnimator/CYBORG`; separate model weights, model code, API and IDE.
4. Inspect private `vladleopold/2Spine` and `vladleopold/3Spine-core`; map them to public wrappers and document ownership/access boundaries.
5. Verify Spine-Link production deployment and resolve repository homepage `spinepreview-vercel.vercel.app` versus user-supplied `spine-link.vercel.app`.
6. Inspect `vlAds`, `ZeyWinAdsSDK-Unity`, `zey-win.github.io`, and identify whether Ads and Arbitrage are separate products or a shared system.
7. Inspect GracePlan manifest, API bridge, relay service and actual Vercel deployment. Do not expose HAR file or secrets in the registry.
8. Confirm the public role and domain ownership for UkrainianDevelopers, Inna Kuvardina and Vlad Leopold Chaplyhin.

## SpineAnimator inventory notes
The SA-Wiki repository contains a repository inventory dated 2026-11-27 with 18 repositories. It explicitly warns that back-* repositories are README placeholders, public runners are ephemeral GitHub-hosted CI, three wrappers point to private `vladleopold/3Spine-core`, and `spine-scripts` is deprecated.

## Owner relationship
The SA-Wiki states that SYMBIOTYC owns the 2Spine / SA product domain for platform and engineering governance, while legal/IP title must be recorded separately. Preserve this as owner-declared governance evidence, not legal proof.
