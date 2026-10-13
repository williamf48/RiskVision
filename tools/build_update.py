"""Build a source-only Windows update using the original demo's file hashes."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
from tempfile import TemporaryDirectory
import zipfile

ROOT = Path(__file__).resolve().parents[1]


def git(*args):
    return subprocess.check_output(["git", *args], cwd=ROOT, stderr=subprocess.DEVNULL)


def build(output, base=None):
    if base:
        paths = git("diff", "--name-only", "--diff-filter=ACMRT", base, "HEAD").decode().splitlines()
        baseline = {}
        for path in paths:
            try:
                baseline[path] = hashlib.sha256(git("show", f"{base}:{path}")).hexdigest()
            except subprocess.CalledProcessError:
                baseline[path] = None
    else:
        baseline = json.loads((ROOT / "tools/demo_v1_hashes.json").read_text(encoding="utf-8"))
        paths = [path for path in git("ls-tree", "-r", "--name-only", "HEAD").decode().splitlines()
                 if hashlib.sha256((ROOT / path).read_bytes()).hexdigest() != baseline.get(path)]
    manifest = {"version": "professional-v2", "base": base or "original-demo-v1", "files": []}
    with TemporaryDirectory() as directory:
        bundle = Path(directory) / "RiskVision-Professional-Update"
        (bundle / "payload").mkdir(parents=True)
        for path in paths:
            current = (ROOT / path).read_bytes()
            before = baseline.get(path)
            destination = bundle / "payload" / path
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_bytes(current)
            manifest["files"].append({"path": path, "before": before, "after": hashlib.sha256(current).hexdigest()})
        (bundle / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
        (bundle / "apply_update.py").write_bytes((ROOT / "tools/apply_update.py").read_bytes())
        (bundle / "APPLY_UPDATE.bat").write_bytes(b'@echo off\r\nsetlocal\r\ncd /d "%~dp0"\r\npython "%~dp0apply_update.py" %*\r\necho.\r\npause\r\n')
        (bundle / "READ_ME_FIRST.txt").write_text(
            "RISKVISION PROFESSIONAL UPDATE\n\n"
            "1. Stop the current RiskVision terminal with Ctrl+C.\n"
            "2. Extract this entire ZIP. Keep apply_update.py, manifest.json and payload together.\n"
            "3. Double-click APPLY_UPDATE.bat.\n"
            "4. In your ORIGINAL RiskVision folder, double-click START_RISKVISION.bat.\n\n"
            "The updater finds an installed RiskVision project in Downloads automatically.\n"
            "It saves a backup and reuses installed packages. It does not publish anything or contact external services.\n"
            "If your project is elsewhere, open PowerShell in this update folder and run:\n"
            'python apply_update.py --target "C:\\full\\path\\to\\your\\RiskVision-folder"\n\n'
            "Unexpected local source changes stop the update instead of overwriting them.\n"
            "The app remains a local synthetic-data demonstration with transparent credit-monitoring rules.\n",
            encoding="utf-8")
        with zipfile.ZipFile(output, "w", zipfile.ZIP_DEFLATED) as archive:
            for file in sorted(bundle.rglob("*")):
                if file.is_file():
                    archive.write(file, file.relative_to(bundle.parent).as_posix())
    print(f"Created {output.name}: {len(paths)} updated files, {output.stat().st_size:,} bytes")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=ROOT.parent / "RiskVision-Professional-Update.zip")
    parser.add_argument("--base", help="Optional Git baseline; defaults to the original demo's recorded file hashes")
    args = parser.parse_args()
    build(args.output, args.base)
