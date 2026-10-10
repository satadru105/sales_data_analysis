
# Week 3 Internship Project: Sales Data Analysis
# Purpose: Clean sales data, calculate metrics, and generate a report.

from pathlib import Path
from html import escape
import pandas as pd

# Keep project files in the same folder as this Python script.
BASE_DIR = Path(__file__).resolve().parent
INPUT_FILE = BASE_DIR / "sales_data.csv"
REPORT_FILE = BASE_DIR / "analysis_report.md"
CHART_FILE = BASE_DIR / "sales_by_product.svg"

# Step 1: Load the CSV dataset.
try:
    df = pd.read_csv(INPUT_FILE)
except FileNotFoundError:
    print("Error: sales_data.csv was not found.")
    raise SystemExit(1)

# Accept either the CSV's Price column or the more explicit Unit_Price name.
if "Unit_Price" not in df.columns and "Price" in df.columns:
    df = df.rename(columns={"Price": "Unit_Price"})

# Step 2: Check that the required columns exist.
required_columns = ["Product", "Quantity", "Unit_Price"]

missing_columns = [
    col for col in required_columns if col not in df.columns
]

if missing_columns:
    print(f"Missing required columns: {missing_columns}")
    raise SystemExit(1)

# Step 3: Explore the original dataset.
print("\n===== ORIGINAL DATA =====")
print(df.head())
print("\nDataset shape:", df.shape)
print("\nColumn data types:\n", df.dtypes)
print("\nMissing values:\n", df.isnull().sum())

original_rows = len(df)

# Step 4: Remove exact duplicate rows.
df = df.drop_duplicates().copy()
duplicates_removed = original_rows - len(df)

# Step 5: Convert numeric columns safely.
for col in ["Quantity", "Unit_Price"]:
    df[col] = pd.to_numeric(df[col], errors="coerce")

# Convert date values when the column exists.
if "Date" in df.columns:
    df["Date"] = pd.to_datetime(df["Date"], errors="coerce")

# Step 6: Handle missing and invalid data.
# Product names cannot be used for product-level analysis if missing.
df["Product"] = df["Product"].astype("string").str.strip()
df["Product"] = df["Product"].replace("", pd.NA)
missing_products = int(df["Product"].isna().sum())
df = df.dropna(subset=["Product"]).copy()

# Missing and non-numeric essential values cannot be analyzed.
missing_quantities = int(df["Quantity"].isna().sum())
missing_prices = int(df["Unit_Price"].isna().sum())
df = df.dropna(subset=["Quantity", "Unit_Price"]).copy()

# A sale requires a positive quantity and a non-negative unit price.
invalid_sales = (df["Quantity"] <= 0) | (df["Unit_Price"] < 0)
invalid_sales_removed = int(invalid_sales.sum())
df = df.loc[~invalid_sales].copy()

# Calculate revenue from quantity and price to ensure consistency.
df["Total_Sales"] = df["Quantity"] * df["Unit_Price"]

# Stop if there is no valid data to analyze.
if df.empty:
    print("No valid sales records remain after cleaning.")
    raise SystemExit(1)

# Step 7: Calculate sales metrics.
total_revenue = df["Total_Sales"].sum()
total_units = df["Quantity"].sum()
average_order_value = df["Total_Sales"].mean()
highest_sale = df["Total_Sales"].max()
lowest_sale = df["Total_Sales"].min()

# Find the product with the highest total revenue.
product_sales = (
    df.groupby("Product")["Total_Sales"]
    .sum()
    .sort_values(ascending=False)
)

best_product = product_sales.index[0]
best_product_revenue = product_sales.iloc[0]

# Find the product with the highest quantity sold.
product_units = df.groupby("Product")["Quantity"].sum()
most_units_product = product_units.idxmax()
most_units = product_units.max()

# Step 8: Display the results.
print("\n===== SALES ANALYSIS RESULTS =====")
print(f"Valid sales records: {len(df)}")
print(f"Duplicate rows removed: {duplicates_removed}")
print(f"Total revenue: Rs. {total_revenue:,.2f}")
print(f"Total units sold: {total_units:,.0f}")
print(f"Average sale value: Rs. {average_order_value:,.2f}")
print(f"Highest sale: Rs. {highest_sale:,.2f}")
print(f"Lowest sale: Rs. {lowest_sale:,.2f}")
print(f"Top product by revenue: {best_product}")
print(f"Top product revenue: Rs. {best_product_revenue:,.2f}")
print(f"Most units sold: {most_units_product} ({most_units:,.0f})")

