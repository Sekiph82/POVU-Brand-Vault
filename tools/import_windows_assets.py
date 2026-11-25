#!/usr/bin/env python3
"""Stage and (only after private-repository verification) publish the owner's exact POVU artwork.
Python standard library only. Never generates or changes a pixel.
"""
import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path

SOURCE_DEFAULT = r"C:\Users\sekip\Desktop\Character Reference Sheets\Character Refence Sheets"
ROOT = Path(__file__).resolve().parents[1]
KNOWN = json.loads((ROOT / "manifests" / "canonical_assets.json").read_text(encoding="utf-8"))
ALLOWED_ICON_SUFFIXES = {".png", ".ico", ".icns", ".svg", ".webp", ".jpg", ".jpeg", ".json", ".txt"}
def sha(path):
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()

def files_under(folder):
    return sorted(p for p in folder.rglob("*") if p.is_file() and ".git" not in p.parts)

def copy_exact(src, dst):
    dst.parent.mkdir(parents=True, exist_ok=True)
    if dst.exists():
        if sha(dst) != sha(src):
            raise RuntimeError(f"REFUSE OVERWRITE: {dst}")
        return
    shutil.copy2(src, dst)
    if sha(src) != sha(dst):
        raise RuntimeError(f"COPY HASH FAILURE: {src}")

def verified_private():
    try:
        r = subprocess.run(
            ["gh", "api", "repos/Sekiph82/POVU-Brand-Vault", "--jq", ".private"],
            capture_output=True, text=True, timeout=25, check=True,
        )
        return r.stdout.strip().lower() == "true"
    except (OSError, subprocess.SubprocessError):
        return False

def parse_file_arg(value, root):
    if not value:
        return None
    p = Path(value)
    if not p.is_absolute():
        p = root / p
    p = p.resolve()
    if not p.is_file():
        raise RuntimeError(f"Missing file: {p}")
    if root.resolve() not in p.parents:
        raise RuntimeError(f"File must be inside source folder: {p}")
    return p

def ingest(source, logo_name, icons_name, publish):
    if not source.is_dir():
        raise RuntimeError(f"LOCAL SOURCE MISSING: {source}. This tool must run on the owner's Windows computer.")
    originals = files_under(source)
    by_hash = {}
    for p in originals:
        if p.suffix.lower() in {".png", ".jpg", ".jpeg", ".webp"}:
            by_hash.setdefault(sha(p), []).append(p)
    records = []
    for item in KNOWN["characters"]:
        candidates = by_hash.get(item["known_sha256"], [])
        if not candidates:
            raise RuntimeError(f"CHARACTER MISSING OR CHANGED: {item['id']} sha256 {item['known_sha256']}")
        records.append((item["id"], candidates[0], f"brand/characters/{item['id']}/{item['old_source_filename']}"))
    group = [p for p in originals if "bactro" in p.name.lower() and "gang" in p.name.lower()]
    if len(group) != 1:
        raise RuntimeError("Expected exactly one Bactro Gang group image, found: " + str([str(x) for x in group]))
    records.append(("BACTRO_GANG", group[0], f"brand/groups/bactro-gang/{group[0].name}"))
    logo = parse_file_arg(logo_name, source)
    icons = parse_file_arg(icons_name, source)
    if logo is None:
        opts = [p for p in originals if "povu" in p.name.lower() and "logo" in p.name.lower()
                and p.suffix.lower() in {".png", ".jpg", ".jpeg", ".webp", ".svg"}]
        if len(opts) != 1:
            raise RuntimeError("Select the exact NEW owner-approved logo using --logo relative/path. Candidates: " + str([str(x) for x in opts]))
        logo = opts[0]
    if icons is None:
        opts = [p for p in originals if p.suffix.lower() == ".zip" and
                ("ico" in p.name.lower() or "icon" in p.name.lower())]
        if len(opts) != 1:
            raise RuntimeError("Select the original ICO package with --icons relative/path. ZIP candidates: " + str([str(x) for x in opts]))
        icons = opts[0]
    if logo.suffix.lower() not in {".png", ".svg", ".webp", ".jpg", ".jpeg"}:
        raise RuntimeError("Unsupported master logo extension")
    if icons.suffix.lower() not in {".zip", ".ico"}:
        raise RuntimeError("Use the original ICO package ZIP or .ico file")
    records.append(("POVU_NEW_LOGO", logo, f"brand/logos/{logo.name}"))
    records.append(("POVU_ICON_PACKAGE", icons, f"brand/icons/{icons.name}"))
    digest_list = [dict(id=id, file=dest, sha256=sha(src), bytes=src.stat().st_size) for id, src, dest in records]
    if len(records) != 12:
        raise RuntimeError("Expected nine characters, one group, logo and icon package")
    print(json.dumps(dict(found=len(records), assets=digest_list), indent=2))
    if not publish:
        print("DRY RUN ONLY. Nothing copied or uploaded. Use --publish AFTER PRIVATE visibility verification.")
        return
    if not verified_private():
        raise RuntimeError("STOP: GitHub does NOT confirm POVU-Brand-Vault is PRIVATE. No binary upload permitted.")
    if not (ROOT / ".git").is_dir():
        raise RuntimeError("Run on locally cloned POVU-Brand-Vault Git repository")
    for id, src, dest in records:
        copy_exact(src, ROOT / dest)
    if icons.suffix.lower() == ".zip":
        with zipfile.ZipFile(icons) as z:
            for entry in z.infolist():
                if entry.is_dir():
                    continue
                name = Path(entry.filename.replace("\\", "/"))
                if name.is_absolute() or ".." in name.parts or name.suffix.lower() not in ALLOWED_ICON_SUFFIXES:
                    raise RuntimeError("Unexpected/unsafe ICO archive entry: " + entry.filename)
                if entry.file_size > 32 * 1024 * 1024:
                    raise RuntimeError("ICO archive entry too large: " + entry.filename)
                target = ROOT / "brand" / "icons" / "extracted" / name
                target.parent.mkdir(parents=True, exist_ok=True)
                content = z.read(entry)
                if target.exists() and hashlib.sha256(target.read_bytes()).digest() != hashlib.sha256(content).digest():
                    raise RuntimeError("Refuse replacing existing icon: " + str(target))
                if not target.exists():
                    target.write_bytes(content)
    report = {"schema_version": "1.0", "status": "LOCAL_HASH_VERIFIED_AWAITING_GIT_PUSH", "assets": digest_list}
    output = ROOT / "manifests" / "approved-release-local.json"
    if output.exists():
        raise RuntimeError("Refuse replacing prior manifest: " + str(output))
    output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(f"LOCAL COPY OK. NO AUTOMATIC COMMIT/PUSH. Agent must review, git add, commit, push, and verify every GitHub blob: {output}")

def main():
    a = argparse.ArgumentParser()
    a.add_argument("--source", default=SOURCE_DEFAULT)
    a.add_argument("--logo", help="Exact newest owner-approved logo relative to source root")
    a.add_argument("--icons", help="Exact owner-approved ICO ZIP or ICO file relative to source root")
    a.add_argument("--publish", action="store_true", help="Copy into cloned Vault ONLY after GitHub confirms private")
    o = a.parse_args()
    try:
        ingest(Path(o.source), o.logo, o.icons, o.publish)
    except (RuntimeError, OSError, ValueError, zipfile.BadZipFile) as exc:
        print("BLOCKED:", exc, file=sys.stderr)
        sys.exit(2)

if __name__ == "__main__":
    main()
