import pandas as pd


def filter_sales_by_date(df, start_date=None, end_date=None):
    """Filter sales records by an inclusive, validated date range."""
    df = df.copy()
    df["sales_date"] = pd.to_datetime(
        df["sales_date"]
    ).dt.normalize()

    available_start = df["sales_date"].min()
    available_end = df["sales_date"].max()

    if pd.isna(available_start) or pd.isna(available_end):
        raise ValueError("Sales data contains no valid dates.")

    start = (
        available_start
        if start_date is None
        else pd.to_datetime(start_date).normalize()
    )
    end = (
        available_end
        if end_date is None
        else pd.to_datetime(end_date).normalize()
    )

    if start > end:
        raise ValueError("Start date must not be later than end date.")

    if start < available_start or end > available_end:
        raise ValueError(
            f"Requested date range is outside available data: "
            f"{available_start:%Y-%m-%d} to {available_end:%Y-%m-%d}."
        )

    return df.loc[
        (df["sales_date"] >= start)
        & (df["sales_date"] <= end)
    ].copy()


def load_sales_data(file_path="data/sales.csv"):
    """Load sales records from a CSV file."""
    df = pd.read_csv(file_path)

    df["sales_qty"] = pd.to_numeric(df["sales_qty"], errors="raise")
    df["pos_price"] = pd.to_numeric(df["pos_price"], errors="raise")

    df["sales_amount"] = df["sales_qty"] * df["pos_price"]

    return df


def get_sales_overview(df):
    """Return key sales metrics for the dataset."""
    return {
        "total_sales": round(df["sales_amount"].sum(), 2),
        "total_quantity": int(df["sales_qty"].sum()),
        "transaction_count": int(df["transaction_id"].nunique()),
        "product_count": int(df["product_id"].nunique()),
        "sales_record_count": int(len(df)),
    }


def get_daily_sales_summary(df):
    """Return daily sales metrics and identify the highest and lowest sales days."""
    daily_sales = (
        df.groupby("sales_date")
        .agg(
            sales_amount=("sales_amount", "sum"),
            sales_qty=("sales_qty", "sum"),
            transaction_count=("transaction_id", "nunique"),
        )
        .reset_index()
    )

    daily_sales["sales_date"] = pd.to_datetime(daily_sales["sales_date"])

    average_daily_sales = daily_sales["sales_amount"].mean()

    highest_sales_day = daily_sales.loc[
        daily_sales["sales_amount"].idxmax()
    ]

    lowest_sales_day = daily_sales.loc[
        daily_sales["sales_amount"].idxmin()
    ]

    return {
        "days_analysed": int(len(daily_sales)),
        "average_daily_sales": round(float(average_daily_sales), 2),
        "highest_sales_date": highest_sales_day["sales_date"].strftime("%Y-%m-%d"),
        "highest_sales_amount": round(float(highest_sales_day["sales_amount"]), 2),
        "lowest_sales_date": lowest_sales_day["sales_date"].strftime("%Y-%m-%d"),
        "lowest_sales_amount": round(float(lowest_sales_day["sales_amount"]), 2),
    }


def get_daily_sales_trend(df, start_date=None, end_date=None):
    """
    Return daily sales totals and a seven-calendar-day moving average.
    """
    # Validate the requested period and get the available sales records.
    filtered_df = filter_sales_by_date(
        df,
        start_date=start_date,
        end_date=end_date,
    )

    # Preserve the full dataset's date range for moving-average warm-up.
    all_sales = df.copy()
    all_sales["sales_date"] = pd.to_datetime(
        all_sales["sales_date"]
    ).dt.normalize()

    available_start = all_sales["sales_date"].min()
    available_end = all_sales["sales_date"].max()

    requested_start = (
        available_start
        if start_date is None
        else pd.to_datetime(start_date).normalize()
    )
    requested_end = (
        available_end
        if end_date is None
        else pd.to_datetime(end_date).normalize()
    )

    # Include up to six preceding calendar days for the first MA value.
    calculation_start = max(
        available_start,
        requested_start - pd.Timedelta(days=6),
    )

    calculation_df = all_sales.loc[
        (all_sales["sales_date"] >= calculation_start)
        & (all_sales["sales_date"] <= requested_end)
    ]

    daily_sales = (
        calculation_df.groupby("sales_date")
        .agg(
            sales_amount=("sales_amount", "sum"),
            sales_qty=("sales_qty", "sum"),
        )
        .sort_index()
    )

    # Ensure every calendar date exists before calculating the rolling mean.
    full_dates = pd.date_range(
        start=calculation_start,
        end=requested_end,
        freq="D",
    )

    daily_sales = daily_sales.reindex(full_dates, fill_value=0)
    daily_sales.index.name = "sales_date"

    daily_sales["sales_7day_ma"] = (
        daily_sales["sales_amount"]
        .rolling(window=7, min_periods=7)
        .mean()
    )

    # Display only the requested reporting period.
    daily_sales = daily_sales.loc[
        (daily_sales.index >= requested_start)
        & (daily_sales.index <= requested_end)
    ]

    return daily_sales.reset_index()


