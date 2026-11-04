# Tea Data Platform

## 1. Objective

Tea Data Platform is a portfolio Data Engineering project that simulates the data platform of a tea importing company.

The company receives daily information from multiple independent sources:

- a product CSV file;
- an inventory CSV file;
- a daily sales CSV file;
- a REST API providing exchange rates.

The objective is to build a production-inspired ETL pipeline orchestrated with Apache Airflow, executed with Docker and Docker Compose, and backed by PostgreSQL.

The design prioritizes maintainability, scalability, modularity, traceability, incremental loads, idempotency, and observability.

> This document defines the project's architecture and decisions. It does not contain the pipeline implementation.

## 2. Technology Stack

- Python
- Pandas
- PostgreSQL
- SQL
- Apache Airflow
- Docker
- Docker Compose

## 3. General Flow

```text
Product CSV ────────┐
Inventory CSV ──────┤
Daily sales CSV ────┼──> Extract ──> raw ──> Validate/Transform ──> staging
Exchange-rate API ──┘                                             │
                                                                  ▼
                                                            analytics
                                                                  │
                                                                  ▼
                                                             monitoring
```

The original data must be preserved. The `raw` layer represents exactly what was received and makes it possible to audit or reprocess a load if the transformation logic changes.

## 4. Data Sources

### 4.1 Products

Expected fields:

- `product_id`
- `product_name`
- `brand`
- `category`
- `origin_country`
- `supplier_id`
- `unit_price`
- `currency`
- `active`
- `updated_at`

This represents the product catalog and serves as a reference dimension for sales and inventory.

### 4.2 Inventory

Expected fields:

- `inventory_date`
- `product_id`
- `warehouse_country`
- `quantity_available`
- `reorder_level`
- `unit_cost`
- `currency`

This makes it possible to identify available stock, low stock, and out-of-stock products.

### 4.3 Sales

Expected fields:

- `sale_id`
- `sale_timestamp`
- `warehouse_id`
- `product_id`
- `customer_id`
- `quantity`
- `unit_price`
- `currency`

This is the primary source of commercial facts.

Sales records include `warehouse_id` so daily quantities can be reconciled directly with the Inventory ledger at the grain `(snapshot_date, warehouse_id, product_id)`.

### 4.4 Exchange-Rate API

The API provides currency conversions. Each response must be stored as a snapshot containing:

- source currency;
- target currency;
- exchange rate;
- effective date;
- query timestamp;
- provider;
- `pipeline_run_id`.

The transformation must use the stored snapshot and must not query the API again during historical reprocessing. This ensures that the same run remains reproducible.

## 5. PostgreSQL Schemas

PostgreSQL uses four schemas with distinct responsibilities:

```text
raw          Received data and original evidence
staging      Cleaned, typed, and normalized data
analytics    Data modeled for analysis
monitoring   Operational metadata and data quality information
```

### 5.1 `raw` Schema

This contains data as received, with minimal modifications. It should preferably be append-only.

Tables:

- `raw.products`
- `raw.inventory`
- `raw.sales`
- `raw.exchange_rates`
- `raw.rejected_records`

Raw business tables must include ingestion metadata:

- `ingestion_id`;
- `source_file_name`;
- `source_file_path`;
- `source_file_hash`;
- `ingested_at`;
- `pipeline_run_id`;
- original record number.

`raw.rejected_records` preserves records that cannot pass basic validations, together with the applicable rule and corresponding error.

### 5.2 `staging` Schema

This contains data prepared for analytical modeling.

Tables:

- `staging.products_clean`
- `staging.inventory_clean`
- `staging.sales_clean`
- `staging.exchange_rates_clean`
- `staging.data_quality_results`

Responsibilities:

- normalize names;
- convert data types;
- handle missing values;
- remove duplicates;
- validate business rules;
- apply currency conversions;
- resolve relationships between sources.

