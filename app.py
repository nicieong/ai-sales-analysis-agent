import streamlit as st
import pandas as pd

from sales_analysis import (
    load_sales_data,
    get_sales_performance,
    get_daily_sales_trend,
    get_sales_by_product,
)

from inventory_analysis import analyze_inventory

from agent import ask_agent


# Page configuration
st.set_page_config(
    page_title="AI Sales & Inventory Analyst",
    page_icon="📊",
    layout="wide",
)


# Dashboard title
st.title("AI Sales & Inventory Analyst")
st.caption("Sales Performance Dashboard")

# AI Analyst
st.divider()
st.subheader("AI Analyst")

with st.form("ai_analyst_form"):
    question = st.text_input(
        "Ask a question about sales or inventory",
        placeholder="e.g. What are the total sales?"
    )

    submitted = st.form_submit_button("Ask AI")

if submitted:
    if not question.strip():
        st.warning("Please enter a question.")
    else:
        with st.spinner("AI is analysing your question..."):
            try:
                answer = ask_agent(question)
                st.markdown("**AI Answer**")
                st.write(answer)
            except Exception as error:
                st.error(f"Unable to get an AI response: {error}")


try:
    # Load sales data
    sales_df = load_sales_data("data/sales.csv")

    # Determine the available data period
    sales_df["sales_date"] = pd.to_datetime(
        sales_df["sales_date"]
    ).dt.normalize()

    available_start = sales_df["sales_date"].min().date()
    available_end = sales_df["sales_date"].max().date()

    # Date range selection
    st.subheader("Sales KPI Overview")

    date_mode = st.radio(
        "Select Reporting Period",
        [
            "Last 14 Full Days",
            "Last 30 Full Days",
            "Custom Date Range",
        ],
        index=1,
        horizontal=True,
    )

    if date_mode == "Last 14 Full Days":
        requested_start = max(
            available_start,
            (pd.Timestamp(available_end) - pd.Timedelta(days=13)).date(),
        )
        requested_end = available_end

    elif date_mode == "Last 30 Full Days":
        requested_start = max(
            available_start,
            (pd.Timestamp(available_end) - pd.Timedelta(days=29)).date(),
        )
        requested_end = available_end

    else:
        default_start = max(
            available_start,
            (pd.Timestamp(available_end) - pd.Timedelta(days=29)).date(),
        )

        selected_dates = st.date_input(
            "Custom Date Range",
            value=(default_start, available_end),
        )

        if not isinstance(selected_dates, (tuple, list)) or len(selected_dates) != 2:
            st.info("Please select both a start date and an end date.")
            st.stop()

        requested_start, requested_end = selected_dates

    # Validate the requested date range for every reporting mode
    if requested_start > requested_end:
        st.error("Start date must not be later than end date.")
        st.stop()

    requested_days = (requested_end - requested_start).days + 1

    if requested_days > 365:
        st.error(
            f"The selected date range covers {requested_days} calendar days. "
            "The maximum reporting period is 365 days. "
            "Please shorten the date range. Contact your DBA if you need "
            "sales data beyond the available reporting period."
        )
        st.stop()

    # Determine the actual overlap with available sales data
    actual_start = max(requested_start, available_start)
    actual_end = min(requested_end, available_end)

    if actual_start > actual_end:
        st.warning(
            f"No sales data is available between {requested_start} and "
            f"{requested_end}. Sales KPIs and charts cannot be calculated "
            "for this period. Contact your DBA if you need older sales data."
        )
        st.stop()

    # Use actual available dates for all sales calculations
    start_date = actual_start
    end_date = actual_end
    coverage_days = (actual_end - actual_start).days + 1

    st.caption(
        f"Requested Period: {requested_start} to {requested_end} "
        f"({requested_days} calendar days)"
    )

    st.caption(
        f"Actual Data Coverage: {actual_start} to {actual_end} "
        f"({coverage_days} calendar days)"
    )

    if coverage_days < requested_days:
        st.warning(
            f"Partial data coverage: {coverage_days} of {requested_days} "
            "requested calendar days are available. KPIs and charts use "
            "only the available data. Contact your DBA if you need older "
            "sales data."
        )

    # Calculate KPIs using the actual available date range
    kpis = get_sales_performance(
        sales_df,
        start_date=start_date,
        end_date=end_date,
    )

    # Display four KPI cards
    col1, col2, col3, col4 = st.columns(4)

    col1.metric("Total Sales", f"{kpis['total_sales']:,.2f}")
    col2.metric("Total Quantity", f"{kpis['total_quantity']:,}")
    col3.metric("Transaction Count", f"{kpis['transaction_count']:,}")
    col4.metric("Average Daily Sales", f"{kpis['average_daily_sales']:,.2f}")

    st.divider()
    st.subheader("Daily Sales Trend")

    daily_trend = get_daily_sales_trend(
        sales_df,
        start_date=start_date,
        end_date=end_date,
    )

    chart_data = daily_trend.set_index("sales_date")[["sales_amount"]]

    st.line_chart(
        chart_data,
        y="sales_amount",
        x_label="Date",
        y_label="Sales Amount",
    )

    st.divider()
    st.subheader("Top 5 Products by Sales")

    product_sales = get_sales_by_product(
        sales_df,
        start_date=start_date,
        end_date=end_date,
    )

    top_products = product_sales.head(5).copy()

    if top_products.empty:
        st.info("No product sales data available for this period.")
    else:
        chart_data = top_products.set_index("product_name")[["total_sales"]]

        st.bar_chart(
            chart_data,
            horizontal=True,
            x_label="Sales Amount",
            y_label="Product",
        )

        st.dataframe(
            top_products[
                [
                    "product_id",
                    "product_name",
                    "category",
                    "total_qty",
                    "total_sales",
                    "sales_contribution_pct",
                ]
            ].rename(
                columns={
                    "product_id": "Product ID",
                    "product_name": "Product",
                    "category": "Category",
                    "total_qty": "Total Quantity",
                    "total_sales": "Total Sales",
                    "sales_contribution_pct": "Sales Contribution (%)",
                }
            ),
            hide_index=True,
            use_container_width=True,
        )

    st.divider()
    st.header("Inventory Risk Overview")

    inventory_df = analyze_inventory()

    total_products = len(inventory_df)
    reorder_count = (
        inventory_df["inventory_status"] == "Reorder Required"
    ).sum()
    estimable_cover_count = (
        inventory_df["estimated_stock_cover_days"].notna()
    ).sum()

    col1, col2, col3 = st.columns(3)
    col1.metric("Total Products", f"{total_products:,}")
    col2.metric("Reorder Required", f"{reorder_count:,}")
    col3.metric("Estimable Stock Cover", f"{estimable_cover_count:,}")

    st.caption(
        "Average daily sales is based on the last 90 calendar days. "
        "Promotional effects are not yet adjusted."
    )

    st.divider()
    st.subheader("Sales & Inventory Comparison")

    # Get sales data for the selected reporting period
    comparison_sales = get_sales_by_product(
        sales_df,
        start_date=start_date,
        end_date=end_date,
    )

    # Keep the inventory baseline based on the last 90 days
    comparison_inventory = analyze_inventory()

    # Match sales and inventory records by product_id
    comparison_df = comparison_sales.merge(
        comparison_inventory[
            [
                "product_id",
                "stock_on_hand",
                "average_daily_sales",
                "estimated_stock_cover_days",
            ]
        ],
        on="product_id",
        how="left",
        validate="one_to_one",
    )

    st.caption(
        "Sales figures follow the selected reporting period. "
        "Average daily sales and stock cover are based on "
        "the last 90 calendar days."
    )

    comparison_display = comparison_df[
        [
            "product_id",
            "product_name",
            "total_qty",
            "total_sales",
            "stock_on_hand",
            "average_daily_sales",
            "estimated_stock_cover_days",
        ]
    ].rename(
        columns={
            "product_id": "Product ID",
            "product_name": "Product",
            "total_qty": "Sales Qty (Selected Period)",
            "total_sales": "Sales Amount (Selected Period)",
            "stock_on_hand": "Stock on Hand",
            "average_daily_sales": "Average Daily Sales (Last 90 Days)",
            "estimated_stock_cover_days": "Stock Cover (Days)",
        }
    )

    comparison_display = comparison_display.sort_values(
        by="Stock Cover (Days)",
        ascending=True,
        na_position="last",
    )

    st.dataframe(
        comparison_display,
        hide_index=True,
        use_container_width=True,
    )

    st.subheader("Inventory Risk Details")

    inventory_display = inventory_df.copy()

    # Show products requiring reorder first
    inventory_display["_risk_priority"] = (
        inventory_display["inventory_status"] != "Reorder Required"
    )

    # Sort by risk priority, then lowest stock cover
    inventory_display = inventory_display.sort_values(
        by=["_risk_priority", "estimated_stock_cover_days"],
        ascending=[True, True],
        na_position="last",
    ).drop(columns="_risk_priority")

    inventory_display = inventory_display[
        [
            "product_id",
            "product_name",
            "stock_on_hand",
            "reorder_level",
            "average_daily_sales",
            "inventory_status",
            "estimated_stock_cover_days",
        ]
    ].rename(
        columns={
            "product_id": "Product ID",
            "product_name": "Product",
            "stock_on_hand": "Stock on Hand",
            "reorder_level": "Reorder Level",
            "average_daily_sales": "Average Daily Sales (Last 90 Days)",
            "inventory_status": "Inventory Status",
            "estimated_stock_cover_days": "Estimated Stock Cover (Days)",
        }
    )

    st.dataframe(
        inventory_display,
        hide_index=True,
        use_container_width=True,
    )


except (FileNotFoundError, ValueError, KeyError) as error:
    st.error(f"Unable to load sales dashboard: {error}")