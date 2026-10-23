import streamlit as st
import pandas as pd
from datetime import timedelta

from sales_analysis import (
    load_sales_data,
    get_month_period_analysis,
    get_weekday_weekend_analysis,
    get_weekday_sales_analysis,
)


st.set_page_config(
    page_title="Supplementary Sales Analysis",
    page_icon="📊",
    layout="wide",
)

st.title("Supplementary Sales Analysis")
st.caption("Additional analysis of sales patterns across dates and weekdays.")

st.header("1. Month Period Analysis")

try:
    sales_df = load_sales_data()

    # Ensure sales_date is in datetime format
    sales_df["sales_date"] = pd.to_datetime(
        sales_df["sales_date"],
        errors="raise",
    )

    # Determine the available sales date range
    min_date = sales_df["sales_date"].min().date()
    max_date = sales_df["sales_date"].max().date()
    available_days = (max_date - min_date).days + 1

    # Date range controls
    period_option = st.radio(
        "Select Analysis Period",
        ["Last 14 Full Days", "Last 30 Full Days", "Custom Date Range"],
        index=1,
        horizontal=True,
        key="supplementary_period_option",
    )

    if period_option == "Last 14 Full Days":
        end_date = max_date
        start_date = end_date - timedelta(days=13)

    elif period_option == "Last 30 Full Days":
        end_date = max_date
        start_date = end_date - timedelta(days=29)

    else:
        default_start = max(
            min_date,
            max_date - timedelta(days=29),
        )

        selected_dates = st.date_input(
            "Select Date Range",
            value=(default_start, max_date),
            key="supplementary_custom_dates",
        )

        if not isinstance(selected_dates, (tuple, list)) or len(selected_dates) != 2:
            st.info("Please select both a start date and an end date.")
            st.stop()

        start_date, end_date = selected_dates

        if start_date > end_date:
            st.error("Start date must not be later than end date.")
            st.stop()

    MAX_ANALYSIS_DAYS = 365

    requested_days = (end_date - start_date).days + 1

    if requested_days > MAX_ANALYSIS_DAYS:
        st.error(
            f"The selected period is {requested_days} calendar days. "
            f"Please select no more than {MAX_ANALYSIS_DAYS} calendar days."
        )
        st.stop()

    # Determine the actual overlap with available sales data
    actual_start = max(start_date, min_date)
    actual_end = min(end_date, max_date)

    if actual_start > actual_end:
        st.error(
            "No sales data is available within the requested date range. "
            f"Available sales data runs from {min_date} to {max_date}."
        )
        st.stop()

    actual_days = (actual_end - actual_start).days + 1

    st.caption(
        f"Requested Period: {start_date} to {end_date}"
    )

    st.caption(
        f"Actual Data Coverage: {actual_start} to {actual_end} "
        f"({actual_days} calendar days)"
    )

    if actual_start != start_date or actual_end != end_date:
        st.warning(
            "The requested period extends beyond the available sales data. "
            "The analyses below use only the overlapping dates shown in "
            "Actual Data Coverage."
        )

    # Run analysis using the existing analysis function
    period_df = get_month_period_analysis(
        sales_df,
        start_date=actual_start,
        end_date=actual_end,
    )

    if period_df.empty:
        st.warning("No sales data is available for the selected period.")
    else:
        st.caption(
            f"Analysis period: {start_date} to {end_date} "
            f"({(end_date - start_date).days + 1} calendar days)"
        )

        # Summary table
        display_columns = [
            "month_period",
            "days",
            "avg_daily_sales",
            "avg_daily_qty",
            "vs_overall_avg_pct",
        ]

        display_df = period_df[display_columns].copy()

        display_df = display_df.rename(
            columns={
                "month_period": "Period",
                "days": "Days",
                "avg_daily_sales": "Average Daily Sales",
                "avg_daily_qty": "Average Daily Quantity",
                "vs_overall_avg_pct": "Vs Overall Average (%)",
            }
        )

        st.dataframe(
            display_df,
            use_container_width=True,
            hide_index=True,
            column_config={
                "Days": st.column_config.NumberColumn(format="%d"),
                "Average Daily Sales": st.column_config.NumberColumn(
                    format="$%.2f"
                ),
                "Average Daily Quantity": st.column_config.NumberColumn(
                    format="%.2f"
                ),
                "Vs Overall Average (%)": st.column_config.NumberColumn(
                    format="%.2f%%"
                ),
            },
        )

        # Chart
        chart_df = display_df.set_index("Period")[
            ["Average Daily Sales"]
        ]

        st.subheader("Average Daily Sales by Month Period")
        st.bar_chart(chart_df)