def get_sales_by_product(df, start_date=None, end_date=None):
    """Return product-level sales performance for an optional date range."""

    period_df = filter_sales_by_date(df, start_date, end_date)

    product_sales = (
        period_df.groupby(
            ["product_id", "product_name", "category"],
            as_index=False,
        )
        .agg(
            total_qty=("sales_qty", "sum"),
            total_sales=("sales_amount", "sum"),
        )
        .sort_values("total_sales", ascending=False)
        .reset_index(drop=True)
    )

    overall_sales = product_sales["total_sales"].sum()

    product_sales["sales_contribution_pct"] = (
        product_sales["total_sales"] / overall_sales * 100
        if overall_sales != 0
        else 0.0
    )

    return product_sales.round(
        {
            "total_sales": 2,
            "sales_contribution_pct": 2,
        }
    )


def get_product_daily_sales_trend(
    df,
    product_id,
    start_date=None,
    end_date=None,
):
    """
    Return daily sales and a seven-calendar-day moving average
    for one product within the selected date range.
    """
    # Validate the selected date range.
    filter_sales_by_date(df, start_date, end_date)

    all_sales = df.copy()
    all_sales["sales_date"] = pd.to_datetime(
        all_sales["sales_date"]
    ).dt.normalize()

    # Find the available and requested date boundaries.
    available_start = all_sales["sales_date"].min()
    available_end = all_sales["sales_date"].max()

    requested_start = (
        available_start
        if start_date is None
        else pd.to_datetime(start_date).normalize()
    )
    requested_end = (
        available_end
        if end_date is None
        else pd.to_datetime(end_date).normalize()
    )

    # Include six preceding calendar days for the moving average.
    calculation_start = max(
        available_start,
        requested_start - pd.Timedelta(days=6),
    )

    product_df = all_sales.loc[
        (all_sales["product_id"] == product_id)
        & (all_sales["sales_date"] >= calculation_start)
        & (all_sales["sales_date"] <= requested_end)
    ]

    daily_sales = (
        product_df.groupby("sales_date")
        .agg(
            sales_amount=("sales_amount", "sum"),
            sales_qty=("sales_qty", "sum"),
        )
        .sort_index()
    )

    # Fill missing calendar dates with zero sales for this product.
    full_dates = pd.date_range(
        start=calculation_start,
        end=requested_end,
        freq="D",
    )

    daily_sales = daily_sales.reindex(
        full_dates,
        fill_value=0,
    )
    daily_sales.index.name = "sales_date"

    daily_sales["sales_7day_ma"] = (
        daily_sales["sales_amount"]
        .rolling(window=7, min_periods=7)
        .mean()
    )

    # Return only the selected reporting period.
    daily_sales = daily_sales.loc[
        (daily_sales.index >= requested_start)
        & (daily_sales.index <= requested_end)
    ]

    return daily_sales.reset_index()


def get_month_period_analysis(
    df,
    start_date=None,
    end_date=None,
):
    """Summarize sales performance by day-of-month period."""

    df = filter_sales_by_date(
        df,
        start_date=start_date,
        end_date=end_date,
    )

    daily_sales = (
        df.groupby("sales_date")
        .agg(
            sales_amount=("sales_amount", "sum"),
            sales_qty=("sales_qty", "sum"),
        )
        .reset_index()
    )

    day_of_month = daily_sales["sales_date"].dt.day

    daily_sales["month_period"] = pd.cut(
        day_of_month,
        bins=[0, 10, 20, 31],
        labels=["Beginning", "Middle", "End"],
    )

    period_summary = (
        daily_sales.groupby("month_period", observed=False)
        .agg(
            days=("sales_date", "count"),
            avg_daily_sales=("sales_amount", "mean"),
            avg_daily_qty=("sales_qty", "mean"),
        )
        .reset_index()
    )

    overall_avg_sales = daily_sales["sales_amount"].mean()

    if overall_avg_sales != 0:
        period_summary["vs_overall_avg_pct"] = (
            (
                period_summary["avg_daily_sales"]
                - overall_avg_sales
            )
            / overall_avg_sales
            * 100
        )
    else:
        period_summary["vs_overall_avg_pct"] = 0.0

    return period_summary.round(
        {
            "avg_daily_sales": 2,
            "avg_daily_qty": 2,
            "vs_overall_avg_pct": 2,
        }
    )


