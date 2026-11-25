# Owner instructions for Claude Code and all agents

Read `README.md`, `TASKS.md`, `manifests/canonical_assets.json` and this file BEFORE any asset changes.

1. Source is the exact owner Windows directory `C:\Users\sekip\Desktop\Character Reference Sheets\Character Refence Sheets`. Work **locally** on Windows for binary import; GitHub-only agents cannot see its files.
2. Repository was observed PUBLIC on 2026-11-25. Verify `gh api repos/Sekiph82/POVU-Brand-Vault --jq .private` returns `true` before committing ANY masters, logos, ico pack or business-only artwork. If not PRIVATE, STOP at metadata tasks and report the blocker.
3. Preserve byte-identical approved masters and new owner logo. Validate nine old known character hashes, plus one Bactro Gang ensemble sheet. Never count ensemble as villain #8.
4. Exact NEW logo and full original ICO package from owner folder supersede previous marketing logo after owner-designated file selection and SHA recording. Never reuse older logo just because it was approved.
5. Initial local audit: `python tools/import_windows_assets.py` (read-only). If more than one logo/ICO candidate, use explicit `--logo` and `--icons` from the owner's supplied folder, not a guess.
6. Once private, use `python tools/import_windows_assets.py --logo <relative-file> --icons <relative-zip> --publish` in the cloned Vault. This makes local copies but intentionally does NOT auto-push. Review `git status`, file sizes and SHA, then make a safe commit/push with `gh` authentication and verify GitHub bytes/checksums. Do NOT overwrite old masters or approve unverified files.
7. Propagate to Marketing Studio, FMCG ERP, and POVU content paths in PackLab as read-only, verified imports. `PackLab.ico` and unrelated FormuLab/game branding are out of scope. Update consumers' TASKS.md and maintain rollback versions.
8. For videos use existing owner-approved character cutouts, not new synthesized portraits. New poses are review-only until separately approved.
9. No GitHub Actions; no paid external APIs; no destructive git actions; no fabricated QA; no independent creation of additional characters. The source directory and logo are owned assets, not an invitation to redraw them.
