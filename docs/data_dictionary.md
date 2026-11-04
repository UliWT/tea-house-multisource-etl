# Data Dictionary

## Relational source catalog

The PostgreSQL `source` schema contains the reference catalog used later by the Sales and Inventory sources.

### `source.brands`

A brand represents the company or label associated with one or more commercially sellable tea products. `headquarters_country` identifies where the brand is headquartered; it does not describe the origin of the tea. Fictional portfolio brands are marked with `is_fictional = TRUE`.

### `source.products`

A product represents a distinct sellable SKU. Different commercial formats or package sizes are separate products because they may have different prices, inventory quantities, and sales behavior. For example, 20 tea bags / 40g and 100g loose leaf are separate SKUs.

Important fields include:

- `product_id`: deterministic identifier later referenced by Sales and Inventory records.
- `brand_id`: foreign key to `source.brands`.
- `tea_type`: controlled tea taxonomy.
- `origin_country`: country where the tea itself originates; separate from the brand headquarters.
- `product_format`: packaging or commercial format.
- `net_weight_g`: total product weight in grams.
- `units_per_package`: number of tea bags or sachets when applicable; `NULL` is valid for loose-leaf products.

The initial catalog contains 25 brands and 303 products/SKUs across Black Tea, Green Tea, Oolong, White Tea, Pu-erh, Yellow Tea, Matcha, Chai, Rooibos, Herbal Infusion, and Fruit Infusion.

Customers and warehouses are intentionally not seeded in this phase. Future records will reference them through `sales.customer_id` and `inventory.warehouse_id`, while product-to-brand joins will be resolved through `source.products.brand_id`.


## Sales source

Sales is generated from the Inventory ledger. Its public CSV schema is:

```text
sale_id,sale_timestamp,warehouse_id,product_id,customer_id,quantity,unit_price,currency
```

`warehouse_id` is intentionally included so the sum of `quantity` can be reconciled to `inventory_ledger.units_sold` for each date, warehouse, and product. Sales does not simulate demand independently.