def get_weekday_weekend_analysis(
    df,
    start_date=None,
    end_date=None,
):
    """Compare sales performance between weekdays and weekends."""

    df = filter_sales_by_date(
        df,
        start_date=start_date,
        end_date=end_date,
    )

    daily_sales = (
        df.groupby("sales_date")
        .agg(
            sales_amount=("sales_amount", "sum"),
            sales_qty=("sales_qty", "sum"),
            total_transactions=("transaction_id", "nunique"),
        )
        .reset_index()
    )

    daily_sales["day_type"] = daily_sales["sales_date"].dt.dayofweek.map(
        lambda day: "Weekend" if day >= 5 else "Weekday"
    )

    summary = (
        daily_sales.groupby("day_type")
        .agg(
            days=("sales_date", "count"),
            total_sales=("sales_amount", "sum"),
            avg_daily_sales=("sales_amount", "mean"),
            avg_daily_qty=("sales_qty", "mean"),
            total_transactions=("total_transactions", "sum"),
        )
        .reset_index()
    )

    summary["avg_daily_transactions"] = (
        summary["total_transactions"] / summary["days"]
    )

    summary["avg_transaction_value"] = (
        summary["total_sales"] / summary["total_transactions"].replace(0, float("nan"))
    )

    return summary[
        [
            "day_type",
            "days",
            "total_sales",
            "avg_daily_sales",
            "avg_daily_qty",
            "total_transactions",
            "avg_daily_transactions",
            "avg_transaction_value",
        ]
    ].round(
        {
            "total_sales": 2,
            "avg_daily_sales": 2,
            "avg_daily_qty": 2,
            "avg_daily_transactions": 2,
            "avg_transaction_value": 2,
        }
    )


def get_weekday_sales_analysis(
    df,
    start_date=None,
    end_date=None,
):
    """Analyze sales performance for each day of the week."""

    df = filter_sales_by_date(
        df,
        start_date=start_date,
        end_date=end_date,
    )

    daily_sales = (
        df.groupby("sales_date")
        .agg(
            sales_amount=("sales_amount", "sum"),
            total_transactions=("transaction_id", "nunique"),
        )
        .reset_index()
    )

    daily_sales["day_of_week"] = (
        daily_sales["sales_date"].dt.day_name()
    )

    summary = (
        daily_sales.groupby("day_of_week")
        .agg(
            days=("sales_date", "count"),
            avg_daily_sales=("sales_amount", "mean"),
            total_sales=("sales_amount", "sum"),
            total_transactions=("total_transactions", "sum"),
        )
    )

    weekdays = [
        "Monday",
        "Tuesday",
        "Wednesday",
        "Thursday",
        "Friday",
        "Saturday",
        "Sunday",
    ]

    summary = summary.reindex(weekdays).fillna(0)
    summary.index.name = "day_of_week"
    summary = summary.reset_index()

    summary["avg_daily_transactions"] = (
        summary["total_transactions"]
        / summary["days"].replace(0, float("nan"))
    ).fillna(0)

    summary["avg_transaction_value"] = (
        summary["total_sales"]
        / summary["total_transactions"].replace(0, float("nan"))
    ).fillna(0)

    overall_avg_sales = daily_sales["sales_amount"].mean()

    if overall_avg_sales != 0:
        summary["vs_overall_avg_pct"] = (
            (summary["avg_daily_sales"] - overall_avg_sales)
            / overall_avg_sales
            * 100
        )
    else:
        summary["vs_overall_avg_pct"] = 0.0

    return summary[
        [
            "day_of_week",
            "days",
            "avg_daily_sales",
            "total_sales",
            "total_transactions",
            "avg_daily_transactions",
            "avg_transaction_value",
            "vs_overall_avg_pct",
        ]
    ].round(
        {
            "avg_daily_sales": 2,
            "total_sales": 2,
            "avg_daily_transactions": 2,
            "avg_transaction_value": 2,
            "vs_overall_avg_pct": 2,
        }
    )


def get_sales_performance(df, start_date=None, end_date=None):
    """Calculate sales KPIs for an optional inclusive date range."""

    period_df = filter_sales_by_date(df, start_date, end_date)

    start = (
        pd.to_datetime(start_date).normalize()
        if start_date is not None
        else period_df["sales_date"].min()
    )

    end = (
        pd.to_datetime(end_date).normalize()
        if end_date is not None
        else period_df["sales_date"].max()
    )

    calendar_days = (end - start).days + 1

    total_sales = float(period_df["sales_amount"].sum())
    total_quantity = int(period_df["sales_qty"].sum())
    transaction_count = int(period_df["transaction_id"].nunique())

    average_transaction_value = (
        round(total_sales / transaction_count, 2)
        if transaction_count > 0
        else None
    )

    return {
        "start_date": start.strftime("%Y-%m-%d"),
        "end_date": end.strftime("%Y-%m-%d"),
        "calendar_days": calendar_days,
        "total_sales": round(total_sales, 2),
        "total_quantity": total_quantity,
        "transaction_count": transaction_count,
        "average_daily_sales": round(total_sales / calendar_days, 2),
        "average_daily_quantity": round(total_quantity / calendar_days, 2),
        "average_daily_transactions": round(
            transaction_count / calendar_days, 2
        ),
        "average_transaction_value": average_transaction_value,
    }