Sales and inventory must preserve both the original amount and the standardized amount:

```text
original_amount
original_currency
exchange_rate
standard_currency
standard_amount
```

The standard currency may be USD, but it must be configurable and documented.

### 5.3 `analytics` Schema

This contains models designed for analytical consumption. A combination of a dimensional model and aggregate tables is recommended.

Dimensions:

- `analytics.dim_product`
- `analytics.dim_country`
- `analytics.dim_date`
- `analytics.dim_currency`

Facts:

- `analytics.fact_sales`
- `analytics.fact_inventory`

Aggregates:

- `analytics.sales_by_country`
- `analytics.sales_by_brand`
- `analytics.daily_revenue`
- `analytics.inventory_status`
- `analytics.top_products`

### 5.4 `monitoring` Schema

This contains the pipeline's operational state and evidence.

Main tables:

- `monitoring.pipeline_runs`
- `monitoring.pipeline_tasks`
- `monitoring.processed_files`
- `monitoring.data_quality_checks`
- `monitoring.pipeline_errors`
- `monitoring.row_counts`

## 6. Incremental Loading and Idempotency

### 6.1 File Directories

`data/incoming/` contains files waiting to be processed.

```text
data/incoming/
├── products_YYYY-MM-DD.csv
├── inventory_YYYY-MM-DD.csv
└── sales_YYYY-MM-DD.csv
```

`data/processed/` contains successfully processed files, organized by date:

```text
data/processed/YYYY/MM/DD/
```

A file is moved to `processed` only after the required loads have completed successfully. If the pipeline fails, the file remains in `incoming` or is left in a `failed` state to allow recovery.

### 6.2 `monitoring.processed_files` Table

This table must contain at least:

- `processed_file_id`;
- `file_name`;
- `file_path`;
- `source_type`;
- `file_size`;
- `file_hash`;
- `arrival_timestamp`;
- `processing_started_at`;
- `processing_completed_at`;
- `status`;
- `pipeline_run_id`;
- `rows_read`;
- `rows_loaded`;
- `duplicates_removed`;
- `error_message`.

File identity must be based on `source_type + file_hash`. The file name alone is not sufficient because a file could be replaced while keeping the same name.

Possible states:

```text
detected
processing
processed
failed
quarantined
```

### 6.3 Duplicate Prevention

The pipeline must prevent duplicates across multiple layers:

1. Calculate the file hash.
2. Check `processed_files` before processing it.
3. Ignore hashes that have already been processed successfully.
4. Apply natural business keys in staging and analytics.
5. Use primary keys, unique indexes, and PostgreSQL transactions.
6. Record the number of removed duplicates.

Examples of business keys:

- sales: `sale_id`;
- inventory: `product_id`, date, and warehouse;
- products: `product_id` and version or update date.

Running the same DAG twice for the same files must produce the same final state.

## 7. Validations

### 7.1 Schema

- required columns are present;
- unexpected columns are detected;
- the structure is compatible with the source contract.

### 7.2 Data Types

- quantities are numeric;
- prices are decimal values;
- timestamps are valid;
- currencies are valid;
- flags are boolean.

Records that cannot be converted must be sent to `raw.rejected_records`.

### 7.3 Business Rules

- sold quantities are greater than zero;
- prices are not negative;
- currencies are supported;
- products exist;
- inventory quantities are not negative;
- critical IDs are not null;
- dates are reasonable.

### 7.4 Duplicates

The pipeline must distinguish between physical duplicates, business duplicates, and legitimate updates. Deduplication must use business keys, not only compare complete rows.

## 8. Currency Conversion

The original amount must never be overwritten.

Process:

1. Extract data from the API.
2. Validate the response.
3. Save the snapshot in `raw.exchange_rates`.
4. Clean it in `staging.exchange_rates_clean`.
5. Associate each sale and inventory record with the corresponding rate.
6. Calculate the amount in the standard currency.
7. Reject or flag records for which no rate is available.

