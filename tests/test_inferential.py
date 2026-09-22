"""Inferential engineering: adjustment, refusal, and the API card."""
from __future__ import annotations

import shutil
import sys
from pathlib import Path

import duckdb
import numpy as np
from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def _counts(n_event: int, n: int) -> np.ndarray:
    return np.array([1] * n_event + [0] * (n - n_event), dtype=float)


def test_stratification_removes_mix_confounding():
    from inferential.engine import association_signal, stratified_risk_difference

    # Within each category the late rate does not depend on the arm.
    # The focal arm sits in the high-late category, so the crude gap is large.
    y = np.concatenate([
        _counts(200, 400),  # stratum A, treated, p=0.50
        _counts(20, 40),    # stratum A, control, p=0.50
        _counts(4, 40),     # stratum B, treated, p=0.10
        _counts(40, 400),   # stratum B, control, p=0.10
    ])
    treat = np.concatenate([
        np.ones(400), np.zeros(40), np.ones(40), np.zeros(400),
    ]).astype(int)
    stratum = np.array(["A"] * 440 + ["B"] * 440)
    fit = stratified_risk_difference(y, treat, stratum, min_cell=20)
    assert fit["ok"]
    assert fit["naive_risk_difference"] > 0.20
    assert abs(fit["adjusted_risk_difference"]) < 1e-9
    assert fit["ci_low"] < 0 < fit["ci_high"]
    assert association_signal(fit["ci_low"], fit["ci_high"], 0.02) == "hold"


def test_clear_gap_is_a_prioritize_signal():
    from inferential.engine import association_signal, stratified_risk_difference

    y = np.concatenate([_counts(200, 500), _counts(100, 500)])
    treat = np.concatenate([np.ones(500), np.zeros(500)]).astype(int)
    stratum = np.array(["only"] * 1000)
    fit = stratified_risk_difference(y, treat, stratum, min_cell=20)
    assert fit["ok"]
    assert fit["ci_low"] > 0.02
    assert association_signal(fit["ci_low"], fit["ci_high"], 0.02) == "prioritize"


def test_small_samples_cannot_see_a_two_point_gap():
    from inferential.power import minimum_detectable_effect

    assert minimum_detectable_effect(40, 40, 0.3) > 0.02
    assert minimum_detectable_effect(20000, 20000, 0.3) < 0.02


def test_one_stratum_can_flip_the_sign():
    from inferential.engine import leave_one_stratum_out

    y = np.concatenate([
        _counts(240, 400),
        _counts(80, 400),
        _counts(4, 40),
        _counts(20, 40),
    ])
    treat = np.concatenate([
        np.ones(400), np.zeros(400), np.ones(40), np.zeros(40),
    ]).astype(int)
    stratum = np.array(["A"] * 800 + ["B"] * 80)
    out = leave_one_stratum_out(y, treat, stratum, min_cell=20)
    assert out["checked"] is True
    assert out["sign_flip"] is True


def test_nullification_bias_is_the_distance_from_zero_to_the_bound():
    from inferential.engine import nullification_bias

    # |0.10| - 1.96 * 0.01
    assert abs(nullification_bias(0.10, 0.01, z=1.96) - 0.0804) < 1e-9
    assert nullification_bias(0.01, 0.02, z=1.96) == 0.0


def test_selected_treatment_overrides_a_large_gap():
    from inferential.studies import _card

    fit = {
        "ok": True,
        "method": "test",
        "alpha": 0.05,
        "n": 400,
        "n_treated": 200,
        "n_control": 200,
        "p_treated": 0.8,
        "p_control": 0.2,
        "naive_risk_difference": 0.6,
        "naive_se": 0.04,
        "adjusted_risk_difference": 0.55,
        "se": 0.04,
        "ci_low": 0.47,
        "ci_high": 0.63,
        "z": 1.96,
        "strata_used": 2,
        "strata_dropped": 0,
        "min_cell": 20,
    }
    card = _card(
        study_id="advance_selection",
        title="selected",
        estimand={"target_warehouse": None},
        identification={"class": "selected_treatment", "causal_claim": False, "assumptions": [], "failures": ["selected"]},
        fit=fit,
        override_verdict="do_not_claim",
        action_for={"do_not_claim": "refuse"},
    )
    assert card["statistical_signal"] == "prioritize"
    assert card["decision"]["verdict"] == "do_not_claim"
    assert card["decision"]["causal_claim"] is False
    assert card["decision"]["overrides_signal"] is True


