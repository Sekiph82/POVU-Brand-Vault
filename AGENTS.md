# Owner instructions for Claude Code and all agents

Read `README.md`, `TASKS.md`, `manifests/canonical_assets.json` and this file BEFORE any asset changes.

1. Source is the exact owner Windows directory `C:\Users\sekip\Desktop\Character Reference Sheets\Character Refence Sheets`. Work **locally** on Windows for binary import; GitHub-only agents cannot see its files.
2. Owner explicitly chose PUBLIC visibility and authorized publication of only the designated nine character masters, Bactro Gang group, latest approved logo and original ICO pack. Verify `gh api repos/Sekiph82/POVU-Brand-Vault --jq .private` returns `false`. Do not change visibility; exclude confidential business data, secrets and unrelated files.
3. Preserve byte-identical approved masters and new owner logo. Compute new hashes from the nine current owner originals only. No prior hash matching or other source folders. Verify one Bactro Gang ensemble sheet. Never count ensemble as villain #8.
4. Use only the logo and complete ICO package from the specified owner folder; calculate fresh hashes.
5. Initial local audit: `python tools/import_windows_assets.py` (read-only). If more than one logo/ICO candidate, use explicit `--logo` and `--icons` from the owner's supplied folder, not a guess.
6. After dry-run verification, use `python tools/import_windows_assets.py --logo <relative-file> --icons <relative-zip> --publish --allow-public-assets --review-source` in the cloned Vault. This makes local copies but intentionally does NOT auto-push. Review `git status`, file sizes and SHA, then make a safe commit/push with `gh` authentication and verify GitHub bytes/checksums. Do NOT overwrite old masters or approve unverified files.
7. Propagate to FMCG ERP, POVU content paths in PackLab and future authorized media projects. Distribute assets as read-only, verified imports. `PackLab.ico` and unrelated FormuLab/game branding are out of scope. Update consumers' TASKS.md and maintain rollback versions.
8. For videos use existing owner-approved character cutouts, not new synthesized portraits. New poses are review-only until separately approved.
9. No GitHub Actions; no paid external APIs; no destructive git actions; no fabricated QA; no independent creation of additional characters. The source directory and logo are owned assets, not an invitation to redraw them.