Missing exchange rates must not be invented. The policy must be documented; for this project, marking the record as invalid or failing the run when the rate is critical is recommended.

## 9. Airflow DAG

The daily DAG is conceptually named `tea_daily_etl`.

Tasks:

1. `start_pipeline_run`: creates the run record with a `running` status.
2. `detect_new_files`: inspects `incoming`, calculates hashes, and determines which files to process.
3. `extract_products`: reads new product files.
4. `extract_inventory`: reads new inventory files.
5. `extract_sales`: reads new sales files.
6. `extract_exchange_rates`: queries the API and saves the snapshot.
7. `validate_raw_data`: validates schema, types, and basic rules.
8. `deduplicate_raw_data`: identifies and records duplicates.
9. `transform_products`: generates `staging.products_clean`.
10. `transform_inventory`: generates `staging.inventory_clean` and applies currency conversion.
11. `transform_sales`: generates `staging.sales_clean` and calculates revenue.
12. `load_raw`: consolidates or confirms the load of original data.
13. `load_staging`: loads clean data using transactions.
14. `refresh_analytics`: updates dimensions, facts, and aggregates.
15. `register_processed_files`: marks files as processed and moves them.
16. `register_pipeline_success`: records final metrics and a successful status.
17. `register_pipeline_failure`: records the error, failed task, and run status.

Conceptual dependencies:

```text
start_pipeline_run
          │
          ▼
detect_new_files
          │
   ┌──────┼────────┬──────────────┐
   ▼      ▼        ▼              ▼
products inventory sales   exchange_rates
   │      │        │              │
   └──────┴────────┴──────┬───────┘
                          ▼
                 validate_raw_data
                          │
                          ▼
                 deduplicate_raw_data
                          │
                ┌─────────┼─────────┐
                ▼         ▼         ▼
       transform_products  transform_inventory  transform_sales
                └─────────┬─────────┘
                          ▼
                   load_staging
                          │
                          ▼
                 refresh_analytics
                          │
                          ▼
                 register_processed_files
                          │
                          ▼
                 register_pipeline_success
```

Extraction tasks can run in parallel. Transformations begin only when all required data, including exchange rates, is available.

The DAG must configure retries, timeouts, logs, error callbacks, and parameters for running a specific date or a backfill.

Complex business logic must not live inside the DAG; it must be located in `src`.

## 10. Analytics Layer

### `analytics.sales_by_country`

Aggregates by date and country:

- number of orders;
- units sold;
- revenue in the original currency;
- revenue in the standard currency.

### `analytics.sales_by_brand`

Aggregates by date and brand:

- units sold;
- revenue;
- number of products;
- average order value.

### `analytics.daily_revenue`

Aggregates by day:

- total revenue;
- orders;
- units;
- average order value;
- active countries and brands.

### `analytics.inventory_status`

Calculates the following by product, warehouse, and date:

- current stock;
- reorder level;
- inventory value;
- status.

Suggested statuses:

```text
in_stock
low_stock
out_of_stock
unknown
```

### `analytics.top_products`

Generates rankings by period with:

- product;
- brand;
- units;
- revenue;
- position;
- primary country.

Aggregates must be built from `staging`, not directly from CSV files. Analytics totals must be checked against staging.

## 11. Monitoring

### `monitoring.pipeline_runs`

Must record:

- `pipeline_run_id`;
- Airflow DAG and run;
- logical date;
- start and end times;
- duration;
- status;
- detected and processed files;
- rows read and loaded;
- removed duplicates;
- rejected rows;
- number of errors;
- final message.

### `monitoring.pipeline_tasks`

Records the following for each task:

- start and end times;
- duration;
- status;
- processed rows;
- error.

### `monitoring.data_quality_checks`

Records:

- table;
- rule;
- result;
- evaluated rows;
- valid and invalid rows;
- severity;
- timestamp.

