# Review queue — 2026-11-27

## Highest-priority verification
1. Inspect private `SYMBIOTYC/SYMBIOTYC-CLOUD` and private Cloud Wiki. Confirm exact deployed resources separately from README and CI evidence.
2. Inspect `SYMBIOTYC/CY-cyborg_model` and separate model weights, model code, CYIDE extension, API worker and gateway. Confirm model identity, license, hosting and API health.
3. Reconcile CY CLI source `SYMBIOTYC/cy-cli` with release repository `SYMBIOTYC/CY_CLI`; inspect release tags and checksums and confirm platform artifacts.
4. Verify whether `cy.symbiotyc.workers.dev/v1` is currently healthy and whether the Cloudflare Worker is production-routed.
5. Verify Spine-Link production deployment and resolve repository homepage `spinepreview-vercel.vercel.app` versus user-supplied `spine-link.vercel.app`.
6. Confirm the legal/IP ownership relationship for `vladleopold/2Spine`, `3Spine`, `3Spine-core`, and the SA public CI wrappers. SA-Wiki states SYMBIOTYC owns the SA/2Spine product domain for platform and engineering governance; legal/IP title remains separate.
7. Verify 3Spine public API destinations and service health. Its README confirms the public site is frontend-only and the engine/backend remain private.
8. Verify ZeyWin Ads SDK distribution, publisher dashboard, live ad-serving endpoints and policy/compliance posture. Do not classify the generic `vlAds` starter template as an implemented ad platform.
9. Verify the live GracePlan Vercel deployment and relay health; do not expose HAR file, user data or secrets.
10. Confirm public profiles and roles for UkrainianDevelopers, Inna Kuvardina and Vlad Leopold Chaplyhin.

## Source-confirmed implementation facts
- CYIDE is a VS Code extension fork branded CY, with a local adapter between Codex Responses API and the CY gateway.
- CY CLI is a Rust coding-agent CLI; README documents v0.3.4 and macOS/Linux/Windows build targets. `CY_CLI` is a separate binary-release repository.
- 2Spine is a macOS drag-and-drop Spine project packager/converter; README reports version 4.8.14 and MIT license.
- 3Spine public repository is frontend-only; its README identifies the GitHub Pages URL and says the engine/backend remain private.
- 3Spine-core README documents a local Docker backend, Python HTTP service on port 8080, and native Linux converter.
- ZeyWinAdsSDK-Unity README documents a Unity mobile SDK with interstitial, rewarded, banner, native and popup formats and AdMob fallback mediation.
- CY API Worker source and Wrangler config exist; production endpoint health remains unverified.
- CLOUD-COMPUTE, CLOUD-CPU, CLOUD-VPS and Worker-Registry READMEs explicitly state that bootstrap CI does not prove deployed compute, persistent workers, VPS or registry service.
- GracePlan repository tree includes API bridge, desktop relay, browser extension manifest and deployment documentation.

## Inventory boundary
The 44 repositories under `vladleopold` are an owner-scoped candidate inventory. They are not automatically counted as SYMBIOTYC-owned assets. Private source repositories are recorded by metadata only.
