#!/usr/bin/env python3
"""
Boliye -- Local launcher
=======================
Single command to validate the environment, check services, and start the
FastAPI backend with hot-reload.

    python run_local.py          # default: port 8000, reload on
    python run_local.py --port 8080 --no-reload

The script will:
  1. Verify Python version
  2. Check that all required packages are installed
  3. Load and validate .env configuration
  4. Probe external services (Qwen TTS, Ollama) to surface issues early
  5. Start uvicorn
"""
from __future__ import annotations

import argparse
import importlib
import os
import sys
import textwrap
from pathlib import Path

# ── Constants ────────────────────────────────────────────────────────
BACKEND_DIR = Path(__file__).resolve().parent
ROOT_DIR = BACKEND_DIR.parent
ENV_FILE = ROOT_DIR / ".env"
MIN_PYTHON = (3, 10)

# ANSI helpers -- detect if terminal supports them
def _supports_ansi() -> bool:
    if os.getenv("NO_COLOR"):
        return False
    if sys.platform == "win32":
        # Windows Terminal and modern PS support ANSI, but enable VT processing
        try:
            import ctypes
            kernel32 = ctypes.windll.kernel32  # type: ignore[attr-defined]
            # STD_OUTPUT_HANDLE = -11, ENABLE_VIRTUAL_TERMINAL_PROCESSING = 0x4
            handle = kernel32.GetStdHandle(-11)
            mode = ctypes.c_ulong()
            kernel32.GetConsoleMode(handle, ctypes.byref(mode))
            kernel32.SetConsoleMode(handle, mode.value | 0x4)
            return True
        except Exception:
            return False
    return hasattr(sys.stdout, "isatty") and sys.stdout.isatty()


_USE_ANSI = _supports_ansi()
_BOLD  = "\033[1m"  if _USE_ANSI else ""
_GREEN = "\033[92m" if _USE_ANSI else ""
_YELLOW= "\033[93m" if _USE_ANSI else ""
_RED   = "\033[91m" if _USE_ANSI else ""
_CYAN  = "\033[96m" if _USE_ANSI else ""
_DIM   = "\033[2m"  if _USE_ANSI else ""
_RESET = "\033[0m"  if _USE_ANSI else ""


def _ok(msg: str) -> None:
    print(f"  {_GREEN}[OK]{_RESET} {msg}")


def _warn(msg: str) -> None:
    print(f"  {_YELLOW}[!!]{_RESET} {msg}")


def _fail(msg: str) -> None:
    print(f"  {_RED}[FAIL]{_RESET} {msg}")


def _info(msg: str) -> None:
    print(f"  {_CYAN}[..]{_RESET} {msg}")


def _header(msg: str) -> None:
    print(f"\n{_BOLD}{msg}{_RESET}")


# ── 1. Python version ───────────────────────────────────────────────
def check_python() -> bool:
    v = sys.version_info
    if (v.major, v.minor) >= MIN_PYTHON:
        _ok(f"Python {v.major}.{v.minor}.{v.micro}")
        return True
    _fail(f"Python {v.major}.{v.minor} -- need >= {MIN_PYTHON[0]}.{MIN_PYTHON[1]}")
    return False


# ── 2. Required packages ────────────────────────────────────────────
REQUIRED_PACKAGES = {
    # pip-name         -> import-name (if different)
    "fastapi":          "fastapi",
    "uvicorn":          "uvicorn",
    "python-dotenv":    "dotenv",
    "pydantic":         "pydantic",
    "sqlalchemy":       "sqlalchemy",
    "httpx":            "httpx",
    "numpy":            "numpy",
    "scipy":            "scipy",
    "google-genai":     "google.genai",
    "python-jose":      "jose",
    "passlib":          "passlib",
    "python-multipart": "multipart",
}

OPTIONAL_PACKAGES = {
    "openai-whisper":   ("whisper",           "STT (Whisper)"),
    "faster-whisper":   ("faster_whisper",    "STT (faster-whisper)"),
    "langchain-ollama": ("langchain_ollama",  "LLM fallback (Ollama)"),
    "transformers":     ("transformers",      "TTS fallback (HuggingFace VITS)"),
    "torch":            ("torch",             "TTS fallback (HuggingFace VITS)"),
}


