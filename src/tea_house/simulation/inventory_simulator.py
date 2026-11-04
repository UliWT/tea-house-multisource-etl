"""Reproducible inventory simulation and its latent daily ledger.

The ledger is the source of truth for inventory, future sales, and future
replenishment records. Inventory snapshots are a projection of ledger rows and
retain only the public five-column source schema.
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from datetime import date, timedelta
import csv
import io
from pathlib import Path
import random
import re
from typing import Sequence

SEED = 20260830
DEFAULT_START_DATE = date(2026, 6, 8)
DEFAULT_DAYS = 75
INVENTORY_HEADER = [
    "inventory_id",
    "snapshot_date",
    "warehouse_id",
    "product_id",
    "stock_units",
]
LEDGER_HEADER = [
    "snapshot_date",
    "warehouse_id",
    "product_id",
    "opening_stock",
    "units_sold",
    "units_replenished",
    "closing_stock",
]

PRODUCT_ROW_PATTERN = re.compile(
    r"^\s*\((\d+),\s*(\d+),\s*'((?:[^']|'')+)',\s*'([^']+)',\s*'([^']+)',\s*'([^']+)',\s*([0-9.]+),\s*(NULL|\d+),\s*TRUE\)",
    re.MULTILINE,
)
WAREHOUSE_ROW_PATTERN = re.compile(
    r"\((\d+),\s*'([^']+)',\s*'([^']+)',\s*'([^']+)',\s*'([A-Z]{2})',\s*'([A-Z]{3})',\s*\d+,\s*TRUE\)"
)


@dataclass(frozen=True)
class Product:
    product_id: int
    brand_id: int
    product_name: str
    tea_type: str
    origin_country: str
    product_format: str


@dataclass(frozen=True)
class Warehouse:
    warehouse_id: int
    warehouse_name: str
    city: str
    country: str
    country_code: str
    currency_code: str


@dataclass(frozen=True)
class LedgerRow:
    snapshot_date: date
    warehouse_id: int
    product_id: int
    opening_stock: int
    units_sold: int
    units_replenished: int
    closing_stock: int


@dataclass
class SimulationResult:
    ledger: list[LedgerRow]
    product_ids: set[int]
    warehouse_ids: set[int]
    dates: list[date]
    replenishment_events: int
    stockout_episodes: int


def load_products_from_sql(path: Path) -> dict[int, Product]:
    """Load product IDs and attributes from the existing catalog seed."""
    sql = path.read_text(encoding="utf-8")
    section = sql.split("INSERT INTO source.products", 1)[1].split(
        "ON CONFLICT (product_id)", 1
    )[0]
    products = {}
    for match in PRODUCT_ROW_PATTERN.finditer(section):
        product_id, brand_id, name, tea_type, origin, product_format, _, _ = match.groups()
        products[int(product_id)] = Product(
            product_id=int(product_id),
            brand_id=int(brand_id),
            product_name=name.replace("''", "'"),
            tea_type=tea_type,
            origin_country=origin,
            product_format=product_format,
        )
    if not products:
        raise ValueError(f"No products found in {path}")
    return products


def load_warehouses_from_sql(path: Path) -> dict[int, Warehouse]:
    """Load warehouse IDs and attributes from the existing warehouse seed."""
    sql = path.read_text(encoding="utf-8")
    warehouses = {}
    for match in WAREHOUSE_ROW_PATTERN.finditer(sql):
        warehouse_id, name, city, country, country_code, currency_code = match.groups()
        warehouses[int(warehouse_id)] = Warehouse(
            warehouse_id=int(warehouse_id),
            warehouse_name=name,
            city=city,
            country=country,
            country_code=country_code,
            currency_code=currency_code,
        )
    if not warehouses:
        raise ValueError(f"No warehouses found in {path}")
    return warehouses


def load_reference_pairs(path: Path) -> list[tuple[int, int]]:
    """Preserve the product/warehouse distribution from the small test CSV."""
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames != INVENTORY_HEADER:
            raise ValueError(f"Unexpected reference header in {path}: {reader.fieldnames}")
        pairs = sorted(
            {(int(row["product_id"]), int(row["warehouse_id"])) for row in reader}
        )
    if len(pairs) != 90:
        raise ValueError(f"Expected 90 reference pairs, found {len(pairs)}")
    return pairs


def classify_rotation(product: Product) -> str:
    name = product.product_name.lower()
    if any(
        token in name
        for token in ("matcha", "gyokuro", "white peony", "white sky", "tieguanyin", "pu-erh")
    ):
        return "low"
    if product.tea_type == "Black Tea" and (
        any(
            token in name
            for token in ("earl grey", "english breakfast", "ceylon", "gold", "yorkshire", "original")
        )
        or product.brand_id <= 8
    ):
        return "high"
    return "medium"


BRAND_TIER = {
    1: 1.14, 2: 1.12, 3: 1.10, 4: 1.06, 5: 1.04, 6: 1.05, 7: 1.08, 8: 1.05,
    9: 0.96, 10: 0.98, 11: 0.96, 12: 0.94, 13: 0.93, 14: 0.91, 15: 0.90,
    16: 0.92, 17: 0.86, 18: 0.88, 19: 0.87, 20: 0.85,
    21: 0.86, 22: 0.84, 23: 0.82, 24: 0.88, 25: 0.90,
}
WAREHOUSE_FACTOR = {
    1001: 1.34, 1002: 1.16, 1003: 1.03,
    1004: 1.19, 1005: 1.31, 1006: 1.22,
    1007: 0.96, 1008: 0.91, 1009: 0.79,
}
BASE_DEMAND = {"high": (5, 20), "medium": (2, 10), "low": (0, 4)}
INITIAL_STOCK = {"high": (150, 350), "medium": (80, 220), "low": (30, 100)}
ACTIVITY_PROBABILITY = {"high": 0.94, "medium": 0.84, "low": 0.62}
DEFAULT_PRODUCT_IDS = (
    1001, 1003, 1005, 1007, 1015,
    1021, 1033, 1047, 1061, 1098,
    1110, 1148, 1167, 1200, 1250,
)


def default_reference_pairs(
    products: dict[int, Product],
    warehouses: dict[int, Warehouse],
) -> list[tuple[int, int]]:
    """Build the stable 90-pair source universe without reading old CSVs."""
    warehouse_ids = sorted(warehouses)
    if len(warehouse_ids) < 6:
        raise ValueError("At least six warehouses are required")
    if any(product_id not in products for product_id in DEFAULT_PRODUCT_IDS):
        raise ValueError("The default product universe is missing from source.products")
    pairs = []
    for product_index, product_id in enumerate(DEFAULT_PRODUCT_IDS):
        start = (product_index * 2) % len(warehouse_ids)
        pairs.extend(
            (product_id, warehouse_ids[(start + offset) % len(warehouse_ids)])
            for offset in range(6)
        )
    return sorted(pairs)


def regional_factor(warehouse: Warehouse, product: Product) -> float:
    name = product.product_name.lower()
    tea_type = product.tea_type
    if warehouse.country == "United Kingdom":
        if tea_type == "Black Tea" or any(token in name for token in ("earl grey", "english breakfast", "ceylon")):
            return 1.15
        if tea_type in {"Matcha", "Oolong"}:
            return 0.86
        return 1.00
    if warehouse.country == "United States":
        if tea_type in {"Green Tea", "Matcha", "Oolong", "Fruit Infusion"}:
            return 1.16
        if tea_type == "Black Tea":
            return 0.96
        return 1.02
    if warehouse.country in {"Netherlands", "Germany"}:
        return 1.02 if tea_type in {"Green Tea", "Black Tea", "Oolong"} else 0.98
    if tea_type in {"Black Tea", "Fruit Infusion"} or any(token in name for token in ("earl grey", "english breakfast")):
        return 1.12
    if tea_type in {"Matcha", "Oolong"}:
        return 0.84
    return 0.98


def daily_demand(product: Product, warehouse: Warehouse, day_index: int, rng: random.Random) -> int:
    level = classify_rotation(product)
    low, high = BASE_DEMAND[level]
    if rng.random() > ACTIVITY_PROBABILITY[level]:
        return 0
    nominal = rng.randint(low, high)
    temporal_factor = 1.0 + rng.uniform(-0.09, 0.09) + 0.025 * ((day_index % 11) - 5) / 5
    value = round(
        nominal
        * WAREHOUSE_FACTOR[warehouse.warehouse_id]
        * BRAND_TIER[product.brand_id]
        * regional_factor(warehouse, product)
        * temporal_factor
    )
    return max(0, value)


def generate_inventory_simulation(
    products: dict[int, Product],
    warehouses: dict[int, Warehouse],
    reference_pairs: Sequence[tuple[int, int]],
    *,
    seed: int = SEED,
    start_date: date = DEFAULT_START_DATE,
    days: int = DEFAULT_DAYS,
    inventory_id_start: int = 300001,
) -> SimulationResult:
    """Generate one explicit ledger and its projected inventory states."""
    if days <= 0:
        raise ValueError("days must be positive")
    pairs = sorted(set(reference_pairs))
    if not pairs:
        raise ValueError("At least one product/warehouse pair is required")
    if any(product_id not in products for product_id, _ in pairs):
        raise ValueError("Reference pairs contain an unknown product_id")
    if any(warehouse_id not in warehouses for _, warehouse_id in pairs):
        raise ValueError("Reference pairs contain an unknown warehouse_id")

    rng = random.Random(seed)
    dates = [start_date + timedelta(days=i) for i in range(days)]
    state = {}
    schedules = {}
    for product_id, warehouse_id in pairs:
        product = products[product_id]
        level = classify_rotation(product)
        low, high = INITIAL_STOCK[level]
        pair = (product_id, warehouse_id)
        state[pair] = {"stock": rng.randint(low, high), "recent_sales": [], "replenishments": 0}
        schedules[pair] = [rng.randint(14, 18)]

    ledger = []
    for day_index, snapshot_date in enumerate(dates):
        for product_id, warehouse_id in pairs:
            product = products[product_id]
            warehouse = warehouses[warehouse_id]
            pair = (product_id, warehouse_id)
            current = state[pair]
            opening_stock = current["stock"]
            desired_demand = daily_demand(product, warehouse, day_index, rng)
            units_sold = min(desired_demand, opening_stock)
            after_sales = opening_stock - units_sold
            current["recent_sales"].append(units_sold)
            current["recent_sales"] = current["recent_sales"][-7:]

            units_replenished = 0
            if day_index + 1 in schedules[pair]:
                level = classify_rotation(product)
                interval = rng.randint(14, 18)
                recent_average = sum(current["recent_sales"]) / len(current["recent_sales"])
                factor = {"high": 1.35, "medium": 1.22, "low": 1.08}[level]
                units_replenished = max(
                    1, round(recent_average * interval * factor + rng.randint(-8, 12))
                )
                units_replenished = min(units_replenished, {"high": 360, "medium": 240, "low": 110}[level])
                schedules[pair].append(day_index + 1 + interval)
                current["replenishments"] += 1

            closing_stock = after_sales + units_replenished
            current["stock"] = closing_stock
            ledger.append(
                LedgerRow(
                    snapshot_date=snapshot_date,
                    warehouse_id=warehouse_id,
                    product_id=product_id,
                    opening_stock=opening_stock,
                    units_sold=units_sold,
                    units_replenished=units_replenished,
                    closing_stock=closing_stock,
                )
            )

    stockout_episodes = 0
    by_pair = defaultdict(list)
    for row in ledger:
        by_pair[(row.warehouse_id, row.product_id)].append(row)
    for rows in by_pair.values():
        previous_zero = False
        for row in rows:
            current_zero = row.closing_stock == 0
            if current_zero and not previous_zero:
                stockout_episodes += 1
            previous_zero = current_zero

    return SimulationResult(
        ledger=ledger,
        product_ids={row.product_id for row in ledger},
        warehouse_ids={row.warehouse_id for row in ledger},
        dates=dates,
        replenishment_events=sum(
            1 for row in ledger if row.units_replenished > 0
        ),
        stockout_episodes=stockout_episodes,
    )


def validate_simulation(
    result: SimulationResult,
    products: dict[int, Product],
    warehouses: dict[int, Warehouse],
    expected_pairs: int = 90,
    expected_days: int = DEFAULT_DAYS,
) -> None:
    """Validate the ledger before it is projected into inventory CSVs."""
    expected_dates = [DEFAULT_START_DATE + timedelta(days=i) for i in range(expected_days)]
    assert result.dates == expected_dates
    assert len(result.dates) == expected_days
    assert len(result.ledger) == expected_pairs * expected_days
    keys = [(row.snapshot_date, row.warehouse_id, row.product_id) for row in result.ledger]
    assert len(set(keys)) == len(keys)
    assert all(row.product_id in products for row in result.ledger)
    assert all(row.warehouse_id in warehouses for row in result.ledger)
    assert all(row.opening_stock >= 0 for row in result.ledger)
    assert all(row.units_sold >= 0 for row in result.ledger)
    assert all(row.units_replenished >= 0 for row in result.ledger)
    assert all(row.closing_stock >= 0 for row in result.ledger)
    assert all(row.units_sold <= row.opening_stock for row in result.ledger)
    assert all(
        row.opening_stock - row.units_sold + row.units_replenished == row.closing_stock
        for row in result.ledger
    )
    assert result.stockout_episodes >= 4
    assert result.replenishment_events >= 2


def write_inventory_csvs(result: SimulationResult, output_dir: Path, inventory_id_start: int = 300001) -> None:
    """Write only the public five-column inventory projection."""
    output_dir.mkdir(parents=True, exist_ok=True)
    by_date = defaultdict(list)
    for row in result.ledger:
        by_date[row.snapshot_date].append(row)
    next_id = inventory_id_start
    for snapshot_date in result.dates:
        buffer = io.StringIO(newline="")
        writer = csv.writer(buffer, lineterminator="\n")
        writer.writerow(INVENTORY_HEADER)
        for row in by_date[snapshot_date]:
            writer.writerow([
                next_id,
                row.snapshot_date.isoformat(),
                row.warehouse_id,
                row.product_id,
                row.closing_stock,
            ])
            next_id += 1
        (output_dir / f"inventory_{snapshot_date.isoformat()}.csv").write_text(
            buffer.getvalue(), encoding="utf-8"
        )


def write_ledger_csv(result: SimulationResult, path: Path) -> None:
    """Persist the explicit ledger used as the future Sales source of truth."""
    path.parent.mkdir(parents=True, exist_ok=True)
    buffer = io.StringIO(newline="")
    writer = csv.writer(buffer, lineterminator="\n")
    writer.writerow(LEDGER_HEADER)
    for row in result.ledger:
        writer.writerow([
            row.snapshot_date.isoformat(),
            row.warehouse_id,
            row.product_id,
            row.opening_stock,
            row.units_sold,
            row.units_replenished,
            row.closing_stock,
        ])
    path.write_text(buffer.getvalue(), encoding="utf-8")
