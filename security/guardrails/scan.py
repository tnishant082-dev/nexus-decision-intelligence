"""Heuristic prompt-injection / jailbreak / PII / SQL-write guards.

Not a model firewall and not a database firewall. Patterns are deliberately
narrow so clean OTIF questions stay allowed.
"""
from __future__ import annotations

import re

INJECTION = [
    re.compile(r"ignore (all )?(previous|prior|above) (instructions|prompts)", re.I),
    re.compile(r"you are now ", re.I),
    re.compile(r"system prompt", re.I),
    re.compile(r"developer message", re.I),
    re.compile(r"jailbreak", re.I),
    re.compile(r"dan mode", re.I),
    re.compile(r"override (the )?policy", re.I),
]
PII = [
    ("email", re.compile(r"[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}", re.I)),
    ("ssn_like", re.compile(r"\b\d{3}-\d{2}-\d{4}\b")),
    ("phone", re.compile(r"\b\+?\d{1,3}[-. (]*\d{3}[-. )]*\d{3}[-. ]*\d{4}\b")),
]
SQL_WRITE = re.compile(r"\b(drop|delete|update|insert|alter|truncate|grant)\b", re.I)


def scan(text: str, surface: str = "prompt") -> dict:
    findings = []
    for rx in INJECTION:
        if rx.search(text or ""):
            findings.append(
                {
                    "rule": "prompt_injection",
                    "severity": "block",
                    "detail": f"Injection pattern matched ({rx.pattern}) on {surface}.",
                }
            )
    if re.search(r"jailbreak|do anything now", text or "", re.I):
        findings.append({"rule": "jailbreak", "severity": "block", "detail": "Jailbreak phrasing detected."})
    for name, rx in PII:
        if rx.search(text or ""):
            findings.append(
                {
                    "rule": f"pii:{name}",
                    "severity": "block",
                    "detail": f"Possible {name} in {surface}. Customer names are not stored; do not paste live PII.",
                }
            )
    if surface == "sql" and SQL_WRITE.search(text or ""):
        findings.append(
            {
                "rule": "sql_write",
                "severity": "block",
                "detail": "SQL keyword guard: mutating statements are refused. This is not a database firewall.",
            }
        )
    if surface == "rag" and re.search(r"live sop|production policy|real customer list", text or "", re.I):
        findings.append(
            {
                "rule": "sample_policy",
                "severity": "review",
                "detail": "Knowledge files are SAMPLE. Do not treat them as live SOPs.",
            }
        )
    allowed = not any(f["severity"] == "block" for f in findings)
    return {"allowed": allowed, "findings": findings}
