"""Apply the accompanying verified source update to an installed RiskVision demo.

Preserves installed packages, environment settings, and demo data. Backs up changed
source files and the local demo database. Stops on unexpected local source changes.
No downloads, external publication, or credential access.
"""
import argparse
from datetime import datetime
import hashlib
import json
import os
from pathlib import Path
import shutil
import socket
import sys


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest() if path.is_file() else None


def find_project(explicit):
    if explicit:
        candidates = [Path(explicit).expanduser().resolve()]
    else:
        downloads = Path.home() / "Downloads"
        candidates = [Path.cwd(), Path(__file__).resolve().parent.parent]
        for folder in downloads.glob("RiskVision*"):
            if folder.is_dir():
                candidates.append(folder)
                candidates.extend(p for p in folder.glob("RiskVision*") if p.is_dir())
    found = []
    for candidate in candidates:
        if (candidate / "start_demo.py").is_file() and (candidate / "frontend/package.json").is_file():
            if candidate.resolve() not in found:
                found.append(candidate.resolve())
    if len(found) != 1:
        raise RuntimeError("Could not identify one installed demo folder. Run: python apply_update.py --target \"FULL PATH TO YOUR RISKVISION FOLDER\"")
    return found[0]


def apply(target, bundle, check_only=False):
    manifest = json.loads((bundle / "manifest.json").read_text(encoding="utf-8"))
    changed = []
    for record in manifest["files"]:
        relative = Path(record["path"])
        if relative.is_absolute() or ".." in relative.parts:
            raise RuntimeError("Invalid path in update bundle")
        source, destination = bundle / "payload" / relative, target / relative
        if digest(source) != record["after"]:
            raise RuntimeError("The update bundle is incomplete or damaged: " + str(relative))
        existing = digest(destination)
        if existing == record["after"]:
            continue
        if existing != record["before"]:
            raise RuntimeError("Local changes found in " + str(relative) + ". No files were changed. Keep this file and ask for help merging the update.")
        if destination.is_symlink() or not destination.resolve().is_relative_to(target.resolve()):
            raise RuntimeError("An update path points outside the project")
        changed.append((relative, source, destination))
    print("RiskVision folder:", target)
    if check_only:
        print(f"Update verified: {len(changed)} files ready. Nothing changed.")
        return
    if not changed:
        print("This update is already installed.")
        return
    for port in (8000, 5173):
        with socket.socket() as probe:
            probe.settimeout(.5)
            if probe.connect_ex(("127.0.0.1", port)) == 0:
                raise RuntimeError(f"A service is still running on port {port}. Stop RiskVision with Ctrl+C, then run APPLY_UPDATE.bat again.")
    backup = target / ("riskvision-update-backup-" + datetime.now().strftime("%Y%m%d-%H%M%S"))
    backup.mkdir(exist_ok=False)
    for relative, _, destination in changed:
        if destination.exists():
            copy = backup / relative
            copy.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(destination, copy)
    database = target / "backend/.demo/riskvision.sqlite3"
    if database.is_file():
        (backup / "backend/.demo").mkdir(parents=True, exist_ok=True)
        shutil.copy2(database, backup / "backend/.demo/riskvision.sqlite3")
    (backup / "update-record.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    applied = []
    try:
        for relative, source, destination in changed:
            destination.parent.mkdir(parents=True, exist_ok=True)
            temporary = destination.with_name(destination.name + ".riskvision-update-tmp")
            shutil.copyfile(source, temporary)
            os.replace(temporary, destination)
            applied.append((relative, destination))
    except Exception:
        for relative, destination in reversed(applied):
            original = backup / relative
            if original.exists():
                shutil.copy2(original, destination)
            else:
                destination.unlink(missing_ok=True)
        raise
    print(f"Installed {len(changed)} updated files.")
    print("Previous files saved in:", backup.name)
    print("Your installed packages and database were preserved.")
    print("Double-click START_RISKVISION.bat in your original project folder to start.")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--target", help="Existing project folder containing start_demo.py")
    parser.add_argument("--check", action="store_true", help="Validate without changing files")
    args = parser.parse_args()
    try:
        apply(find_project(args.target), Path(__file__).resolve().parent, args.check)
    except Exception as error:
        print("\nUpdate stopped:", error)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
