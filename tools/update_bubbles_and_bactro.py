"""Update ONLY Bubbles and Bactro Gang from the owner's sole source folder.
Preserve exact bytes, all other assets, and both manifests; no paid services.
Run from a clean Vault checkout after git pull --ff-only.
"""
import hashlib
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = Path(r"C:\Users\sekip\Desktop\Character Reference Sheets\Character Refence Sheets")
CANON = ROOT / "manifests/canonical_assets.json"
RELEASE = ROOT / "manifests/approved-release-local.json"
def git(*args):
    return subprocess.check_output(["git", *args], cwd=ROOT, text=True).strip()
def digest(data):
    return hashlib.sha256(data).hexdigest()
def resolve_inside(base, rel):
    p = (base / rel).resolve()
    p.relative_to(base.resolve())
    return p
def main():
    if git("status", "--porcelain"):
        raise RuntimeError("Local Vault not clean; review changes first.")
    if git("remote", "get-url", "origin").rstrip("/") not in ("https://github.com/Sekiph82/POVU-Brand-Vault.git", "https://github.com/Sekiph82/POVU-Brand-Vault"):
        raise RuntimeError("Wrong repository")
    if not SOURCE.is_dir():
        raise RuntimeError("Missing owner source folder")
    canon = json.loads(CANON.read_text(encoding="utf-8"))
    release = json.loads(RELEASE.read_text(encoding="utf-8"))
    rows = release["assets"]
    for row in rows:
        p = resolve_inside(ROOT, row["file"])
        if digest(p.read_bytes()) != row["sha256"]:
            raise RuntimeError("Existing Vault bytes do not match its own manifest: " + row["file"])
    targets = {"H_BUBBLES": next(c for c in canon["characters"] if c["id"] == "H_BUBBLES"),
               "BACTRO_GANG": canon["group_sheet"]}
    plan = []
    for asset_id, entry in targets.items():
        row = next(r for r in rows if r["id"] == asset_id)
        if row["file"] != entry["current_master_path"] or row["sha256"] != entry["sha256"]:
            raise RuntimeError("Vault manifests disagree: " + asset_id)
        dest = resolve_inside(ROOT, row["file"])
        candidates = [p for p in SOURCE.rglob(dest.name) if p.is_file() and not p.is_symlink()
                      and p.resolve().is_relative_to(SOURCE.resolve())]
        if len(candidates) != 1:
            needle = "bubbles" if asset_id == "H_BUBBLES" else "bactro gang"
            candidates = [p for p in SOURCE.rglob("*.png") if needle in p.stem.lower()
                          and p.is_file() and not p.is_symlink() and p.resolve().is_relative_to(SOURCE.resolve())]
            if not candidates:
                raise RuntimeError("No matching source for " + asset_id)
            print("Select current source for", asset_id)
            for i, p in enumerate(candidates, 1):
                print(i, p.relative_to(SOURCE))
            choice = input("File number (Q cancels): ").strip()
            if not choice.isdigit() or not 1 <= int(choice) <= len(candidates):
                raise RuntimeError("Cancelled or invalid selection")
            candidates = [candidates[int(choice)-1]]
        src = candidates[0]
        data = src.read_bytes()
        if not data.startswith(b"\x89PNG\r\n\x1a\n") or len(data) > 100*1024*1024:
            raise RuntimeError("Expected a PNG under GitHub ordinary Git size limit")
        print(asset_id, src.name, len(data), digest(data))
        plan.append((entry, row, dest, src, data))
    if digest(plan[0][4]) == digest(plan[1][4]):
        raise RuntimeError("Duplicate source images")
    if input("Replace ONLY these two public Vault references? Type PUBLISH: ").strip() != "PUBLISH":
        raise RuntimeError("Cancelled")
    for entry, row, dest, src, data in plan:
        dest.write_bytes(data)
        if dest.read_bytes() != data:
            raise RuntimeError("Copy verification failed")
        row.update(sha256=digest(data), bytes=len(data), source_filename=src.name)
        entry.update(sha256=digest(data), verified=True)
    for path, value in ((CANON, canon), (RELEASE, release)):
        value["status"] = "APPROVED_RELEASE"
        path.write_text(json.dumps(value, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
    for row in rows:
        if digest(resolve_inside(ROOT, row["file"]).read_bytes()) != row["sha256"]:
            raise RuntimeError("Post-update verification failed: " + row["file"])
    paths = [str(x[2].relative_to(ROOT)) for x in plan] + ["manifests/canonical_assets.json", "manifests/approved-release-local.json"]
    subprocess.run(["git", "add", "--", *paths], cwd=ROOT, check=True)
    if git("diff", "--cached", "--name-only"):
        subprocess.run(["git", "commit", "-m", "Update owner Bubbles and Bactro Gang reference sheets"], cwd=ROOT, check=True)
    subprocess.run(["git", "push", "origin", "HEAD:main"], cwd=ROOT, check=True)
    subprocess.run(["git", "fetch", "origin", "main"], cwd=ROOT, check=True)
    if git("rev-parse", "HEAD") != git("rev-parse", "origin/main"):
        raise RuntimeError("Remote HEAD differs")
    print("SUCCESS: both current references and manifests verified at", git("rev-parse", "HEAD"))

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print("BLOCKED:", e)
        raise SystemExit(1)
