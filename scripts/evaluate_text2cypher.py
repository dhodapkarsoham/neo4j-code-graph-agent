#!/usr/bin/env python3
"""Evaluate text2cypher across modes (no-docs, append, docs-only).

Runs a small suite of queries against the running server's /api/text2cypher
endpoint and reports:
- rows: number of results
- chain_ok: whether canonical Commit->FileVer->File chain appears in the query
- uses_fpath: whether f.path is used for file filtering
- latency_ms: db latency reported by backend

Usage:
  python scripts/evaluate_text2cypher.py --host http://localhost:8000

This script is read-only and does not modify the database.
"""

import argparse
import json
import re
import sys
from dataclasses import dataclass
from typing import Dict, List, Tuple

import urllib.request


@dataclass
class EvalCase:
    name: str
    question: str


CASES: List[EvalCase] = [
    EvalCase(
        name="developers_louvain",
        question="Who worked on Louvain?",
    ),
    EvalCase(
        name="devs_methods_in_similarity",
        question="Which developers worked on methods that are part of a similarity community?",
    ),
    EvalCase(
        name="files_with_similarity_methods",
        question="List files that declare methods in a similarity community.",
    ),
    EvalCase(
        name="files_with_external_deps",
        question="Which files depend on external dependencies?",
    ),
    EvalCase(
        name="method_calls",
        question="Show method call relationships.",
    ),
]


def post_json(url: str, payload: Dict) -> Dict:
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        charset = resp.headers.get_content_charset() or "utf-8"
        txt = resp.read().decode(charset, errors="replace")
        return json.loads(txt)


def evaluate_case(host: str, case: EvalCase) -> List[Tuple[str, Dict]]:
    url = f"{host.rstrip('/')}/api/text2cypher"
    modes = [
        ("no_docs", {"include_graph_docs": False, "use_docs_only": False}),
        ("append_docs", {"include_graph_docs": True, "use_docs_only": False}),
        ("docs_only", {"include_graph_docs": True, "use_docs_only": True}),
    ]
    results = []
    for mode_name, flags in modes:
        payload = {"question": case.question, **flags}
        try:
            res = post_json(url, payload)
        except Exception as e:
            res = {"error": str(e)}
        results.append((mode_name, res))
    return results


def summarize(res: Dict) -> Dict[str, object]:
    query = res.get("generated_query", "") or ""
    metrics = res.get("db_metrics", {}) or {}
    rows = metrics.get("rows")
    latency = metrics.get("latency_ms")
    chain_ok = bool(re.search(r"CHANGED\]->\(fv:FileVer\).*OF_FILE\]->\(f:File\)", query))
    uses_fpath = "f.path" in query
    declares_ok = "-[:DECLARES]->(m:Method)" in query or re.search(r"DECLARES\]->\(m:Method\)", query) is not None
    imports_ok = bool(re.search(r"IMPORTS\]->\(imp:Import\).*DEPENDS_ON\]->\(dep:ExternalDependency\)", query))
    simcomm_filter = "similarityCommunity" in query
    return {
        "rows": rows,
        "latency_ms": latency,
        "chain_ok": chain_ok,
        "uses_fpath": uses_fpath,
        "declares_ok": declares_ok,
        "imports_ok": imports_ok,
        "simil_comm": simcomm_filter,
        "query": query,
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--host", default="http://localhost:8000", help="Server host base URL")
    args = ap.parse_args()

    print("Evaluating text2cypher modes...\n")

    header = f"{'case':<28} {'mode':<12} {'rows':>5} {'chain':>6} {'f.path':>7} {'decl':>5} {'imp':>4} {'sim':>4} {'latency_ms':>11}"
    print(header)
    print("-" * len(header))

    improvements: List[str] = []

    for case in CASES:
        mode_results = evaluate_case(args.host, case)
        summarized = {mode: summarize(res) for mode, res in mode_results}

        for mode, res in mode_results:
            s = summarized[mode]
            print(
                f"{case.name:<28} {mode:<12} {str(s['rows'] or '?'):>5} {('ok' if s['chain_ok'] else 'x'):>6} {('yes' if s['uses_fpath'] else 'no'):>7} {('ok' if s['declares_ok'] else 'x'):>5} {('ok' if s['imports_ok'] else 'x'):>4} {('ok' if s['simil_comm'] else 'x'):>4} {str(round(s['latency_ms'],1)) if s['latency_ms'] else '?':>11}"
            )

        # Simple improvement signal: docs_only succeeds where no_docs failed previously
        nd_rows = summarized.get("no_docs", {}).get("rows")
        do_rows = summarized.get("docs_only", {}).get("rows")
        do_chain = summarized.get("docs_only", {}).get("chain_ok")
        if (do_rows or 0) > 0 and do_chain and (nd_rows or 0) >= 0:
            improvements.append(
                f"{case.name}: docs_only rows={do_rows}, chain_ok={do_chain}"
            )

    print("\nExamples where docs-only shows upside:")
    if improvements:
        for line in improvements:
            print(f"- {line}")
    else:
        print("- None identified in this run (consider adding more cases)")

    print("\nTip: share contrasting queries with colleagues by pasting the generated_query from each mode.")

    return 0


if __name__ == "__main__":
    sys.exit(main())


