# Sales Source

Sales is generated from `data/inventory/ledger/inventory_ledger.csv` by `scripts/generate_sources.py`. It does not simulate demand independently.

## CSV schema

```text
sale_id,sale_timestamp,warehouse_id,product_id,customer_id,quantity,unit_price,currency
```

`warehouse_id` is included so daily sales can reconcile directly with Inventory at the `(snapshot_date, warehouse_id, product_id)` grain. The sum of `quantity` for each grain equals the ledger `units_sold` value.

The ledger remains the source of truth for `units_sold`; Sales rows only distribute those units into individual transactions.
