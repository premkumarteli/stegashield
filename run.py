#!/usr/bin/env python3
"""StegaShield Single-Command Application Launcher.

Starts both the FastAPI backend and Next.js frontend concurrently,
monitors their health, and automatically launches the browser.
Handles clean shutdown on Ctrl+C.
"""

import os
import signal
import subprocess
import sys
import time
import urllib.request
import webbrowser
from pathlib import Path
from threading import Thread

ROOT_DIR = Path(__file__).resolve().parent
BACKEND_DIR = ROOT_DIR / "backend"
FRONTEND_DIR = ROOT_DIR / "frontend"

BACKEND_URL = "http://127.0.0.1:8000/api/v1/health"
FRONTEND_URL = "http://localhost:3000"


def stream_output(process, prefix, color_code):
    """Streams child process stdout/stderr with colored prefix."""
    reset_code = "\033[0m"
    try:
        for line in iter(process.stdout.readline, ""):
            if not line:
                break
            sys.stdout.write(f"{color_code}[{prefix}]{reset_code} {line}")
            sys.stdout.flush()
    except (ValueError, OSError):
        pass


def wait_for_server(url, timeout=30):
    """Waits for HTTP server endpoint to respond with 200 OK."""
    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "StegaShield-Launcher"})
            with urllib.request.urlopen(req, timeout=2) as response:
                if response.status in (200, 304, 307, 308):
                    return True
        except Exception:
            pass
        time.sleep(0.5)
    return False


def main():
    # Windows ANSI escape sequence enablement
    if sys.platform == "win32":
        os.system("")

    print("\033[1;36m" + "=" * 60)
    print("   🛡️  StegaShield — Steganography & Steganalysis Lab")
    print("   Starting Full Application Suite...")
    print("=" * 60 + "\033[0m\n")

    # Verify directories
    if not BACKEND_DIR.exists():
        print(f"\033[31mError: Backend directory not found at {BACKEND_DIR}\033[0m")
        sys.exit(1)
    if not FRONTEND_DIR.exists():
        print(f"\033[31mError: Frontend directory not found at {FRONTEND_DIR}\033[0m")
        sys.exit(1)

    processes = []

    try:
        # 1. Start Backend (FastAPI on Port 8000)
        print("\033[32m[1/2] Launching FastAPI Backend on http://localhost:8000 ...\033[0m")
        backend_cmd = [sys.executable, "-m", "uvicorn", "app.main:app", "--port", "8000", "--host", "127.0.0.1"]
        backend_proc = subprocess.Popen(
            backend_cmd,
            cwd=str(BACKEND_DIR),
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
        )
        processes.append(backend_proc)
        Thread(target=stream_output, args=(backend_proc, "BACKEND", "\033[32m"), daemon=True).start()

        # 2. Start Frontend (Next.js on Port 3000)
        print("\033[34m[2/2] Launching Next.js Frontend on http://localhost:3000 ...\033[0m")
        npm_cmd = "npm.cmd" if sys.platform == "win32" else "npm"
        frontend_proc = subprocess.Popen(
            [npm_cmd, "run", "dev"],
            cwd=str(FRONTEND_DIR),
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
        )
        processes.append(frontend_proc)
        Thread(target=stream_output, args=(frontend_proc, "FRONTEND", "\033[34m"), daemon=True).start()

        # 3. Wait for readiness
        print("\n\033[33mWaiting for servers to initialize...\033[0m")
        backend_ready = wait_for_server(BACKEND_URL, timeout=15)
        if backend_ready:
            print("\033[32m✔ Backend is healthy (FastAPI REST API ready)\033[0m")
        else:
            print("\033[33m⚠ Backend startup taking longer than expected, continuing...\033[0m")

        frontend_ready = wait_for_server(FRONTEND_URL, timeout=25)
        if frontend_ready:
            print("\033[32m✔ Frontend is healthy (Next.js Liquid Glass UI ready)\033[0m")
        else:
            print("\033[33m⚠ Frontend compiling, will open browser shortly...\033[0m")

        print("\n\033[1;32m" + "-" * 60)
        print("   🚀 StegaShield is LIVE!")
        print("   🌐 Web App:    http://localhost:3000")
        print("   📚 API Docs:   http://localhost:8000/docs")
        print("   Press Ctrl+C at any time to shut down both servers.")
        print("-" * 60 + "\033[0m\n")

        # Open in default browser
        webbrowser.open("http://localhost:3000")

        # Keep parent alive while children run
        while True:
            for p in processes:
                if p.poll() is not None:
                    print(f"\n\033[31mProcess exited unexpectedly with code {p.returncode}\033[0m")
                    return
            time.sleep(0.5)

    except KeyboardInterrupt:
        print("\n\n\033[33mShutting down StegaShield servers gracefully...\033[0m")
    finally:
        for p in processes:
            if p.poll() is None:
                p.terminate()
                try:
                    p.wait(timeout=3)
                except subprocess.TimeoutExpired:
                    p.kill()
        print("\033[32mAll StegaShield processes stopped. Good luck with your demo!\033[0m\n")


if __name__ == "__main__":
    main()
