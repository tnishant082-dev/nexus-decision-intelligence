"""Investigate graph state."""
from __future__ import annotations

from typing import Any, TypedDict


class InvestigateState(TypedDict, total=False):
    question: str
    human_review: bool
    retries: int
    snippets: list[str]
    sql_results: list[dict[str, Any]]
    drivers: list[str]
    models: list[dict[str, Any]]
    inventory_notes: list[str]
    risk_notes: list[str]
    documents: list[dict[str, Any]]
    recommendations: list[str]
    action_cards: list[dict[str, Any]]
    pending_review: bool
    trail: list[dict[str, Any]]
    errors: list[str]
