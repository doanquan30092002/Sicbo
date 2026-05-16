"""Health-check script cho production deployment.

Kiểm tra:
- Backend /health endpoint
- Frontend root page
- CORS từ frontend → backend

Usage:
    python -m scripts.health_check https://sicbo-prod.railway.app https://sicbo.vercel.app
"""
import sys

import httpx


def check_backend(url: str) -> bool:
    print(f"[backend] GET {url}/health ...", end=" ")
    try:
        r = httpx.get(f"{url}/health", timeout=10)
        if r.status_code == 200 and r.json().get("status") == "ok":
            print(f"OK (env={r.json().get('env')})")
            return True
        print(f"FAIL (status={r.status_code}, body={r.text[:100]})")
        return False
    except Exception as e:
        print(f"ERROR: {e}")
        return False


def check_frontend(url: str) -> bool:
    print(f"[frontend] GET {url} ...", end=" ")
    try:
        r = httpx.get(url, timeout=15, follow_redirects=True)
        if r.status_code == 200 and "<html" in r.text.lower():
            print("OK")
            return True
        print(f"FAIL (status={r.status_code})")
        return False
    except Exception as e:
        print(f"ERROR: {e}")
        return False


def check_cors(backend: str, frontend: str) -> bool:
    print(f"[cors] OPTIONS {backend}/api/auth/login from {frontend} ...", end=" ")
    try:
        r = httpx.options(
            f"{backend}/api/auth/login",
            headers={
                "Origin": frontend,
                "Access-Control-Request-Method": "POST",
                "Access-Control-Request-Headers": "content-type",
            },
            timeout=10,
        )
        allowed = r.headers.get("access-control-allow-origin", "")
        if allowed in (frontend, "*"):
            print(f"OK (Allow-Origin: {allowed})")
            return True
        print(f"FAIL (Allow-Origin: '{allowed}', expected '{frontend}')")
        return False
    except Exception as e:
        print(f"ERROR: {e}")
        return False


def check_docs(url: str) -> bool:
    print(f"[docs] GET {url}/docs ...", end=" ")
    try:
        r = httpx.get(f"{url}/docs", timeout=10)
        if r.status_code == 200:
            print("OK")
            return True
        print(f"FAIL (status={r.status_code})")
        return False
    except Exception as e:
        print(f"ERROR: {e}")
        return False


def main() -> int:
    if len(sys.argv) < 2:
        print("Usage: python -m scripts.health_check <backend_url> [frontend_url]")
        print("Example: python -m scripts.health_check https://sicbo.up.railway.app https://sicbo.vercel.app")
        return 1

    backend = sys.argv[1].rstrip("/")
    frontend = sys.argv[2].rstrip("/") if len(sys.argv) >= 3 else None

    results = [check_backend(backend), check_docs(backend)]
    if frontend:
        results.append(check_frontend(frontend))
        results.append(check_cors(backend, frontend))

    passed = sum(results)
    total = len(results)
    print(f"\n=== {passed}/{total} checks passed ===")
    return 0 if passed == total else 1


if __name__ == "__main__":
    sys.exit(main())
