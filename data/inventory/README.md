# Inventory Snapshot Simulation

This directory contains the 75-day inventory history used as the reference state for a future compatible Sales source.

The persistent generator is [`scripts/generate_sources.py`](../../scripts/generate_sources.py), with reusable simulation logic in [`src/tea_house/simulation/inventory_simulator.py`](../../src/tea_house/simulation/inventory_simulator.py) and [`src/tea_house/simulation/sales_simulator.py`](../../src/tea_house/simulation/sales_simulator.py).

## Scope

- Date range: `2026-06-08` through `2026-08-21` (75 consecutive daily snapshots).
- Product/warehouse universe: the 90 product-warehouse pairs from the original test snapshot.
- Rows per file: 90.
- Total rows: 6750.
- CSV schema: `inventory_id,snapshot_date,warehouse_id,product_id,stock_units`.
- Explicit ledger: `ledger/inventory_ledger.csv`.

## Compatibility contract for future Sales

For every product and warehouse pair, each closing inventory value is produced from the persisted daily ledger using:

```text
closing_stock = opening_stock - units_sold + units_replenished
```

Where `units_sold` is the fulfilled demand for that day, capped at the opening stock. Therefore, a stockout represents demand exhausting available stock; it is not an independently assigned random zero. `units_replenished` is an inbound stock event applied after daily sales. Neither ledger value is added as a column to the inventory CSV.

A future Sales generator should generate sale quantities from the same daily demand process, cap fulfilled sales at opening inventory, and reconcile its daily product-warehouse totals against the inventory transitions. Replenishment events are separate from sales and should be modeled as inventory inputs.

## Reproducibility rules

- Deterministic random seed: `20260830`.
- Initial stock bands: high rotation `150-350`, medium `80-220`, low `30-100`.
- Daily demand bands: high `5-20`, medium `2-10`, low `0-4`.
- Activity probabilities: high `0.94`, medium `0.84`, low `0.62`, so not every product sells every day.
- Replenishment intervals vary between 14 and 18 days per product-warehouse pair.
- Replenishment quantities depend on the trailing seven-day fulfilled demand average, the product rotation class, and current stock conditions.
- Demand is adjusted by product brand tier, warehouse market size, and regional preferences (UK, USA, continental Europe, and Buenos Aires/LATAM).
- A small bounded temporal variation is applied; no strong seasonality is modeled.

The exact product and warehouse IDs remain those defined in the SQL seeds; this README documents the simulation contract without changing the CSV schema.

## Reproduction

From the project root:

```bash
python3 scripts/generate_sources.py
```

The default seed is `20260830`. The command validates the complete ledger before writing Inventory and Sales projections. The ledger is the single source of truth for both sources; `units_sold` must be consumed from the ledger rather than regenerated independently. Sales includes `warehouse_id` so it can reconcile directly at date, warehouse, and product level.
