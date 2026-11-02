"""
NEXUS benchmark
===============

Runs the real LangGraph research workflow on a fixed set of queries and reports:

  * success rate             - share of runs that produced a report
  * end-to-end latency       - p50 / p95 seconds per research task
  * per-agent latency        - mean seconds spent in planner, researcher, analyst, writer, critic
  * critic quality score     - mean 1-10 score the Critic gave the final draft
  * first-draft approval     - share of reports the Critic approved without a revision
  * mean revisions           - average Writer <-> Critic revision loops
  * citations per report     - and the share the pipeline marked as verified
  * Redis cache speed-up     - researcher time on a cold run vs. a repeat of the same query

It calls ResearchOrchestrator directly (no HTTP), so it measures the agents, not the API layer.

Prerequisites (from the repo root):
    docker compose -f infra/docker-compose.yml up -d db redis
    # backend/.env (or environment) must contain:
    #   GEMINI_API_KEY=...  TAVILY_API_KEY=...
    #   DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/nexus
    #   REDIS_URL=redis://localhost:6379/0

Run:
    cd backend
    python -m benchmarks.run_benchmark            # all queries, depth=quick
    python -m benchmarks.run_benchmark --limit 3  # quick smoke test
"""
import argparse
import asyncio
import json
import statistics
import time
import uuid
from pathlib import Path

from config.settings import get_settings
from orchestration.graph import ResearchOrchestrator
from schemas.research import ResearchTask
from services.cache_service import CacheService
from services.db_service import DatabaseService

HERE = Path(__file__).resolve().parent
NODE_TO_AGENT = {"plan": "planner", "research": "researcher", "analyze": "analyst",
                 "write": "writer", "review": "critic"}


def pct(values, p):
    values = sorted(values)
    if not values:
        return None
    return values[min(len(values) - 1, int(round(p / 100 * (len(values) - 1))))]


async def run_one(orch, query, depth):
    """Run one research task; return timings and final-state stats."""
    task_id = f"bench-{uuid.uuid4().hex[:8]}"
    node_times = {}
    last = time.perf_counter()
    start = last

    async def on_step(update):
        nonlocal last
        now = time.perf_counter()
        agent = NODE_TO_AGENT.get(update["node"])
        if agent:
            node_times[agent] = node_times.get(agent, 0.0) + (now - last)
        last = now

    task = ResearchTask(query=query, depth=depth, require_human_approval=False)
    result = {"query": query, "ok": False}
    try:
        await orch.run(task, task_id, callback=on_step)
        result["ok"] = True
    except Exception as e:  # record the failure and keep going
        result["error"] = f"{type(e).__name__}: {e}"[:300]
    result["total_s"] = time.perf_counter() - start
    result["agent_s"] = node_times

    state = orch.graph.get_state({"configurable": {"thread_id": task_id}}).values or {}
    review = state.get("review") or {}
    report = state.get("draft_report") or {}
    citations = [c for s in report.get("sections", []) for c in s.get("citations", [])]
    result.update(
        revisions=max(int(state.get("revision_count", 0)) - 1, 0),  # first review counts as 1
        approved_first_draft=bool(review.get("approved")) and int(state.get("revision_count", 0)) <= 1,
        quality_score=review.get("quality_score"),
        citations=len(citations),
        verified_citations=sum(bool(c.get("verified")) for c in citations),
        tokens=sum((state.get("token_usage") or {}).values()) if state.get("token_usage") else None,
    )
    return result


async def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--queries", default=str(HERE / "queries.json"))
    ap.add_argument("--depth", default="quick", choices=["quick", "standard", "deep"])
    ap.add_argument("--limit", type=int, default=None)
    ap.add_argument("--pause", type=float, default=20.0, help="seconds between runs (free-tier rate limits)")
    args = ap.parse_args()

    settings = get_settings()
    cache = CacheService(settings.redis_url)
    await cache.connect()
    db = DatabaseService(settings.database_url)
    await db.init_db()
    orch = ResearchOrchestrator(settings, db, cache)

    queries = json.loads(Path(args.queries).read_text())[: args.limit]
    results = []
    for i, q in enumerate(queries, 1):
        print(f"[{i}/{len(queries)}] {q}")
        r = await run_one(orch, q, args.depth)
        status = "ok" if r["ok"] else f"FAILED ({r.get('error', '')[:80]})"
        print(f"     {r['total_s']:.1f}s  score={r['quality_score']}  revisions={r['revisions']}  {status}")
        results.append(r)
        await asyncio.sleep(args.pause)

    # Cache effect: repeat the first query; Tavily results should now come from Redis.
    print("\nRepeating the first query to measure the Redis cache effect...")
    repeat = await run_one(orch, queries[0], args.depth)

    ok = [r for r in results if r["ok"]]
    lat = [r["total_s"] for r in ok]
    scores = [r["quality_score"] for r in ok if r["quality_score"] is not None]
    cites = sum(r["citations"] for r in ok)
    agents = ["planner", "researcher", "analyst", "writer", "critic"]
    summary = {
        "runs": len(results),
        "success_rate": round(len(ok) / len(results), 3) if results else 0,
        "latency_p50_s": round(statistics.median(lat), 1) if lat else None,
        "latency_p95_s": round(pct(lat, 95), 1) if lat else None,
        "mean_agent_s": {a: round(statistics.mean([r["agent_s"].get(a, 0) for r in ok]), 1) for a in agents} if ok else {},
        "mean_quality_score": round(statistics.mean(scores), 2) if scores else None,
        "first_draft_approval_rate": round(sum(r["approved_first_draft"] for r in ok) / len(ok), 3) if ok else None,
        "mean_revisions": round(statistics.mean([r["revisions"] for r in ok]), 2) if ok else None,
        "citations_per_report": round(cites / len(ok), 1) if ok else None,
        "verified_citation_rate": round(sum(r["verified_citations"] for r in ok) / cites, 3) if cites else None,
        "researcher_s_cold": round(results[0]["agent_s"].get("researcher", 0), 1) if results else None,
        "researcher_s_cached": round(repeat["agent_s"].get("researcher", 0), 1),
    }

    out = HERE / "results.json"
    out.write_text(json.dumps({"summary": summary, "runs": results}, indent=2, default=str))
    print("\n" + json.dumps(summary, indent=2))
    print(f"\nSaved {out} - send the summary block to Claude.")

    await cache.disconnect()
    await db.dispose()


if __name__ == "__main__":
    asyncio.run(main())