def _fixture_db(path: Path) -> None:
    con = duckdb.connect(str(path))
    con.execute("CREATE TABLE dim_warehouse (warehouse_key INTEGER, warehouse_name VARCHAR)")
    con.execute("CREATE TABLE dim_product (product_key INTEGER, category_name VARCHAR)")
    con.execute(
        """
        CREATE TABLE fact_orders (
          order_id INTEGER, warehouse_key INTEGER, product_key INTEGER,
          is_late INTEGER, is_revenue INTEGER, net_sales DOUBLE
        )
        """
    )
    con.execute(
        """
        CREATE TABLE fact_shipments (
          is_late INTEGER, is_advance INTEGER, warehouse_key INTEGER
        )
        """
    )
    con.execute("INSERT INTO dim_warehouse VALUES (1, 'Alpha'), (2, 'Beta')")
    con.execute("INSERT INTO dim_product VALUES (1, 'Electronics'), (2, 'Apparel')")

    def orders(start: int, n: int, warehouse: int, product: int, late_n: int, sales: float):
        rows = []
        for i in range(n):
            rows.append((start + i, warehouse, product, 1 if i < late_n else 0, 1, sales))
        con.executemany("INSERT INTO fact_orders VALUES (?, ?, ?, ?, ?, ?)", rows)

    # Alpha is later inside both categories and carries more late revenue.
    orders(1, 80, 1, 1, 40, 100.0)
    orders(1000, 80, 1, 2, 32, 100.0)
    orders(2000, 80, 2, 1, 8, 10.0)
    orders(3000, 80, 2, 2, 4, 10.0)

    ship_rows = [(1, 1, 1)] * 40 + [(0, 1, 1)] * 10 + [(0, 0, 1)] * 80 + [(1, 0, 2)] * 10 + [(0, 0, 2)] * 80
    con.executemany("INSERT INTO fact_shipments VALUES (?, ?, ?)", ship_rows)
    con.close()


def test_registered_studies_on_a_fixture():
    from inferential.studies import run_board, run_study

    folder = Path(__file__).resolve().parent / "_inferential_fixture"
    folder.mkdir(exist_ok=True)
    db = folder / "nexus.duckdb"
    if db.exists():
        db.unlink()
    _fixture_db(db)
    try:
        board = run_board(db)
        assert board["discipline"] == "inferential_engineering"
        by_id = {card["study_id"]: card for card in board["studies"]}

        gap = by_id["warehouse_late_gap"]
        assert gap["ok"]
        assert gap["estimand"]["target_warehouse"] == "Alpha"
        assert gap["estimate"]["adjusted_risk_difference"] > 0.02
        assert gap["decision"]["verdict"] == "prioritize"
        assert gap["decision"]["causal_claim"] is False
        assert gap["stability"]["sign_flip"] is False
        assert "minimum_detectable_effect" in gap["power"]

        from decisions.policy import next_action

        policy = next_action(db)
        assert policy["decision"] == "investigate"
        assert policy["causal_claim"] is False
        assert "lost sales" in policy["does_not_mean"].lower()
        assert policy["refused"][0]["verdict"] == "do_not_claim"

        advance = by_id["advance_selection"]
        assert advance["ok"]
        assert advance["statistical_signal"] == "prioritize"
        assert advance["decision"]["verdict"] == "do_not_claim"

        missing = run_study("not-a-study", db=db)
        assert missing["ok"] is False
    finally:
        shutil.rmtree(folder, ignore_errors=True)


def test_inferential_api_shape():
    from backend.main import app

    client = TestClient(app)
    response = client.get(
        "/api/v1/inferential/board",
        headers={"X-API-Key": "dev-nexus-key"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["discipline"] == "inferential_engineering"
    assert body["not"] == "llm_inference_gateway"
    assert len(body["studies"]) == 2
    nxt = client.get("/api/v1/decision/next", headers={"X-API-Key": "dev-nexus-key"})
    assert nxt.status_code == 200
    assert nxt.json()["causal_claim"] is False
