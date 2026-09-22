"""Order-volume versus rate-excess split. Fixtures only — no full warehouse."""
from __future__ import annotations

import sys
from pathlib import Path

import duckdb

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def _write_orders(
    path: Path,
    a_orders: int,
    a_late: int,
    b_orders: int,
    b_late: int,
    sales: float,
) -> None:
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
    con.execute("INSERT INTO dim_warehouse VALUES (1, 'A'), (2, 'B')")
    con.execute("INSERT INTO dim_product VALUES (1, 'General')")

    def add(start: int, n: int, warehouse: int, late_n: int) -> None:
        rows = [
            (start + i, warehouse, 1, 1 if i < late_n else 0, 1, sales)
            for i in range(n)
        ]
        con.executemany("INSERT INTO fact_orders VALUES (?, ?, ?, ?, ?, ?)", rows)

    add(1, a_orders, 1, a_late)
    add(100_000, b_orders, 2, b_late)
    con.executemany(
        "INSERT INTO fact_shipments VALUES (?, ?, ?)",
        [(1, 1, 1)] * 40 + [(0, 0, 1)] * 40 + [(0, 0, 2)] * 40,
    )
    con.close()


def test_same_late_rate_more_orders_is_volume(tmp_path: Path):
    from decisions.decompose import exposure_split

    db = tmp_path / "nexus.duckdb"
    _write_orders(db, a_orders=200, a_late=40, b_orders=50, b_late=10, sales=50.0)
    out = exposure_split(db, "A")
    assert out["ok"] is True
    assert out["orders"] > out["rest_orders"]
    assert abs(out["warehouse_late_rate"] - out["rest_of_network_late_rate"]) < 1e-12
    assert abs(out["rate_excess_dollars"]) < 0.05
    assert abs(out["volume_dollars"] - out["late_line_revenue"]) < 0.05
    assert abs(out["volume_dollars"] + out["rate_excess_dollars"] - out["late_line_revenue"]) < 0.01
    assert out["pool_is_large"] is True
    assert "large, not later" in out["explanation"]
    assert "not a causal effect" in out["formula"]
    assert "not recovered EBITDA" in out["formula"]
    assert out["causal_claim"] is False
    assert "lost sales" in out["does_not_mean"].lower()


def test_small_warehouse_much_later_is_rate_excess(tmp_path: Path):
    from decisions.decompose import exposure_split

    db = tmp_path / "nexus.duckdb"
    _write_orders(db, a_orders=20, a_late=16, b_orders=200, b_late=20, sales=25.0)
    out = exposure_split(db, "A")
    assert out["ok"] is True
    assert out["orders"] < out["rest_orders"]
    assert out["warehouse_late_rate"] > out["rest_of_network_late_rate"]
    assert out["rate_excess_dollars"] > out["volume_dollars"]
    assert out["rate_excess_share"] > 0.5
    assert abs(out["volume_dollars"] + out["rate_excess_dollars"] - out["late_line_revenue"]) < 0.01
    assert "large, not later" not in out["explanation"]
    assert out["causal_claim"] is False


def test_next_action_attaches_the_split_and_still_holds(tmp_path: Path):
    from decisions.policy import next_action

    db = tmp_path / "nexus.duckdb"
    _write_orders(db, a_orders=200, a_late=40, b_orders=50, b_late=10, sales=50.0)
    policy = next_action(db)
    assert policy["ok"] is True
    assert policy["decision"] == "hold"
    assert policy["causal_claim"] is False
    assert policy["extract_window"] == "2015-01-01 → 2018-01-31"
    assert policy["refused"][0]["verdict"] == "do_not_claim"
    assert "lost sales" in policy["does_not_mean"].lower()
    split = policy["exposure_split"]
    assert split["ok"] is True
    assert split["warehouse"] == policy["warehouse"] == "A"
    assert abs(split["rate_excess_dollars"]) < 0.05
    assert "large, not later" in split["explanation"]
