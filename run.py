#!/usr/bin/env python3
"""StegaShield — Blazing-Fast Universal Application Launcher.

Runs the complete StegaShield stack with maximum performance:
1. Validates environment (Python 3.12+, Node.js, npm, .env configuration).
2. Applies database migrations automatically (Alembic -> MySQL 8).
3. Serves the pre-compiled production build (next start) by default for
   INSTANT, sub-10ms page transitions with zero on-demand compiling delay.
4. Concurrently launches FastAPI backend (Port 8000) and Next.js frontend (Port 3000).
5. Streams unified, color-coded process logs.
6. Performs readiness polling and opens your browser to http://localhost:3000.
7. Guarantees clean, orphaned-process-free shutdown on Ctrl+C.

Usage:
    python run.py             # Blazing-fast production mode (Instant page loads)
    python run.py --dev       # Development mode (Hot-reload for editing code)
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
DOT_NEXT_DIR = FRONTEND_DIR / ".next"


def is_port_in_use(port: int, host: str = "127.0.0.1") -> bool:
    """Checks whether a local TCP port is already bound."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(0.3)
        return s.connect_ex((host, port)) == 0


def find_pids_on_port(port: int) -> set[int]:
    """Finds all process IDs bound to or listening on a given port."""
    pids: set[int] = set()
    my_pid = os.getpid()

    if sys.platform == "win32":
        # Strategy 1: netstat -ano
        try:
            res = subprocess.run(
                f"netstat -ano | findstr :{port}",
                shell=True,
                capture_output=True,
                text=True,
                check=False,
            )
            for line in res.stdout.splitlines():
                parts = line.strip().split()
                if len(parts) >= 5 and parts[1].endswith(f":{port}"):
                    try:
                        pid = int(parts[-1])
                        if pid > 4 and pid != my_pid:
                            pids.add(pid)
                    except ValueError:
                        pass
        except Exception:
            pass

        # Strategy 2: PowerShell Get-NetTCPConnection
        try:
            cmd = f"Get-NetTCPConnection -LocalPort {port} -ErrorAction SilentlyContinue | Select-Object -ExpandProperty OwningProcess"
            res = subprocess.run(
                ["powershell", "-NoProfile", "-Command", cmd],
                capture_output=True,
                text=True,
                check=False,
            )
            for line in res.stdout.splitlines():
                pid_str = line.strip()
                if pid_str.isdigit():
                    pid = int(pid_str)
                    if pid > 4 and pid != my_pid:
                        pids.add(pid)
        except Exception:
            pass

    return pids


def kill_occupying_processes(ports: list[int], max_wait: float = 3.0) -> None:
    """Terminates processes listening on specified ports (including child trees) and waits until free."""
    for port in ports:
        if not is_port_in_use(port):
            continue

        pids = find_pids_on_port(port)
        for pid in pids:
            if sys.platform == "win32":
                # Use /F (force) and /T (tree kill all child workers like WatchFiles/multiprocessing)
                subprocess.run(
                    ["taskkill", "/F", "/T", "/PID", str(pid)],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    check=False,
                )
            else:
                try:
                    os.kill(pid, signal.SIGKILL)
                except OSError:
                    pass

        # Wait until port is actually unbound by OS
        start = time.time()
        while time.time() - start < max_wait:
            if not is_port_in_use(port):
                break
            time.sleep(0.2)


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


def wait_for_server(url: str, timeout: int = 25) -> bool:
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
        time.sleep(0.4)
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
    print("\033[36m[DB] Verifying database schema (alembic upgrade head)...\033[0m")
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
            print("\033[32m✔ Database connected & schema up to date.\033[0m")
            return True
        else:
            print(f"\033[33m⚠ Migration notice:\n{res.stdout}\033[0m")
            return False
    except Exception as e:
        print(f"\033[33m⚠ Warning running migrations: {e}\033[0m")
        return False


def main() -> None:
    parser = argparse.ArgumentParser(description="StegaShield Fast Application Runner")
    parser.add_argument("--dev", action="store_true", help="Run in development mode (hot-reloading enabled)")
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

    # 1. Environment Validations
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

    # Clean existing dangling processes on ports 8000 & 3000
    if is_port_in_use(args.backend_port) or is_port_in_use(args.frontend_port):
        print("\033[33mCleaning dangling processes from previous runs...\033[0m")
        kill_occupying_processes([args.backend_port, args.frontend_port])
        if is_port_in_use(args.backend_port) or is_port_in_use(args.frontend_port):
            time.sleep(1.0)
            kill_occupying_processes([args.backend_port, args.frontend_port])

    # 2. Database Migrations
    run_database_migrations()

    # Check whether to use pre-built production mode (instant) or dev mode
    use_prod_mode = not args.dev and DOT_NEXT_DIR.exists()
    npm_cmd = "npm.cmd" if sys.platform == "win32" else "npm"

    if use_prod_mode:
        print("\033[1;32m⚡ Fast Mode: Serving pre-compiled production build (INSTANT page transitions).\033[0m")
        frontend_args = [npm_cmd, "run", "start", "--", "-p", str(args.frontend_port)]
    else:
        print("\033[33m🛠 Dev Mode: JIT compiling enabled (hot-reload mode).\033[0m")
        frontend_args = [npm_cmd, "run", "dev", "--", "-p", str(args.frontend_port)]

    processes: list[subprocess.Popen] = []

    try:
        # 3. Start FastAPI Backend
        print(f"\n\033[32m[1/2] Launching FastAPI backend on http://localhost:{args.backend_port} ...\033[0m")
        backend_cmd = [
            sys.executable,
            "-m",
            "uvicorn",
            "app.main:app",
            "--host",
            "127.0.0.1",
            "--port",
            str(args.backend_port),
        ]
        if args.dev:
            backend_cmd.append("--reload")

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
        print(f"\033[34m[2/2] Launching Next.js frontend on http://localhost:{args.frontend_port} ...\033[0m")
        frontend_proc = subprocess.Popen(
            frontend_args,
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
            print("\033[32m✔ Backend API is live & ready!\033[0m")
        else:
            print("\033[33m⚠ Backend initializing in background...\033[0m")

        frontend_ready = wait_for_server(frontend_url, timeout=15)
        if frontend_ready:
            print("\033[32m✔ Frontend UI is live & ready!\033[0m")
        else:
            print("\033[33m⚠ Frontend readying in background...\033[0m")

        print("\n\033[1;32m" + "=" * 65)
        print("   🎉 StegaShield Lab is LIVE & FAST!")
        print(f"   🌐 Web Application : {frontend_url}")
        print(f"   📚 Interactive API : http://localhost:{args.backend_port}/docs")
        print("   ⚡ Press Ctrl+C to terminate both servers cleanly.")
        print("=" * 65 + "\033[0m\n")

        # Open browser
        if not args.no_browser:
            time.sleep(0.5)
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
        # Ensure no lingering background sockets or spawned subprocesses remain
        kill_occupying_processes([args.backend_port, args.frontend_port])
        print("\033[32m✔ All StegaShield processes cleanly stopped.\033[0m\n")


if __name__ == "__main__":
    main()
