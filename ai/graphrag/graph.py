"""In-process entity graph. NetworkX is optional; dict fallback is the default path."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SNAPSHOT = ROOT / "artifacts" / "graph_snapshot.json"


def load_graph(path: Path | None = None) -> dict:
    p = path or SNAPSHOT
    data = json.loads(p.read_text())
    data.setdefault("backend", "networkx_snapshot")
    data.setdefault("neo4j", False)
    return data


def to_networkx(payload: dict | None = None):
    """Return a NetworkX DiGraph if the extra is installed, else None."""
    try:
        import networkx as nx  # type: ignore
    except ImportError:
        return None
    payload = payload or load_graph()
    g = nx.DiGraph()
    for n in payload.get("nodes") or []:
        g.add_node(n["id"], **n)
    for e in payload.get("edges") or []:
        g.add_edge(e["source"], e["target"], **e)
    return g


def nodes_of(payload: dict, typ: str) -> list[dict]:
    return [n for n in payload.get("nodes") or [] if n.get("type") == typ]


def node_by_id(payload: dict, nid: str) -> dict | None:
    for n in payload.get("nodes") or []:
        if n.get("id") == nid:
            return n
    return None


def out_edges(payload: dict, nid: str) -> list[dict]:
    return [e for e in payload.get("edges") or [] if e.get("source") == nid]


def in_edges(payload: dict, nid: str) -> list[dict]:
    return [e for e in payload.get("edges") or [] if e.get("target") == nid]
