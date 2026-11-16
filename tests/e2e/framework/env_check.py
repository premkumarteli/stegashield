"""
StegaShield E2E Environment Verification & Health Check.
Checks Python packages, backend availability, and database connectivity.
"""

from __future__ import annotations

import importlib
import socket
import sys
from typing import Any, Dict, List
from urllib.parse import urlparse


def check_python_packages() -> Dict[str, bool]:
    """Verifies that all required StegaShield runtime & testing libraries are installed."""
    required = [
        "pytest",
        "PIL",
        "cryptography",
        "numpy",
        "scipy",
        "fastapi",
        "httpx",
        "sqlalchemy",
        "pymysql",
    ]
    results = {}
    for pkg in required:
        try:
            importlib.import_module(pkg)
            results[pkg] = True
        except ImportError:
            results[pkg] = False
    return results


def check_mysql_connection(host: str = "localhost", port: int = 3306, timeout: float = 1.0) -> bool:
    """Checks if the local MySQL service is accepting connections."""
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except (socket.timeout, ConnectionRefusedError, OSError):
        return False


def check_backend_alive(url: str = "http://127.0.0.1:8000", timeout: float = 1.0) -> bool:
    """Checks if the FastAPI backend is running and reachable."""
    try:
        parsed = urlparse(url)
        host = parsed.hostname or "127.0.0.1"
        port = parsed.port or (443 if parsed.scheme == "https" else 8000)
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except (socket.timeout, ConnectionRefusedError, OSError):
        return False


def run_full_env_check(backend_url: str = "http://127.0.0.1:8000") -> Dict[str, Any]:
    """Runs a complete environment check and returns a comprehensive status report."""
    packages = check_python_packages()
    mysql_ok = check_mysql_connection()
    backend_ok = check_backend_alive(backend_url)

    issues: List[str] = []
    missing = [pkg for pkg, ok in packages.items() if not ok]
    if missing:
        issues.append(f"Missing required Python packages: {', '.join(missing)}")

    status = "ok"
    if issues:
        status = "error"
    elif not backend_ok or not mysql_ok:
        status = "degraded"

    return {
        "status": status,
        "python_version": sys.version.split()[0],
        "packages": packages,
        "database_listening": mysql_ok,
        "backend_listening": backend_ok,
        "issues": issues,
    }


if __name__ == "__main__":
    report = run_full_env_check()
    print("Environment Check Report:")
    for k, v in report.items():
        print(f"  {k}: {v}")
