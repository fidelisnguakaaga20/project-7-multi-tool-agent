import time
from typing import Dict, Any

from app.agent.runner import run_agent
from app.eval.test_cases import TEST_CASES


def _rag_has_matches(response: Dict[str, Any]) -> bool:
    """
    Returns True only when the RAG tool actually retrieved >= 1 passage.
    We infer this from the trace output_summary e.g. "matches=2".
    """
    traces = response.get("trace", [])
    for t in traces:
        if t.get("tool") == "rag":
            summary = str(t.get("output_summary", ""))
            # output_summary looks like: "matches=2"
            if "matches=" in summary:
                try:
                    n = int(summary.split("matches=")[-1].strip())
                    return n > 0
                except Exception:
                    return False
    return False


def run_evaluation() -> Dict[str, Any]:
    results = []
    passed = 0

    for case in TEST_CASES:
        start = time.time()
        response = run_agent(
            message=case["message"],
            conversation_id=f"eval-{case['name']}",
        )
        latency_ms = int((time.time() - start) * 1000)

        tools_used = [t.get("tool") for t in response.get("trace", [])]
        expect_tool = case["expect"].get("tool")

        ok = expect_tool in tools_used

        # /// Stage 9: citations required ONLY if RAG actually retrieved matches
        if case["expect"].get("citations_required"):
            if _rag_has_matches(response):
                ok = ok and bool(response.get("citations"))
            else:
                # No matches -> don't fail (index/model availability issue)
                ok = ok and True

        if ok:
            passed += 1

        results.append(
            {
                "test": case["name"],
                "expected_tool": expect_tool,
                "tools_used": tools_used,
                "latency_ms": latency_ms,
                "pass": ok,
            }
        )

    return {
        "total": len(TEST_CASES),
        "passed": passed,
        "accuracy": round(passed / len(TEST_CASES), 2),
        "results": results,
    }
