"""Neo4j push/pull. Idle unless NEO4J_URI is set and the driver connects."""
from __future__ import annotations

import os


def status() -> dict:
    uri = os.getenv("NEO4J_URI")
    if not uri:
        return {
            "configured": False,
            "connected": False,
            "backend": "networkx_snapshot",
            "note": "NEO4J_URI unset. GraphRAG uses the in-process snapshot.",
        }
    try:
        from neo4j import GraphDatabase  # type: ignore
    except ImportError:
        return {
            "configured": True,
            "connected": False,
            "backend": "networkx_snapshot",
            "note": "neo4j Python driver not installed.",
        }
    try:
        driver = GraphDatabase.driver(uri, auth=(os.getenv("NEO4J_USER", "neo4j"), os.getenv("NEO4J_PASSWORD", "")))
        driver.verify_connectivity()
        driver.close()
        return {"configured": True, "connected": True, "backend": "neo4j", "note": "Live Neo4j session verified."}
    except Exception as e:
        return {
            "configured": True,
            "connected": False,
            "backend": "networkx_snapshot",
            "note": f"Neo4j configured but not reachable: {e}",
        }


def push(_payload: dict) -> dict:
    s = status()
    if not s.get("connected"):
        return {"ok": False, "reason": s.get("note")}
    return {"ok": False, "reason": "Push is not implemented without an explicit migrate job."}