def check_packages() -> bool:
    all_ok = True

    for pip_name, import_name in REQUIRED_PACKAGES.items():
        try:
            importlib.import_module(import_name)
            _ok(f"{pip_name}")
        except ImportError:
            _fail(f"{pip_name}  ->  pip install {pip_name}")
            all_ok = False

    for pip_name, (import_name, purpose) in OPTIONAL_PACKAGES.items():
        try:
            importlib.import_module(import_name)
            _ok(f"{pip_name} {_DIM}({purpose}){_RESET}")
        except ImportError:
            _warn(f"{pip_name} not installed {_DIM}({purpose} -- optional){_RESET}")

    return all_ok


# ── 3. Environment / .env ───────────────────────────────────────────
def load_and_check_env() -> bool:
    if ENV_FILE.exists():
        _ok(f".env found at {ENV_FILE}")
    else:
        _warn(f".env not found at {ENV_FILE} -- using defaults / system env")

    # Load it the same way config.py does
    from dotenv import load_dotenv
    load_dotenv(str(ENV_FILE))

    ok = True

    # -- LLM
    llm_provider = os.getenv("LLM_PROVIDER", "auto").lower()
    gemini_key = os.getenv("GEMINI_API_KEY", "").strip()

    if llm_provider in ("gemini", "auto"):
        if gemini_key:
            _ok(f"GEMINI_API_KEY is set ({len(gemini_key)} chars)")
        else:
            if llm_provider == "gemini":
                _fail("GEMINI_API_KEY is empty but LLM_PROVIDER=gemini")
                ok = False
            else:
                _warn("GEMINI_API_KEY is empty -- will try Ollama as fallback")
    elif llm_provider == "ollama":
        _info(f"LLM_PROVIDER=ollama -- Gemini key not needed")

    gemini_model = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")
    _info(f"LLM: provider={llm_provider}  model={gemini_model}")

    # -- TTS
    tts_provider = os.getenv("TTS_PROVIDER", "auto").lower()
    qwen_url = os.getenv("TTS_QWEN_BASE_URL", "").strip()

    if tts_provider in ("qwen", "auto") and qwen_url:
        _info(f"TTS: provider={tts_provider}  qwen_url={qwen_url}")
    elif tts_provider == "qwen" and not qwen_url:
        _fail("TTS_PROVIDER=qwen but TTS_QWEN_BASE_URL is empty")
        ok = False
    else:
        _info(f"TTS: provider={tts_provider}  (will use HuggingFace VITS if Qwen unavailable)")

    # -- STT
    whisper_model = os.getenv("WHISPER_MODEL", "base")
    stt_backend = os.getenv("STT_BACKEND", "whisper")
    _info(f"STT: backend={stt_backend}  model={whisper_model}")

    # -- Frontend origin
    frontend = os.getenv("FRONTEND_ORIGIN", "http://localhost:5173")
    _info(f"CORS origin: {frontend}")

    return ok


