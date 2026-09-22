"""Inferential engineering — estimands, adjusted contrasts, and decision verdicts.

This package is not the LLM gateway in ``inference/``. It engineers whether a
number is allowed to drive an action.
"""
from inferential.studies import claim_summary, run_board, run_study

__all__ = ["run_study", "run_board", "claim_summary"]