print("\n===== REVENUE BY PRODUCT =====")
print(product_sales.to_string())

# Step 9: Create a product revenue chart as a standalone SVG.
chart_width = 900
left_margin = 180
right_margin = 150
top_margin = 90
row_height = 44
chart_height = top_margin + row_height * len(product_sales) + 35
plot_width = chart_width - left_margin - right_margin
max_revenue = float(product_sales.max())
chart_rows = []

for index, (product, revenue) in enumerate(product_sales.items()):
    y = top_margin + index * row_height
    bar_width = plot_width * float(revenue) / max_revenue if max_revenue else 0
    chart_rows.append(
        f"""  <text x="{left_margin - 12}" y="{y + 21}" text-anchor="end"
        class="label">{escape(str(product))}</text>
  <rect x="{left_margin}" y="{y}" width="{bar_width:.2f}" height="28"
        rx="4" class="bar" />
  <text x="{left_margin + bar_width + 8:.2f}" y="{y + 20}"
        class="value">Rs. {float(revenue):,.2f}</text>"""
    )

chart = f"""<svg xmlns="http://www.w3.org/2000/svg" width="{chart_width}"
     height="{chart_height}" viewBox="0 0 {chart_width} {chart_height}"
     role="img" aria-labelledby="chart-title chart-description">
  <title id="chart-title">Revenue by Product</title>
  <desc id="chart-description">Horizontal bar chart of cleaned sales revenue by product.</desc>
  <style>
    text {{ font-family: Arial, sans-serif; fill: #243247; }}
    .title {{ font-size: 24px; font-weight: bold; }}
    .label, .value {{ font-size: 14px; }}
    .bar {{ fill: #2878b5; }}
    .axis {{ stroke: #c8d1dc; stroke-width: 1; }}
  </style>
  <rect width="100%" height="100%" fill="#ffffff" />
  <text x="{left_margin}" y="42" class="title">Revenue by Product</text>
  <line x1="{left_margin}" y1="{top_margin - 12}"
        x2="{left_margin}" y2="{chart_height - 18}" class="axis" />
{chr(10).join(chart_rows)}
</svg>
"""
CHART_FILE.write_text(chart, encoding="utf-8")

# Step 10: Create a formatted Markdown report.
report = f"""# Sales Data Analysis Report

## 1. Project Overview

This project uses Python and Pandas to clean and analyze
a sample sales dataset and identify useful business insights.

## 2. Data Cleaning

- Original rows: {original_rows}
- Exact duplicate rows removed: {duplicates_removed}
- Valid rows analyzed: {len(df)}
- Rows with missing product names excluded: {missing_products}
- Missing or non-numeric quantity values: {missing_quantities}
- Missing or non-numeric unit price values: {missing_prices}
- Rows with non-positive quantities or negative prices excluded: {invalid_sales_removed}
- Revenue was recalculated using Quantity × Unit_Price.

## 3. Key Performance Metrics

| Metric | Result |
|---|---:|
| Total revenue | Rs. {total_revenue:,.2f} |
| Total units sold | {total_units:,.0f} |
| Average sale value | Rs. {average_order_value:,.2f} |
| Highest sale | Rs. {highest_sale:,.2f} |
| Lowest sale | Rs. {lowest_sale:,.2f} |
| Valid sales records | {len(df)} |
| Duplicate rows removed | {duplicates_removed} |

## 4. Product Performance

**Top product by revenue:** {best_product} (Rs. {best_product_revenue:,.2f})

**Best-selling product by quantity:** {most_units_product}

**Units sold:** {most_units:,.0f}

### Revenue by Product

| Product | Revenue (Rs.) |
|---|---:|
{chr(10).join(f"| {product} | {revenue:,.2f} |" for product, revenue in product_sales.items())}

![Revenue by product](sales_by_product.svg)

## 5. Business Insights

- Total recorded revenue is Rs. {total_revenue:,.2f}.
- {best_product} generated the highest product revenue.
- {most_units_product} had the highest total quantity sold.
- Average sale value was Rs. {average_order_value:,.2f}.

## 6. Conclusion

Pandas helped load, clean, group, and summarize sales records.
These results can help a business understand product performance
and make more informed inventory and sales decisions.

## 7. Tools Used

- Python
- Pandas
- CSV
- Markdown

## 8. Validation

The report and chart were generated from the cleaned dataset.
Revenue was recalculated from quantity multiplied by unit price.
"""

# Step 11: Save the report.
REPORT_FILE.write_text(report, encoding="utf-8")

print("\nReport and product revenue chart saved to the project directory.")
