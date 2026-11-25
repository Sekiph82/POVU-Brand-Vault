#!/usr/bin/env python3
"""Stage the owner's exact POVU artwork for the owner-authorized PUBLIC Vault.
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

def verified_public():
    try:
        r = subprocess.run(
            ["gh", "api", "repos/Sekiph82/POVU-Brand-Vault", "--jq", ".private"],
            capture_output=True, text=True, timeout=25, check=True,
        )
        return r.stdout.strip().lower() == "false"
    except (OSError, subprocess.SubprocessError):
        return False

def parse_file_arg(value, root, allow_dir=False):
    if not value:
        return None
    p = Path(value)
    if not p.is_absolute():
        p = root / p
    p = p.resolve()
    if not p.is_file() and not (allow_dir and p.is_dir()):
        raise RuntimeError(f"Missing file or directory: {p}")
    if root.resolve() not in p.parents:
        raise RuntimeError(f"File must be inside source folder: {p}")
    return p

def choose(label, candidates, source):
    """Explicit user selection; never accept a filename guess as identity proof."""
    candidates = sorted(set(candidates))
    if not candidates:
        raise RuntimeError("No candidates for " + label)
    print("\nSELECT " + label)
    for i, p in enumerate(candidates, 1):
        print(f"  {i}. {p.relative_to(source)}")
    while True:
        raw = input("Enter file number (or Q to cancel): ").strip()
        if raw.lower() == "q":
            raise RuntimeError("Cancelled by owner")
        if raw.isdigit() and 1 <= int(raw) <= len(candidates):
            selected = candidates[int(raw)-1]
            print("Selected:", selected)
            return selected
        print("Invalid selection; try again.")

def ingest(source, logo_name, icons_name, publish, allow_public=False, review_source=False):
    if not source.is_dir():
        raise RuntimeError(f"LOCAL SOURCE MISSING: {source}. This tool must run on the owner's Windows computer.")
    originals = files_under(source)
    by_hash = {}
    for p in originals:
        if p.suffix.lower() in {".png", ".jpg", ".jpeg", ".webp"}:
            by_hash.setdefault(sha(p), []).append(p)
    records = []
    revisions = []
    used = set()
    pictures = [p for p in originals if p.suffix.lower() in {".png", ".jpg", ".jpeg", ".webp"}]
    for item in KNOWN["characters"]:
        candidates = by_hash.get(item["known_sha256"], [])
        if not candidates:
            print(f"CHARACTER MISSING OR CHANGED: {item['id']} historical SHA-256 {item['known_sha256']}")
            if not review_source:
                print("Available source images:")
                for p in pictures:
                    print(f"  {p.relative_to(source)}  SHA-256 {sha(p)}")
                raise RuntimeError("No exact historical hash. Use --review-source to review and explicitly select the current owner original.")
            p = choose(item["name"] + " (verify the actual character before selecting)", [p for p in pictures if p not in used], source)
            actual = sha(p)
            print("Historical SHA-256:", item["known_sha256"])
            print("Selected SHA-256:  ", actual)
            if input("Is this the correct current owner-approved original? Type YES: ").strip() != "YES":
                raise RuntimeError("Character revision not approved")
            revisions.append({"id": item["id"], "historical_sha256": item["known_sha256"], "selected_sha256": actual, "source_filename": p.name, "approval": "explicit_owner_selection"})
        else:
            p = candidates[0]
            print(f"EXACT MATCH: {item['id']} -> {p.relative_to(source)}")
        if p in used or any(sha(p) == sha(x) for x in used):
            raise RuntimeError("Same image cannot represent multiple individual characters")
        used.add(p)
        filename = Path(item["old_source_filename"]).with_suffix(p.suffix.lower()).name
        records.append((item["id"], p, f"brand/characters/{item['id']}/{filename}"))
    group = [p for p in pictures if p not in used and "bactro" in p.name.lower() and "gang" in p.name.lower()]
    if len(group) != 1:
        if not review_source:
            raise RuntimeError("Expected exactly one Bactro Gang group image, found: " + str([str(x) for x in group]))
        group = [choose("Bactro Gang GROUP sheet (not an individual villain)", group or [p for p in pictures if p not in used], source)]
    used.add(group[0])
    records.append(("BACTRO_GANG", group[0], f"brand/groups/bactro-gang/{group[0].name}"))
    logo = parse_file_arg(logo_name, source)
    icons = parse_file_arg(icons_name, source, allow_dir=True)
    if logo is None:
        opts = [p for p in originals if "povu" in p.name.lower() and "logo" in p.name.lower()
                and p.suffix.lower() in {".png", ".jpg", ".jpeg", ".webp", ".svg"}]
        opts = [p for p in opts if p not in used]
        if len(opts) != 1:
            if not review_source:
                raise RuntimeError("Select the exact NEW owner-approved logo using --logo relative/path. Candidates: " + str([str(x) for x in opts]))
            logo = choose("NEW owner-approved POVU logo", opts or [p for p in pictures if p not in used], source)
        else:
            logo = opts[0]
    if icons is None:
        opts = [p for p in originals if p.suffix.lower() == ".zip" and
                ("ico" in p.name.lower() or "icon" in p.name.lower())]
        opts.extend(p for p in source.rglob("*") if p.is_dir() and
                    ("ico" in p.name.lower() or "icon" in p.name.lower()) and
                    any(f.suffix.lower() == ".ico" for f in files_under(p)))
        if len(opts) != 1:
            if not review_source:
                raise RuntimeError("Select the original ICO ZIP, .ico or icon folder with --icons relative/path. Candidates: " + str([str(x) for x in opts]))
            icons = choose("original complete ICO package", opts or [p for p in originals if p.suffix.lower() in {".zip", ".ico"}], source)
        else:
            icons = opts[0]
    if logo in used or any(sha(logo) == sha(p) for p in used):
        raise RuntimeError("Logo cannot be a character or group sheet")
    if sha(logo) in {KNOWN["logo"]["previous_mkt_studio_png_sha256"], KNOWN["logo"]["previous_mkt_studio_jpg_sha256"]}:
        raise RuntimeError("Selected logo is the old Marketing Studio logo, not the requested new one")
    if logo.suffix.lower() not in {".png", ".svg", ".webp", ".jpg", ".jpeg"}:
        raise RuntimeError("Unsupported master logo extension")
    if not icons.is_dir() and icons.suffix.lower() not in {".zip", ".ico"}:
        raise RuntimeError("Use the original ICO package ZIP, .ico file or icon directory")
    records.append(("POVU_NEW_LOGO", logo, f"brand/logos/{logo.name}"))
    if icons.is_dir():
        icon_files = files_under(icons)
        if not icon_files or not any(f.suffix.lower() == ".ico" for f in icon_files):
            raise RuntimeError("Icon folder must include at least one .ico file")
        for i, file in enumerate(icon_files):
            if file.suffix.lower() not in ALLOWED_ICON_SUFFIXES:
                raise RuntimeError("Unexpected icon package file: " + str(file))
            records.append((f"POVU_ICON_{i+1}", file, "brand/icons/" + icons.name + "/" + file.relative_to(icons).as_posix()))
    else:
        records.append(("POVU_ICON_PACKAGE", icons, f"brand/icons/{icons.name}"))
    digest_list = [dict(id=id, file=dest, sha256=sha(src), bytes=src.stat().st_size) for id, src, dest in records]
    if len(records) < 12:
        raise RuntimeError("Expected nine characters, one group, logo and at least one icon file")
    print(json.dumps(dict(found=len(records), assets=digest_list), indent=2))
    if not publish:
        print("DRY RUN ONLY. Nothing copied or uploaded. Use --publish --allow-public-assets for the owner-authorized public asset set.")
        return
    if not allow_public:
        raise RuntimeError("Public publication requires --allow-public-assets; only the designated owner artwork is authorized.")
    if not verified_public():
        raise RuntimeError("STOP: GitHub does not confirm the expected PUBLIC Vault. Check gh authentication and repository.")
    if not (ROOT / ".git").is_dir():
        raise RuntimeError("Run on locally cloned POVU-Brand-Vault Git repository")
    if review_source:
        print("\nSelected files (publicly downloadable after push):")
        for asset_id, src, dest in records:
            print(f"  {asset_id}: {src.relative_to(source)} -> {dest}")
        if input("Approve these exact files for PUBLIC upload? Type PUBLISH: ").strip() != "PUBLISH":
            raise RuntimeError("Cancelled before copying")
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
    report = {"schema_version": "1.0", "status": "LOCAL_HASH_VERIFIED_AWAITING_GIT_PUSH", "assets": digest_list, "owner_approved_character_revisions": revisions}
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
    a.add_argument("--publish", action="store_true", help="Copy selected owner assets into the cloned Vault; does not push")
    a.add_argument("--allow-public-assets", action="store_true", help="Acknowledge that the designated artwork will be publicly downloadable")
    a.add_argument("--review-source", action="store_true", help="Interactively review and explicitly approve changed historical source hashes; never silently substitute artwork")
    o = a.parse_args()
    try:
        ingest(Path(o.source), o.logo, o.icons, o.publish, o.allow_public_assets, o.review_source)
    except (RuntimeError, OSError, ValueError, zipfile.BadZipFile) as exc:
        print("BLOCKED:", exc, file=sys.stderr)
        sys.exit(2)

if __name__ == "__main__":
    main()