### `monitoring.pipeline_errors`

Preserves the task, file, row, message, timestamp, and `pipeline_run_id`.

The system must be able to answer how many files arrived, how many were processed, how many rows were rejected, how long each stage took, and which was the last successful run.

## 12. Docker Compose

### `postgres`

Provides persistence for Airflow and the warehouse. For the portfolio, a PostgreSQL service with logical separation between the Airflow metadata database and the project database may be used. In a real company, separate instances would be preferred because of their different lifecycles and permission requirements.

### `airflow-webserver`

Provides a web interface for inspecting DAGs, tasks, runs, and logs. It must not contain transformation logic.

### `airflow-scheduler`

Schedules DAGs, evaluates dependencies, executes tasks, and manages retries.

### `python-etl`

A container with Python, Pandas, a PostgreSQL client, and an HTTP client. It contains reusable extraction, validation, transformation, loading, and monitoring logic.

Services must communicate through the private Docker Compose network and use service names as hostnames. Data, files, logs, and the database must persist through volumes.

## 13. Repository Structure

```text
tea-data-platform/
│
├── dags/
│   ├── tea_daily_etl.py
│   └── README.md
│
├── src/
│   └── tea_pipeline/
│       ├── extraction/
│       ├── validation/
│       ├── transformation/
│       ├── loading/
│       ├── monitoring/
│       ├── configuration/
│       └── utils/
│
├── sql/
│   ├── schemas/
│   ├── raw/
│   ├── staging/
│   ├── analytics/
│   └── monitoring/
│
├── data/
│   ├── incoming/
│   ├── processed/
│   ├── rejected/
│   └── samples/
│
├── tests/
│   ├── unit/
│   ├── integration/
│   └── data_quality/
│
├── docker/
│   ├── airflow/
│   ├── postgres/
│   └── python-etl/
│
├── logs/
├── config/
│   ├── source_contracts/
│   └── pipeline_config/
├── docs/
│   ├── architecture.md
│   ├── data_dictionary.md
│   ├── data_flow.md
│   └── operational_runbook.md
├── docker-compose.yml
├── Dockerfile
├── requirements.txt
├── .env.example
├── .gitignore
└── README.md
```

### Responsibilities

- `dags/`: orchestration only.
- `src/`: reusable pipeline logic.
- `sql/`: versioned schemas, tables, indexes, views, and refreshes.
- `data/samples/`: small datasets for development and testing.
- `tests/`: unit, integration, and data quality tests.
- `docker/`: image and service-specific configurations.
- `config/`: source contracts and declarative configuration.
- `docs/`: architecture, data dictionary, data flow, and operational runbook.

## 14. Production Principles

- `raw` is auditable and ideally immutable.
- The pipeline is idempotent.
- Layers are separated by responsibility.
- Airflow orchestrates; Python transforms; SQL models and aggregates.
- Original data is not overwritten.
- Loads run within transactions.
- PostgreSQL keys and constraints protect against duplicates.
- Analytics is not updated when critical staging errors occur.
- Reprocessing is explicit and traceable.
- Credentials are managed through environment variables and are not committed to version control.
- Data quality rules and source contracts must be documented.

## 15. Future Implementation Plan

The project should be implemented in phases:

1. Prepare the repository, Docker, and PostgreSQL.
2. Create schemas and monitoring tables.
3. Create source contracts and sample data.
4. Implement file detection and incremental metadata.
5. Implement extraction into raw.
6. Implement validations and rejected-record tracking.
7. Implement transformations into staging.
8. Implement currency conversions.
9. Implement facts, dimensions, and analytics.
10. Integrate everything with Airflow.
11. Add tests, retries, recovery, and documentation.
12. Validate a successful run, a failed run, and an idempotent reprocessing run.

The next implementation step should be selected only after reviewing this document and agreeing on the appropriate phase. Do not generate implementation code without explicitly requesting it.
