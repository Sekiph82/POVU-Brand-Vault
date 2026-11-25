#!/usr/bin/env python3
"""Stage the owner's exact POVU artwork for the owner-authorized PUBLIC Vault.
Python standard library only. Never generates or changes a pixel.
"""
import argparse
import hashlib
import json
import re
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
    source = source.resolve()
    originals = [p for p in files_under(source) if not p.is_symlink() and source in p.resolve().parents]
    records = []
    used = set()
    pictures = [p for p in originals if p.suffix.lower() in {".png", ".jpg", ".jpeg", ".webp"}]
    def normalized(s):
        return re.sub(r"[^a-z0-9]", "", s.lower())
    for item in KNOWN["characters"]:
        name = normalized(item["name"])
        available = [p for p in pictures if p not in used and
                     not ("bactro" in p.stem.lower() and "gang" in p.stem.lower()) and
                     "logo" not in p.stem.lower() and
                     not any("icon" in part.lower() or "ico" in part.lower()
                             for part in p.relative_to(source).parts[:-1])]
        candidates = [p for p in available if name in normalized(p.stem)]
        if len(candidates) == 1:
            p = candidates[0]
            print(f"FOUND: {item['id']} -> {p.relative_to(source)}")
        elif review_source:
            p = choose(item["name"] + " (current source folder)", candidates or available, source)
        else:
            print("Source candidates:", [str(p.relative_to(source)) for p in candidates or available])
            raise RuntimeError("Ambiguous or missing name for " + item["id"] + "; run with --review-source to select from this folder.")
        if any(sha(p) == sha(x) for x in used):
            raise RuntimeError("Same image cannot represent multiple individual characters")
        used.add(p)
        records.append((item["id"], p, f"brand/characters/{item['id']}/{p.name}"))
    group = [p for p in pictures if p not in used and "bactro" in p.name.lower() and "gang" in p.name.lower()]
    if len(group) != 1:
        if not review_source:
            raise RuntimeError("Expected exactly one Bactro Gang group image, found: " + str([str(x) for x in group]))
        group = [choose("Bactro Gang GROUP sheet (not an individual villain)", group or [p for p in pictures if p not in used], source)]
    if any(sha(group[0]) == sha(p) for p in used):
        raise RuntimeError("Group sheet duplicates an individual character")
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
        opts.extend(p for p in source.rglob("*") if p.is_dir() and not p.is_symlink() and source in p.resolve().parents and
                    ("ico" in p.name.lower() or "icon" in p.name.lower()) and
                    any(f.suffix.lower() == ".ico" for f in files_under(p)))
        if not opts:
            opts = [p for p in originals if p.suffix.lower() == ".ico"]
        if len(opts) != 1:
            if not review_source:
                raise RuntimeError("Select the original ICO ZIP, .ico or icon folder with --icons relative/path. Candidates: " + str([str(x) for x in opts]))
            icons = choose("original complete ICO package", opts or [p for p in originals if p.suffix.lower() in {".zip", ".ico"}], source)
        else:
            icons = opts[0]
    if logo in used or any(sha(logo) == sha(p) for p in used):
        raise RuntimeError("Logo cannot be a character or group sheet")
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
    digest_list = [dict(id=id, file=dest, source_filename=src.name, sha256=sha(src), bytes=src.stat().st_size) for id, src, dest in records]
    if len({row["file"].lower() for row in digest_list}) != len(records):
        raise RuntimeError("Duplicate destination")
    if any(row["bytes"] > 100 * 1024 * 1024 for row in digest_list):
        raise RuntimeError("Asset exceeds ordinary GitHub file limit; no paid storage will be used")
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
    for p in sorted((ROOT / "brand" / "icons" / "extracted").rglob("*")):
        if p.is_file():
            digest_list.append(dict(id="POVU_ICON_EXTRACTED", file=p.relative_to(ROOT).as_posix(), sha256=sha(p), bytes=p.stat().st_size))
    report = {"schema_version": "1.0", "status": "LOCAL_HASH_VERIFIED_AWAITING_GIT_PUSH", "assets": digest_list, "authority": "owner-selected current source folder"}
    by_id = {row["id"]: row for row in digest_list}
    manifest = json.loads(json.dumps(KNOWN))
    for item in manifest["characters"]:
        row = by_id[item["id"]]
        item.update(current_master_path=row["file"], sha256=row["sha256"], verified=True)
    for key, asset_id in (("group_sheet", "BACTRO_GANG"), ("logo", "POVU_NEW_LOGO")):
        row = by_id[asset_id]
        manifest[key].update(current_master_path=row["file"], sha256=row["sha256"], verified=True)
    manifest["ico_package"] = {"archive_path": by_id.get("POVU_ICON_PACKAGE", {}).get("file"),
        "extracted_files": [row for row in digest_list if row["id"].startswith("POVU_ICON")],
        "verified": True}
    manifest["status"] = "LOCAL_HASH_VERIFIED_AWAITING_GIT_PUSH"
    output = ROOT / "manifests" / "approved-release-local.json"
    if output.exists() and json.loads(output.read_text(encoding="utf-8")) != report:
        raise RuntimeError("Refuse replacing a different prior release manifest: " + str(output))
    output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    (ROOT / "manifests" / "canonical_assets.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(f"LOCAL COPY OK. NO AUTOMATIC COMMIT/PUSH. Agent must review, git add, commit, push, and verify every GitHub blob: {output}")

def main():
    a = argparse.ArgumentParser()
    a.add_argument("--source", default=SOURCE_DEFAULT)
    a.add_argument("--logo", help="Exact newest owner-approved logo relative to source root")
    a.add_argument("--icons", help="Exact owner-approved ICO ZIP or ICO file relative to source root")
    a.add_argument("--publish", action="store_true", help="Copy selected owner assets into the cloned Vault; does not push")
    a.add_argument("--allow-public-assets", action="store_true", help="Acknowledge that the designated artwork will be publicly downloadable")
    a.add_argument("--review-source", action="store_true", help="Select files from the current owner source folder if names are ambiguous")
    o = a.parse_args()
    try:
        ingest(Path(o.source), o.logo, o.icons, o.publish, o.allow_public_assets, o.review_source)
    except (RuntimeError, OSError, ValueError, zipfile.BadZipFile) as exc:
        print("BLOCKED:", exc, file=sys.stderr)
        sys.exit(2)

if __name__ == "__main__":
    main()
