"""Generate public Sales CSVs directly from the Inventory ledger."""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime, time, timedelta
import csv
import io
from pathlib import Path
import random
import re

from .inventory_simulator import LedgerRow, Product, Warehouse, classify_rotation

SALES_HEADER = [
    "sale_id",
    "sale_timestamp",
    "warehouse_id",
    "product_id",
    "customer_id",
    "quantity",
    "unit_price",
    "currency",
]
CUSTOMER_ID_PATTERN = re.compile(r"200000 \+ gs AS customer_id")


@dataclass(frozen=True)
class SaleRow:
    sale_id: int
    sale_timestamp: datetime
    warehouse_id: int
    product_id: int
    customer_id: int
    quantity: int
    unit_price: float
    currency: str


def load_customer_ids(path: Path) -> list[int]:
    """Load the deterministic ID range produced by the customer seed."""
    sql = path.read_text(encoding="utf-8")
    if not CUSTOMER_ID_PATTERN.search(sql):
        raise ValueError(f"Expected customer ID expression not found in {path}")
    return list(range(200001, 210001))


def unit_price(product: Product, warehouse: Warehouse) -> float:
    level_factor = {"high": 1.0, "medium": 1.25, "low": 1.75}[classify_rotation(product)]
    format_factor = {
        "Tea Bags": 1.0, "Tea Sachets": 1.15, "Box": 1.05, "Loose Leaf": 1.35,
        "Pouch": 1.45, "Tin": 1.65, "Matcha Tin": 2.4, "Tea Cake": 2.0,
    }[product.product_format]
    brand_factor = 1.0 + max(product.brand_id - 8, 0) * 0.018
    usd_price = 7.5 * level_factor * format_factor * brand_factor
    currency_factor = {"USD": 1.0, "GBP": 0.79, "EUR": 0.92, "ARS": 1050.0}[warehouse.currency_code]
    return round(usd_price * currency_factor, 2)


def generate_sales(
    ledger: list[LedgerRow],
    products: dict[int, Product],
    warehouses: dict[int, Warehouse],
    customer_ids: list[int],
    *,
    seed: int = 20260831,
    sale_id_start: int = 1000001,
) -> list[SaleRow]:
    """Split ledger units_sold into sale records without changing daily totals."""
    rng = random.Random(seed)
    sales = []
    next_sale_id = sale_id_start
    for row in ledger:
        if row.units_sold == 0:
            continue
        product = products[row.product_id]
        warehouse = warehouses[row.warehouse_id]
        order_count = min(row.units_sold, rng.randint(1, min(4, row.units_sold)))
        quantities = [1] * order_count
        for _ in range(row.units_sold - order_count):
            quantities[rng.randrange(order_count)] += 1
        timestamps = sorted(
            datetime.combine(row.snapshot_date, time(8, 0))
            + timedelta(minutes=rng.randint(0, 12 * 60 - 1))
            for _ in quantities
        )
        for timestamp, quantity in zip(timestamps, quantities):
            sales.append(
                SaleRow(
                    sale_id=next_sale_id,
                    sale_timestamp=timestamp,
                    warehouse_id=row.warehouse_id,
                    product_id=row.product_id,
                    customer_id=customer_ids[rng.randrange(len(customer_ids))],
                    quantity=quantity,
                    unit_price=unit_price(product, warehouse),
                    currency=warehouse.currency_code,
                )
            )
            next_sale_id += 1
    return sales


def validate_sales(
    sales: list[SaleRow],
    ledger: list[LedgerRow],
    customer_ids: set[int],
) -> None:
    expected = defaultdict(int)
    for row in ledger:
        expected[(row.snapshot_date, row.warehouse_id, row.product_id)] = row.units_sold
    actual = defaultdict(int)
    for row in sales:
        key = (row.sale_timestamp.date(), row.warehouse_id, row.product_id)
        actual[key] += row.quantity
        assert row.customer_id in customer_ids
        assert row.quantity > 0
        assert row.unit_price > 0
        assert row.currency in {"GBP", "USD", "EUR", "ARS"}
    assert len({row.sale_id for row in sales}) == len(sales)
    assert dict(actual) == {key: value for key, value in expected.items() if value > 0}


def write_sales_csvs(sales: list[SaleRow], output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    by_date = defaultdict(list)
    for row in sales:
        by_date[row.sale_timestamp.date()].append(row)
    for snapshot_date in sorted(by_date):
        buffer = io.StringIO(newline="")
        writer = csv.writer(buffer, lineterminator="\n")
        writer.writerow(SALES_HEADER)
        for row in by_date[snapshot_date]:
            writer.writerow([
                row.sale_id, row.sale_timestamp.strftime("%Y-%m-%d %H:%M:%S"),
                row.warehouse_id, row.product_id, row.customer_id, row.quantity,
                f"{row.unit_price:.2f}", row.currency,
            ])
        (output_dir / f"sales_{snapshot_date.isoformat()}.csv").write_text(
            buffer.getvalue(), encoding="utf-8"
        )