except Exception as e:
    st.error(f"Unable to load Month Period Analysis: {e}")


st.divider()

st.header("2. Weekday vs Weekend")

try:
    comparison_df = get_weekday_weekend_analysis(
        sales_df,
        start_date=actual_start,
        end_date=actual_end,
    )

    if comparison_df.empty:
        st.warning("No sales data is available for the selected period.")
    else:
        st.caption(
            f"Analysis period: {start_date} to {end_date}"
        )

        display_columns = [
            "day_type",
            "days",
            "total_sales",
            "avg_daily_sales",
            "avg_daily_qty",
            "total_transactions",
            "avg_daily_transactions",
            "avg_transaction_value",
        ]

        display_df = comparison_df[display_columns].copy()

        display_df = display_df.rename(
            columns={
                "day_type": "Day Type",
                "days": "Days",
                "total_sales": "Total Sales",
                "avg_daily_sales": "Average Daily Sales",
                "avg_daily_qty": "Average Daily Quantity",
                "total_transactions": "Total Transactions",
                "avg_daily_transactions": "Average Daily Transactions",
                "avg_transaction_value": "Average Transaction Value",
            }
        )

        st.dataframe(
            display_df,
            use_container_width=True,
            hide_index=True,
            column_config={
                "Days": st.column_config.NumberColumn(format="%d"),
                "Total Sales": st.column_config.NumberColumn(format="$%.2f"),
                "Average Daily Sales": st.column_config.NumberColumn(format="$%.2f"),
                "Average Daily Quantity": st.column_config.NumberColumn(format="%.2f"),
                "Total Transactions": st.column_config.NumberColumn(format="%d"),
                "Average Daily Transactions": st.column_config.NumberColumn(format="%.2f"),
                "Average Transaction Value": st.column_config.NumberColumn(format="$%.2f"),
            },
        )

        st.subheader("Average Daily Sales: Weekday vs Weekend")

        chart_df = display_df.set_index("Day Type")[
            ["Average Daily Sales"]
        ]

        st.bar_chart(chart_df)

except Exception as e:
    st.error(f"Unable to load Weekday vs Weekend Analysis: {e}")


st.divider()

st.header("3. Weekday Sales Analysis")

try:
    weekday_df = get_weekday_sales_analysis(
        sales_df,
        start_date=actual_start,
        end_date=actual_end,
    )

    if weekday_df.empty:
        st.warning("No sales data is available for the selected period.")
    else:
        st.caption(
            f"Analysis period: {start_date} to {end_date}"
        )

        display_columns = [
            "day_of_week",
            "days",
            "avg_daily_sales",
            "total_sales",
            "total_transactions",
            "avg_daily_transactions",
            "avg_transaction_value",
            "vs_overall_avg_pct",
        ]

        display_df = weekday_df[display_columns].copy()

        display_df = display_df.rename(
            columns={
                "day_of_week": "Weekday",
                "days": "Days",
                "avg_daily_sales": "Average Daily Sales",
                "total_sales": "Total Sales",
                "total_transactions": "Total Transactions",
                "avg_daily_transactions": "Average Daily Transactions",
                "avg_transaction_value": "Average Transaction Value",
                "vs_overall_avg_pct": "Vs Overall Average (%)",
            }
        )

        st.dataframe(
            display_df,
            use_container_width=True,
            hide_index=True,
            column_config={
                "Days": st.column_config.NumberColumn(format="%d"),
                "Average Daily Sales": st.column_config.NumberColumn(format="$%.2f"),
                "Total Sales": st.column_config.NumberColumn(format="$%.2f"),
                "Total Transactions": st.column_config.NumberColumn(format="%d"),
                "Average Daily Transactions": st.column_config.NumberColumn(format="%.2f"),
                "Average Transaction Value": st.column_config.NumberColumn(format="$%.2f"),
                "Vs Overall Average (%)": st.column_config.NumberColumn(format="%.2f%%"),
            },
        )

        st.subheader("Average Daily Sales by Weekday")

        chart_df = display_df.set_index("Weekday")[
            ["Average Daily Sales"]
        ]

        st.bar_chart(chart_df)

except Exception as e:
    st.error(f"Unable to load Weekday Sales Analysis: {e}")