"""Launch the isolated sample API and the frontend together on Windows/macOS/Linux."""
import importlib.util
import os
from pathlib import Path
import shutil
import socket
import subprocess
import sys
import time
import urllib.request
import webbrowser

ROOT = Path(__file__).resolve().parent

def main():
    missing = [name for name in ("fastapi", "uvicorn", "pandas", "sqlalchemy", "dotenv", "openpyxl") if importlib.util.find_spec(name) is None]
    if missing:
        raise SystemExit("Install dependencies first: python -m pip install -r backend/requirements.txt")
    node = shutil.which("node")
    vite = ROOT / "frontend/node_modules/vite/bin/vite.js"
    if not node or not vite.is_file():
        raise SystemExit("Install Node.js, then run 'npm ci' inside the frontend folder.")
    for port in (8000, 5173):
        with socket.socket() as probe:
            try:
                probe.bind(("127.0.0.1", port))
            except OSError:
                raise SystemExit(f"Port {port} is already in use. Close the earlier RiskVision server before starting the demo.")
    processes = []
    try:
        env = dict(os.environ)
        env["VITE_API_BASE_URL"] = "http://127.0.0.1:8000"
        processes.append(subprocess.Popen([sys.executable, str(ROOT / "backend/demo.py")], cwd=ROOT))
        processes.append(subprocess.Popen([node, str(vite), "--host", "127.0.0.1", "--port", "5173", "--strictPort"], cwd=ROOT / "frontend", env=env))
        opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
        for _ in range(120):
            if any(p.poll() is not None for p in processes):
                raise RuntimeError("A service stopped during startup. Check the error above.")
            try:
                with opener.open("http://127.0.0.1:8000/health", timeout=1) as response:
                    response.read()
                with opener.open("http://127.0.0.1:5173", timeout=1) as response:
                    response.read()
                break
            except OSError:
                time.sleep(0.5)
        else:
            raise RuntimeError("The demo did not become ready within 60 seconds.")
        print("\nRiskVision is ready at http://127.0.0.1:5173")
        print("Synthetic portfolio. Your PostgreSQL data is not changed. Press Ctrl+C to stop.\n")
        webbrowser.open("http://127.0.0.1:5173")
        while all(p.poll() is None for p in processes):
            time.sleep(0.5)
    except KeyboardInterrupt:
        print("\nStopping RiskVision.")
    finally:
        for process in processes:
            if process.poll() is None:
                process.terminate()
        for process in processes:
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()

if __name__ == "__main__":
    main()
