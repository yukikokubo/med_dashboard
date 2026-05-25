from __future__ import annotations

import csv
import random
from datetime import date, timedelta
from pathlib import Path


OUTPUT_DIR = Path(__file__).parent / "data"
SEED = 20260525


PRODUCTS = [
    {
        "ProductKey": "P001",
        "ProductName": "Diabetra",
        "TherapeuticArea": "糖尿病",
        "LaunchDate": "2018-06-01",
        "ProductCategory": "主力品",
        "UnitPriceJPY": 42000,
        "BaseUnits": 940,
        "Trend": 0.002,
    },
    {
        "ProductKey": "P002",
        "ProductName": "Oncora",
        "TherapeuticArea": "腫瘍",
        "LaunchDate": "2024-07-01",
        "ProductCategory": "新薬",
        "UnitPriceJPY": 178000,
        "BaseUnits": 105,
        "Trend": 0.040,
    },
    {
        "ProductKey": "P003",
        "ProductName": "Cardivex",
        "TherapeuticArea": "循環器",
        "LaunchDate": "2011-10-01",
        "ProductCategory": "長期収載品",
        "UnitPriceJPY": 27000,
        "BaseUnits": 1080,
        "Trend": -0.014,
    },
    {
        "ProductKey": "P004",
        "ProductName": "Respira",
        "TherapeuticArea": "呼吸器",
        "LaunchDate": "2020-02-01",
        "ProductCategory": "重点品",
        "UnitPriceJPY": 35000,
        "BaseUnits": 560,
        "Trend": 0.006,
    },
    {
        "ProductKey": "P005",
        "ProductName": "Immunex",
        "TherapeuticArea": "免疫疾患",
        "LaunchDate": "2022-09-01",
        "ProductCategory": "成長品",
        "UnitPriceJPY": 112000,
        "BaseUnits": 135,
        "Trend": 0.021,
    },
]

REGIONS = [
    ("R01", "北海道", 0.05, 1.01),
    ("R02", "東北", 0.07, 1.02),
    ("R03", "関東", 0.31, 1.08),
    ("R04", "中部", 0.15, 1.03),
    ("R05", "関西", 0.18, 0.94),
    ("R06", "中国", 0.07, 0.98),
    ("R07", "四国", 0.05, 0.96),
    ("R08", "九州", 0.12, 0.92),
]


def iter_dates(start: date, end: date):
    current = start
    while current <= end:
        yield current
        current += timedelta(days=1)


def iter_months(start: date, end: date):
    current = start
    while current <= end:
        yield current
        current = date(current.year + (current.month == 12), current.month % 12 + 1, 1)


def date_key(value: date) -> int:
    return int(value.strftime("%Y%m%d"))


def fiscal_values(value: date) -> tuple[int, int]:
    fiscal_year = value.year if value.month >= 4 else value.year - 1
    fiscal_month = (value.month - 4) % 12 + 1
    return fiscal_year, fiscal_month


def build_date_dimension() -> list[dict[str, object]]:
    rows = []
    for value in iter_dates(date(2023, 4, 1), date(2026, 3, 31)):
        fiscal_year, fiscal_month = fiscal_values(value)
        rows.append(
            {
                "DateKey": date_key(value),
                "Date": value.isoformat(),
                "CalendarYear": value.year,
                "MonthNumber": value.month,
                "MonthNameJP": f"{value.month}月",
                "YearMonth": value.strftime("%Y-%m"),
                "FiscalYear": fiscal_year,
                "FiscalYearLabel": f"FY{fiscal_year}",
                "FiscalQuarter": f"Q{(fiscal_month - 1) // 3 + 1}",
                "FiscalMonthNumber": fiscal_month,
                "IsMonthStart": value.day == 1,
            }
        )
    return rows


def build_product_dimension() -> list[dict[str, object]]:
    fields = ["ProductKey", "ProductName", "TherapeuticArea", "LaunchDate", "ProductCategory", "UnitPriceJPY"]
    return [{field: product[field] for field in fields} for product in PRODUCTS]


def build_region_dimension() -> list[dict[str, object]]:
    return [
        {"RegionKey": key, "RegionName": name, "RegionSortOrder": index + 1}
        for index, (key, name, _, _) in enumerate(REGIONS)
    ]


def seasonal_factor(product_name: str, month: int) -> float:
    if product_name == "Respira":
        return {1: 1.52, 2: 1.38, 3: 1.14, 10: 1.18, 11: 1.36, 12: 1.58}.get(month, 0.78)
    return 1.03 if month in (3, 9) else 1.0


def month_difference(later: date, earlier: date) -> int:
    return (later.year - earlier.year) * 12 + later.month - earlier.month


def build_sales_fact() -> list[dict[str, object]]:
    rng = random.Random(SEED)
    rows = []
    for month_index, month in enumerate(iter_months(date(2023, 4, 1), date(2026, 3, 1))):
        for product in PRODUCTS:
            launch_date = date.fromisoformat(str(product["LaunchDate"]))
            if month < launch_date:
                continue
            months_since_launch = max(0, month_difference(month, launch_date))
            trend_index = months_since_launch if product["ProductName"] == "Oncora" else month_index
            growth = (1 + float(product["Trend"])) ** trend_index
            seasonality = seasonal_factor(str(product["ProductName"]), month.month)

            for region_key, _, region_share, performance in REGIONS:
                base_units = float(product["BaseUnits"]) * region_share * growth * seasonality
                budget_growth = 1 + max(float(product["Trend"]), 0.004) * trend_index
                budget_units = float(product["BaseUnits"]) * region_share * budget_growth * seasonality

                if product["ProductName"] == "Oncora" and region_key in ("R03", "R04"):
                    base_units *= 1.13
                if product["ProductName"] == "Cardivex" and region_key in ("R05", "R08"):
                    base_units *= 0.93

                units = max(1, round(base_units * performance * rng.normalvariate(1.0, 0.045)))
                planned_units = max(1, round(budget_units * rng.normalvariate(1.0, 0.018)))
                unit_price = int(product["UnitPriceJPY"])
                rows.append(
                    {
                        "SalesDateKey": date_key(month),
                        "ProductKey": product["ProductKey"],
                        "RegionKey": region_key,
                        "SalesAmountJPY": units * unit_price,
                        "BudgetAmountJPY": planned_units * unit_price,
                        "UnitQuantity": units,
                        "BudgetUnitQuantity": planned_units,
                    }
                )
    return rows


def write_csv(rows: list[dict[str, object]], filename: str) -> None:
    OUTPUT_DIR.mkdir(exist_ok=True)
    with (OUTPUT_DIR / filename).open("w", encoding="utf-8-sig", newline="") as output_file:
        writer = csv.DictWriter(output_file, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    write_csv(build_date_dimension(), "dim_date.csv")
    write_csv(build_product_dimension(), "dim_product.csv")
    write_csv(build_region_dimension(), "dim_region.csv")
    write_csv(build_sales_fact(), "fact_sales.csv")
    print(f"Created Power BI sample data in {OUTPUT_DIR.resolve()}")


if __name__ == "__main__":
    main()
