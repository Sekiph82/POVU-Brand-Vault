# POVU Brand Vault

Canonical, versioned POVU brand asset contract for **POVU Kenya**. Owner decision: this repository remains **PUBLIC**. Publication is authorized for the nine designated character masters, Bactro Gang group sheet, latest approved POVU logo and original icon package only. These files will be publicly downloadable. Never commit credentials, confidential product data or other unapproved files. Existing official nine character masters belong to `Sekiph82/POVU-AI-Marketing-Studio` (private) and the owner's local Windows folder. Canonical assets are byte-preserved; SHA-256 is checked before any use.

## Canonical brand

Heroes: `H_BUBBLES` (Bubbles), `H_FLUFFY` (Fluffy). Villains: `V_GREASY_GLOOP`, `V_MUDZILLA`, `V_STAINY_INK`, `V_SMELLO`, `V_CRAZY`, `V_SNEAKY`, `V_LEADER`. A separate **Bactro Gang** group sheet is an ensemble reference, **not an eighth villain**.

The newest owner-approved POVU logo (transparent original) and its exact ICO package supersede the older 2026-10-16 marketing-studio logo **only after the new file has been individually fingerprinted and checked**. Never regenerate, recolor, shadow, flatten, crop, alter or redesign these masters.

## Ingestion status

**BLOCKED_LOCAL_SOURCE:** The owner's source files are stored at `C:\Users\sekip\Desktop\Character Reference Sheets\Character Refence Sheets`. GitHub connector sessions cannot access that Windows filesystem. There are no binary brand files in this repo yet. Never mark uploads or checksum QA complete from a manifest alone.

## Cross-project contract

Consumers: `POVU-AI-Marketing-Studio` (exact approved video cutouts), `PackLab` (product/label mockups, not replacement of PackLab's own app branding), `fmcg-erp-system` (POVU ERP/shop/PWA branding), and any *verified* POVU-branded future project. `FormuLab` has its own branding and must not be relabeled by mistake.

See `TASKS.md` for pending owner-local import, verified release, and consumer migration. Never publish a video or approve a print artifact solely based on generated artwork.

## Owner-local import procedure (Claude Code, Windows; no PowerShell installer)

Open a Claude Code session in a clone of this Vault repository on the **same Windows machine** as the supplied source directory. The agent should first run:

```text
python tools/import_windows_assets.py
python -m unittest discover -s tests -v
```

The importer runs read-only by default and reports all detected hashes. If the logo or ICO bundle is ambiguous, identify the owner's exact approved originals first and supply `--logo` and `--icons` as relative paths. ICO bundles can be ZIP archives, a single .ico, or a directory containing .ico and PNG variants.

Use `python tools/import_windows_assets.py --publish --allow-public-assets` after reviewing the dry run (and add `--logo`/`--icons` if selection is ambiguous). The importer verifies the expected PUBLIC repository; no visibility change is needed. It performs local byte-preserving copies and produces a release audit manifest; the Claude agent must then explicitly inspect, commit and push the binaries and verify remote content hashes.

Read `docs/CONSUMER_CONTRACT.md` and owner task tracker before updating Marketing Studio, PackLab or POVU ERP/Shop. Do not turn on expensive GitHub Actions.

