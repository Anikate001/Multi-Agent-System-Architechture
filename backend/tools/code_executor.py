"""Sandboxed code execution tool using subprocess with timeout and security
restrictions."""

from __future__ import annotations

import asyncio
import tempfile
import os
from pathlib import Path
from typing import Any

import structlog

logger = structlog.get_logger(__name__)

# Imports that are explicitly blocked for security
_BLOCKED_IMPORTS = frozenset({
    "os", "sys", "subprocess", "shutil", "pathlib",
    "importlib", "ctypes", "socket", "http", "urllib",
    "requests", "httpx", "ftplib", "smtplib",
    "pickle", "shelve", "multiprocessing", "threading",
    "signal", "resource", "webbrowser", "code", "codeop",
    "compileall", "py_compile",
})

_SECURITY_PREAMBLE = (
    "# Security sandbox — restricted execution environment\n"
    "import builtins as _b\n"
    "_orig_import = _b.__import__\n"
    "def _restricted_import(name, *args, **kwargs):\n"
    "    _blocked = {blocked}\n"
    "    base = name.split('.')[0]\n"
    "    if base in _blocked:\n"
    "        raise ImportError(f'Import of {{name!r}} is blocked in sandbox')\n"
    "    return _orig_import(name, *args, **kwargs)\n"
    "_b.__import__ = _restricted_import\n\n"
)


class CodeExecutorTool:
    """Execute untrusted code snippets in a sandboxed subprocess with
    timeout enforcement and restricted imports."""

    def __init__(self, default_timeout: int = 30) -> None:
        self._default_timeout = default_timeout

    async def execute(
        self,
        code: str,
        language: str = "python",
        timeout: int | None = None,
    ) -> dict[str, Any]:
        """Execute *code* and return structured results.

        Parameters
        ----------
        code:
            Source code to execute.
        language:
            Programming language (currently only ``"python"`` is supported).
        timeout:
            Max execution time in seconds.

        Returns
        -------
        dict with keys ``stdout``, ``stderr``, ``return_code``, ``timed_out``,
        ``language``, ``error``.
        """
        if language != "python":
            return {
                "stdout": "",
                "stderr": f"Unsupported language: {language}",
                "return_code": 1,
                "timed_out": False,
                "language": language,
                "error": f"Only Python execution is supported, got '{language}'",
            }

        effective_timeout = timeout or self._default_timeout
        sandboxed_code = self._sandbox_code(code)

        logger.info(
            "code_execute_start",
            language=language,
            timeout=effective_timeout,
            code_lines=code.count("\n") + 1,
        )

        # Write to a temporary file so the subprocess has a clean script
        tmp_dir = tempfile.mkdtemp(prefix="nexus_exec_")
        script_path = Path(tmp_dir) / "script.py"
        script_path.write_text(sandboxed_code, encoding="utf-8")

        try:
            proc = await asyncio.create_subprocess_exec(
                "python",
                str(script_path),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=tmp_dir,
                env=self._restricted_env(),
            )

            try:
                stdout_bytes, stderr_bytes = await asyncio.wait_for(
                    proc.communicate(),
                    timeout=effective_timeout,
                )
                timed_out = False
            except asyncio.TimeoutError:
                proc.kill()
                await proc.communicate()
                stdout_bytes, stderr_bytes = b"", b"Execution timed out"
                timed_out = True

            stdout = stdout_bytes.decode("utf-8", errors="replace").strip()
            stderr = stderr_bytes.decode("utf-8", errors="replace").strip()
            return_code = proc.returncode if proc.returncode is not None else -1

            logger.info(
                "code_execute_complete",
                return_code=return_code,
                timed_out=timed_out,
                stdout_len=len(stdout),
                stderr_len=len(stderr),
            )

            return {
                "stdout": stdout,
                "stderr": stderr,
                "return_code": return_code,
                "timed_out": timed_out,
                "language": language,
                "error": stderr if return_code != 0 else None,
            }

        except Exception as exc:
            logger.exception("code_execute_error")
            return {
                "stdout": "",
                "stderr": str(exc),
                "return_code": -1,
                "timed_out": False,
                "language": language,
                "error": str(exc),
            }
        finally:
            # Cleanup temp files
            try:
                script_path.unlink(missing_ok=True)
                Path(tmp_dir).rmdir()
            except OSError:
                pass

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _sandbox_code(self, code: str) -> str:
        """Wrap user code with the import-restriction preamble."""
        blocked_repr = repr(_BLOCKED_IMPORTS)
        preamble = _SECURITY_PREAMBLE.format(blocked=blocked_repr)
        return preamble + code

    @staticmethod
    def _restricted_env() -> dict[str, str]:
        """Return a minimal environment dict for the subprocess."""
        env: dict[str, str] = {}
        # Propagate only essential vars
        for key in ("PATH", "PYTHONPATH", "SYSTEMROOT", "TEMP", "TMP"):
            val = os.environ.get(key)
            if val:
                env[key] = val
        # Prevent the child from reading the parent's secrets
        env["GEMINI_API_KEY"] = ""
        env["TAVILY_API_KEY"] = ""
        return env
