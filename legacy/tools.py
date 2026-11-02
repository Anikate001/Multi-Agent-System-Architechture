"""
Tool definitions for the Multi-Agent System.
Provides web search and code execution capabilities to agents.
"""

import subprocess
import sys
import tempfile
import os
from config import TAVILY_API_KEY, MAX_SEARCH_RESULTS


# ═══════════════════════════════════════════════════════════════════════
#  WEB SEARCH TOOL
# ═══════════════════════════════════════════════════════════════════════

def web_search(query: str) -> str:
    """
    Search the web for information.
    Uses Tavily API if available, otherwise falls back to a simple
    DuckDuckGo scrape.

    Args:
        query: The search query string.

    Returns:
        Formatted search results as a string.
    """
    # ── Try Tavily first (best quality) ─────────────────────────────
    if TAVILY_API_KEY and not TAVILY_API_KEY.startswith("tvly-your"):
        try:
            from tavily import TavilyClient
            client = TavilyClient(api_key=TAVILY_API_KEY)
            response = client.search(
                query=query,
                max_results=MAX_SEARCH_RESULTS,
                search_depth="advanced",
            )
            results = []
            for item in response.get("results", []):
                results.append(
                    f"**{item['title']}**\n"
                    f"URL: {item['url']}\n"
                    f"{item['content']}\n"
                )
            if results:
                return "\n---\n".join(results)
        except Exception as e:
            print(f"  ⚠ Tavily search failed: {e}. Using fallback...")

    # ── Fallback: DuckDuckGo via langchain-community ────────────────
    try:
        from langchain_community.tools import DuckDuckGoSearchResults
        ddg = DuckDuckGoSearchResults(num_results=MAX_SEARCH_RESULTS)
        results = ddg.invoke(query)
        if results:
            return str(results)
    except Exception as e:
        print(f"  ⚠ DuckDuckGo search failed: {e}.")

    # ── Last resort ─────────────────────────────────────────────────
    return (
        f"[Search unavailable] Could not search for: '{query}'. "
        f"No search API keys configured. Please set TAVILY_API_KEY in .env "
        f"or install duckduckgo-search: pip install duckduckgo-search"
    )


# ═══════════════════════════════════════════════════════════════════════
#  CODE EXECUTION TOOL (Sandboxed)
# ═══════════════════════════════════════════════════════════════════════

def execute_python_code(code: str, timeout: int = 30) -> str:
    """
    Execute Python code in a sandboxed subprocess.
    Used by the Coder agent to validate generated code.

    Args:
        code: Python source code to execute.
        timeout: Maximum execution time in seconds.

    Returns:
        Execution output (stdout + stderr) or error message.
    """
    # Write code to a temp file
    tmp_dir = os.path.join(os.path.dirname(__file__), ".tmp")
    os.makedirs(tmp_dir, exist_ok=True)

    tmp_path = os.path.join(tmp_dir, "sandbox_exec.py")
    try:
        with open(tmp_path, "w", encoding="utf-8") as f:
            f.write(code)

        result = subprocess.run(
            [sys.executable, tmp_path],
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=tmp_dir,
        )

        output = ""
        if result.stdout:
            output += f"[STDOUT]\n{result.stdout.strip()}\n"
        if result.stderr:
            output += f"[STDERR]\n{result.stderr.strip()}\n"
        if result.returncode != 0:
            output += f"[EXIT CODE] {result.returncode}\n"

        return output if output else "[OK] Code executed successfully with no output."

    except subprocess.TimeoutExpired:
        return f"[TIMEOUT] Code execution exceeded {timeout}s limit."
    except Exception as e:
        return f"[ERROR] Failed to execute code: {e}"
    finally:
        # Cleanup
        if os.path.exists(tmp_path):
            os.remove(tmp_path)
