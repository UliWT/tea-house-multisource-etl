#!/usr/bin/env python3
"""Generate synchronized Inventory and Sales sources from one ledger."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from tea_house.simulation.inventory_simulator import (  # noqa: E402
    DEFAULT_DAYS, DEFAULT_START_DATE, SEED, default_reference_pairs,
    generate_inventory_simulation, load_products_from_sql, load_warehouses_from_sql,
    validate_simulation, write_inventory_csvs, write_ledger_csv,
)
from tea_house.simulation.sales_simulator import (  # noqa: E402
    generate_sales, load_customer_ids, validate_sales, write_sales_csvs,
)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--inventory-output-dir", type=Path, default=PROJECT_ROOT / "data/inventory")
    parser.add_argument("--sales-output-dir", type=Path, default=PROJECT_ROOT / "data/incoming/sales")
    parser.add_argument("--ledger-path", type=Path, default=None)
    parser.add_argument("--seed", type=int, default=SEED)
    args = parser.parse_args()

    sql_dir = PROJECT_ROOT / "sql/seed"
    products = load_products_from_sql(sql_dir / "03_seed_catalog.sql")
    warehouses = load_warehouses_from_sql(sql_dir / "04_create_seed_warehohuses.sql")
    customers = load_customer_ids(sql_dir / "05_seed_customers.sql")
    pairs = default_reference_pairs(products, warehouses)
    result = generate_inventory_simulation(
        products, warehouses, pairs, seed=args.seed,
        start_date=DEFAULT_START_DATE, days=DEFAULT_DAYS,
    )
    validate_simulation(result, products, warehouses)
    sales = generate_sales(result.ledger, products, warehouses, customers, seed=args.seed + 1)
    validate_sales(sales, result.ledger, set(customers))

    ledger_path = args.ledger_path or args.inventory_output_dir / "ledger/inventory_ledger.csv"
    write_ledger_csv(result, ledger_path)
    write_inventory_csvs(result, args.inventory_output_dir)
    write_sales_csvs(sales, args.sales_output_dir)
    print(f"Generated {DEFAULT_DAYS} Inventory snapshots and {DEFAULT_DAYS} Sales files.")
    print(f"Inventory rows: {len(result.ledger)}; Sales rows: {len(sales)}")
    print(f"Ledger: {ledger_path}")
    print(f"Replenishment events: {result.replenishment_events}; stockout episodes: {result.stockout_episodes}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