# ── 4. Probe external services ──────────────────────────────────────
def probe_services() -> None:
    """Best-effort connectivity checks -- warnings only, never fatal."""
    import httpx

    from dotenv import load_dotenv
    load_dotenv(str(ENV_FILE))

    # -- Qwen TTS
    qwen_url = os.getenv("TTS_QWEN_BASE_URL", "").strip().rstrip("/")
    if qwen_url:
        try:
            # Try the common health/model endpoint patterns
            for endpoint in ["/v1/models", "/health", "/"]:
                try:
                    r = httpx.get(f"{qwen_url}{endpoint}", timeout=3.0)
                    if r.status_code < 500:
                        _ok(f"Qwen3-TTS reachable at {qwen_url}")
                        break
                except httpx.ConnectError:
                    raise
                except Exception:
                    continue
            else:
                _ok(f"Qwen3-TTS reachable at {qwen_url}")
        except (httpx.ConnectError, httpx.ConnectTimeout):
            _warn(f"Qwen3-TTS not reachable at {qwen_url} -- TTS will fall back to HuggingFace VITS")
        except Exception as exc:
            _warn(f"Qwen3-TTS probe error: {exc}")
    else:
        _info("Qwen3-TTS URL not configured -- will use fallback TTS")

    # -- Ollama (only relevant if no Gemini key)
    gemini_key = os.getenv("GEMINI_API_KEY", "").strip()
    llm_provider = os.getenv("LLM_PROVIDER", "auto").lower()

    if not gemini_key or llm_provider == "ollama":
        ollama_url = os.getenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434").rstrip("/")
        try:
            r = httpx.get(f"{ollama_url}/api/version", timeout=3.0)
            if r.status_code == 200:
                _ok(f"Ollama reachable at {ollama_url}")
            else:
                _warn(f"Ollama returned status {r.status_code}")
        except (httpx.ConnectError, httpx.ConnectTimeout):
            if not gemini_key:
                _warn(f"Ollama not reachable at {ollama_url} -- and no GEMINI_API_KEY set. LLM will fail!")
            else:
                _info("Ollama not running (not needed -- Gemini is configured)")
        except Exception as exc:
            _warn(f"Ollama probe error: {exc}")

    # -- Gemini (quick validation that the key works)
    if gemini_key and llm_provider in ("gemini", "auto"):
        try:
            from google import genai
            client = genai.Client(api_key=gemini_key)
            # List models -- fast, cheap way to verify the key
            models = list(client.models.list(config={"page_size": 1}))
            _ok("Gemini API key is valid")
        except Exception as exc:
            err_msg = str(exc)
            if "API_KEY_INVALID" in err_msg or "PERMISSION_DENIED" in err_msg:
                _fail(f"Gemini API key is INVALID -- check your .env")
            else:
                _warn(f"Gemini API probe: {exc}")


# ── 5. Start server ─────────────────────────────────────────────────
def start_server(host: str, port: int, reload: bool) -> None:
    """Start uvicorn from within the backend directory."""
    import uvicorn

    _header("Starting Boliye backend")
    print(f"  {_CYAN}>{_RESET} http://{host}:{port}")
    print(f"  {_CYAN}>{_RESET} API docs: http://{host}:{port}/docs")
    print(f"  {_DIM}  Press Ctrl+C to stop{_RESET}\n")

    os.chdir(str(BACKEND_DIR))
    uvicorn.run(
        "main:app",
        host=host,
        port=port,
        reload=reload,
        log_level="info",
    )


# ── Main ─────────────────────────────────────────────────────────────
def main() -> None:
    parser = argparse.ArgumentParser(
        description="Boliye -- setup checks + backend launcher",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=textwrap.dedent("""\
            Examples:
              python run_local.py                   # start on :8000 with reload
              python run_local.py --port 8080       # custom port
              python run_local.py --no-reload       # production-style
              python run_local.py --check-only      # just run checks, don't start
        """),
    )
    parser.add_argument("--host", default="127.0.0.1", help="Bind host (default: 127.0.0.1)")
    parser.add_argument("--port", type=int, default=8000, help="Bind port (default: 8000)")
    parser.add_argument("--no-reload", action="store_true", help="Disable auto-reload")
    parser.add_argument("--check-only", action="store_true", help="Run checks only, don't start server")
    args = parser.parse_args()

    print(f"\n{_BOLD}{'=' * 50}{_RESET}")
    print(f"{_BOLD}  Boliye -- Local Setup & Launch{_RESET}")
    print(f"{_BOLD}{'=' * 50}{_RESET}")

    # 1. Python
    _header("[1/4] Python")
    py_ok = check_python()

    # 2. Packages
    _header("[2/4] Packages")
    pkg_ok = check_packages()

    # 3. Environment
    _header("[3/4] Environment")
    env_ok = load_and_check_env()

    # 4. Services
    _header("[4/4] Services")
    probe_services()

    # Summary
    _header("Summary")
    all_critical_ok = py_ok and pkg_ok and env_ok

    if all_critical_ok:
        _ok("All critical checks passed")
    else:
        _fail("Some critical checks failed -- fix the issues above")
        if not args.check_only:
            print(f"\n  {_DIM}Starting anyway -- some features may not work{_RESET}")

    if args.check_only:
        sys.exit(0 if all_critical_ok else 1)

    # 5. Launch
    try:
        start_server(
            host=args.host,
            port=args.port,
            reload=not args.no_reload,
        )
    except KeyboardInterrupt:
        print(f"\n{_DIM}Shutting down...{_RESET}")


if __name__ == "__main__":
    main()
