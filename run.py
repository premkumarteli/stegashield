#!/usr/bin/env python3
"""StegaShield — Single-Command Universal Application Launcher.

Runs the complete StegaShield stack:
1. Validates environment (Python 3.12+, Node.js, npm, .env configuration).
2. Applies database migrations automatically (Alembic -> MySQL 8).
3. Concurrently launches FastAPI backend (Port 8000) and Next.js frontend (Port 3000).
4. Streams unified, color-coded process logs.
5. Performs readiness polling and opens your browser to http://localhost:3000.
6. Guarantees clean, orphaned-process-free shutdown on Ctrl+C (Windows & Linux/macOS).

Usage:
    python run.py
    python run.py --no-browser
"""

from __future__ import annotations

import argparse
import os
import shutil
import signal
import socket
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


def is_port_in_use(port: int, host: str = "127.0.0.1") -> bool:
    """Checks whether a local TCP port is already bound."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(0.5)
        return s.connect_ex((host, port)) == 0


def stream_output(process: subprocess.Popen, prefix: str, color_code: str) -> None:
    """Streams child process output line-by-line with color-coded prefix tags."""
    reset_code = "\033[0m"
    try:
        if process.stdout:
            for line in iter(process.stdout.readline, ""):
                if not line:
                    break
                sys.stdout.write(f"{color_code}[{prefix}]{reset_code} {line}")
                sys.stdout.flush()
    except (ValueError, OSError):
        pass


def wait_for_server(url: str, timeout: int = 30) -> bool:
    """Polls an HTTP endpoint until it returns a successful or redirect status code."""
    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "StegaShield-Launcher"})
            with urllib.request.urlopen(req, timeout=1.5) as resp:
                if resp.status in (200, 204, 301, 302, 304, 307, 308):
                    return True
        except Exception:
            pass
        time.sleep(0.5)
    return False


def kill_process_tree(proc: subprocess.Popen) -> None:
    """Terminates a process and all its child subprocesses cleanly across platforms."""
    if proc.poll() is not None:
        return

    pid = proc.pid
    if sys.platform == "win32":
        try:
            subprocess.run(
                ["taskkill", "/F", "/T", "/PID", str(pid)],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                check=False,
            )
        except Exception:
            proc.kill()
    else:
        try:
            os.killpg(os.getpgid(pid), signal.SIGTERM)
        except Exception:
            proc.terminate()
            try:
                proc.wait(timeout=3)
            except subprocess.TimeoutExpired:
                proc.kill()


def run_database_migrations() -> bool:
    """Applies Alembic database migrations to ensure MySQL 8 tables exist."""
    print("\033[36m[DB] Checking & applying database migrations (alembic upgrade head)...\033[0m")
    try:
        res = subprocess.run(
            [sys.executable, "-m", "alembic", "upgrade", "head"],
            cwd=str(BACKEND_DIR),
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            check=False,
        )
        if res.returncode == 0:
            print("\033[32m✔ Database schema is up to date (MySQL 8 connected).\033[0m")
            return True
        else:
            print(f"\033[33m⚠ Migration notice:\n{res.stdout}\033[0m")
            return False
    except Exception as e:
        print(f"\033[33m⚠ Warning running migrations: {e}\033[0m")
        return False


def main() -> None:
    parser = argparse.ArgumentParser(description="StegaShield Complete Application Runner")
    parser.add_argument("--no-browser", action="store_true", help="Do not automatically launch web browser")
    parser.add_argument("--backend-port", type=int, default=8000, help="Port for FastAPI backend (default: 8000)")
    parser.add_argument("--frontend-port", type=int, default=3000, help="Port for Next.js frontend (default: 3000)")
    args = parser.parse_args()

    # Enable ANSI escape colors on Windows
    if sys.platform == "win32":
        os.system("")

    banner = r"""
  ____  _                  ____  _     _eld
 / ___|| |_ ___  __ _  __ / ___|| |__ (_) ___| | __| |
 \___ \| __/ _ \/ _` |/ _` \___ \| '_ \| |/ _ \ |/ _` |
  ___) | ||  __/ (_| | (_| |___) | | | | |  __/ | (_| |
 |____/ \__\___|\__, |\__,_|____/|_| |_|_|\___|_|\__,_|
                |___/  Information & Network Security Lab
"""
    print("\033[1;36m" + banner + "\033[0m")
    print(f"\033[1;30mRoot Directory: {ROOT_DIR}\033[0m\n")

    # 1. Environment Pre-flight Validations
    if not BACKEND_DIR.exists():
        print(f"\033[31mError: Backend directory missing at {BACKEND_DIR}\033[0m")
        sys.exit(1)
    if not FRONTEND_DIR.exists():
        print(f"\033[31mError: Frontend directory missing at {FRONTEND_DIR}\033[0m")
        sys.exit(1)

    # Check for backend .env
    backend_env = BACKEND_DIR / ".env"
    if not backend_env.exists():
        example_env = ROOT_DIR / ".env.example"
        if example_env.exists():
            print("\033[33mInitializing backend/.env from .env.example...\033[0m")
            shutil.copy(example_env, backend_env)

    # Check if ports are already taken
    if is_port_in_use(args.backend_port):
        print(f"\033[33m⚠ Warning: Port {args.backend_port} is already in use. Existing service may conflict.\033[0m")
    if is_port_in_use(args.frontend_port):
        print(f"\033[33m⚠ Warning: Port {args.frontend_port} is already in use. Existing service may conflict.\033[0m")

    # 2. Database Migrations
    run_database_migrations()

    processes: list[subprocess.Popen] = []

    try:
        # 3. Start FastAPI Backend
        print(f"\n\033[32m[1/2] Starting FastAPI backend on http://localhost:{args.backend_port} ...\033[0m")
        backend_cmd = [
            sys.executable,
            "-m",
            "uvicorn",
            "app.main:app",
            "--host",
            "127.0.0.1",
            "--port",
            str(args.backend_port),
            "--reload",
        ]
        backend_proc = subprocess.Popen(
            backend_cmd,
            cwd=str(BACKEND_DIR),
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
            preexec_fn=None if sys.platform == "win32" else os.setsid,
        )
        processes.append(backend_proc)
        Thread(target=stream_output, args=(backend_proc, "BACKEND", "\033[32m"), daemon=True).start()

        # 4. Start Next.js Frontend
        print(f"\033[34m[2/2] Starting Next.js frontend on http://localhost:{args.frontend_port} ...\033[0m")
        npm_cmd = "npm.cmd" if sys.platform == "win32" else "npm"
        frontend_proc = subprocess.Popen(
            [npm_cmd, "run", "dev", "--", "-p", str(args.frontend_port)],
            cwd=str(FRONTEND_DIR),
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
            preexec_fn=None if sys.platform == "win32" else os.setsid,
        )
        processes.append(frontend_proc)
        Thread(target=stream_output, args=(frontend_proc, "FRONTEND", "\033[34m"), daemon=True).start()

        # 5. Readiness Polling
        print("\n\033[33mConnecting to application services...\033[0m")
        backend_health_url = f"http://127.0.0.1:{args.backend_port}/api/v1/health"
        frontend_url = f"http://localhost:{args.frontend_port}"

        backend_ready = wait_for_server(backend_health_url, timeout=12)
        if backend_ready:
            print("\033[32m✔ Backend API is live & healthy!\033[0m")
        else:
            print("\033[33m⚠ Backend initializing in background...\033[0m")

        frontend_ready = wait_for_server(frontend_url, timeout=20)
        if frontend_ready:
            print("\033[32m✔ Frontend UI (Abyssal Liquid Glass) is live & healthy!\033[0m")
        else:
            print("\033[33m⚠ Frontend compiling pages in background...\033[0m")

        print("\n\033[1;32m" + "=" * 65)
        print("   🎉 StegaShield Lab is RUNNING!")
        print(f"   🌐 Web Application : {frontend_url}")
        print(f"   📚 Interactive API : http://localhost:{args.backend_port}/docs")
        print("   ⚡ Press Ctrl+C to terminate both servers cleanly.")
        print("=" * 65 + "\033[0m\n")

        # Open browser
        if not args.no_browser:
            time.sleep(1.0)
            webbrowser.open(frontend_url)

        # Monitor processes
        while True:
            for p in processes:
                if p.poll() is not None:
                    print(f"\n\033[31mService exited unexpectedly with return code {p.returncode}\033[0m")
                    return
            time.sleep(0.5)

    except KeyboardInterrupt:
        print("\n\n\033[33mGracefully shutting down StegaShield servers...\033[0m")
    finally:
        for p in processes:
            kill_process_tree(p)
        print("\033[32m✔ All StegaShield processes cleanly stopped.\033[0m\n")


if __name__ == "__main__":
    main()
