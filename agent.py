import json
import ollama
import pandas as pd

from datetime import timedelta

from sales_analysis import (
    load_sales_data,
    get_sales_performance,
)

from inventory_analysis import analyze_inventory


MODEL_NAME = "qwen3:4b"
MAX_TOOL_ROUNDS = 3
MAX_ANALYSIS_DAYS = 365


def get_last_n_days_range(days: int = 30):
    df = load_sales_data()

    sales_dates = pd.to_datetime(
        df["sales_date"]
    ).dt.normalize()

    available_start = sales_dates.min()
    latest_date = sales_dates.max()

    if pd.isna(available_start) or pd.isna(latest_date):
        raise ValueError("Sales data contains no valid dates.")

    requested_start = latest_date - timedelta(
        days=days - 1
    )

    actual_start = max(
        requested_start,
        available_start,
    )

    return (
        actual_start.date().isoformat(),
        latest_date.date().isoformat(),
    )


# Available Python tools
def calculate_total(price: float, quantity: int) -> float:
    """Calculate total price from unit price and quantity."""
    return price * quantity


def get_sales_kpis(start_date=None, end_date=None):
    """Return sales KPIs for an optional inclusive date range."""

    df = load_sales_data()

    return get_sales_performance(
        df,
        start_date=start_date,
        end_date=end_date,
    )


def execute_tool(function_name: str, arguments: dict):
    """Execute an explicitly allowed tool."""

    if function_name == "calculate_total":
        price = arguments.get("price")
        quantity = arguments.get("quantity")

        if isinstance(price, bool) or not isinstance(price, (int, float)):
            raise ValueError("price must be a number")

        if isinstance(quantity, bool) or not isinstance(quantity, int):
            raise ValueError("quantity must be an integer")

        if price < 0 or quantity < 0:
            raise ValueError("price and quantity cannot be negative")

        return calculate_total(price, quantity)

    elif function_name == "get_sales_kpis":
        period_days = arguments.get("period_days")
        start_date = arguments.get("start_date")
        end_date = arguments.get("end_date")

        requested_start_date = start_date
        requested_end_date = end_date

        requested_period_days = period_days

        if period_days is not None:
            if (
                isinstance(period_days, bool)
                or not isinstance(period_days, int)
                or period_days <= 0
                or period_days > MAX_ANALYSIS_DAYS
            ):
                raise ValueError(
                    f"period_days must be between 1 and {MAX_ANALYSIS_DAYS}"
                )

            if start_date is not None or end_date is not None:
                raise ValueError(
                    "Do not combine period_days with start_date or end_date"
                )

            start_date, end_date = get_last_n_days_range(period_days)

        if start_date is not None and not isinstance(start_date, str):
            raise ValueError("start_date must be a string or None")

        if end_date is not None and not isinstance(end_date, str):
            raise ValueError("end_date must be a string or None")

        requested_start = None
        requested_end = None
        requested_calendar_days = None

        if period_days is None and (
                start_date is not None or end_date is not None
        ):
            sales_df = load_sales_data()

            available_dates = pd.to_datetime(
                sales_df["sales_date"]
            ).dt.normalize()

            available_start = available_dates.min()
            available_end = available_dates.max()

            try:
                requested_start = (
                    available_start
                    if start_date is None
                    else pd.to_datetime(
                        start_date, errors="raise"
                    ).normalize()
                )

                requested_end = (
                    available_end
                    if end_date is None
                    else pd.to_datetime(
                        end_date, errors="raise"
                    ).normalize()
                )
            except (ValueError, TypeError):
                raise ValueError(
                    "start_date and end_date must be valid dates."
                )

            if requested_start > requested_end:
                raise ValueError(
                    "start_date must not be later than end_date."
                )

            requested_calendar_days = (
                                              requested_end - requested_start
                                      ).days + 1

            if requested_calendar_days > MAX_ANALYSIS_DAYS:
                raise ValueError(
                    f"Date range must not exceed "
                    f"{MAX_ANALYSIS_DAYS} calendar days."
                )

            actual_start = max(
                requested_start,
                available_start,
            )

            actual_end = min(
                requested_end,
                available_end,
            )

            if actual_start > actual_end:
                raise ValueError(
                    "No sales data is available within the requested date range."
                )

            start_date = actual_start.date().isoformat()
            end_date = actual_end.date().isoformat()

        result = get_sales_kpis(
            start_date=start_date,
            end_date=end_date,
        )

        result["data_coverage_days"] = result["calendar_days"]

        if requested_period_days is not None:
            result["requested_period_days"] = requested_period_days
            result["data_coverage_complete"] = (
                    result["calendar_days"] == requested_period_days
            )

        elif requested_calendar_days is not None:
            result["requested_calendar_days"] = requested_calendar_days
            result["data_coverage_complete"] = (
                    result["calendar_days"] == requested_calendar_days
            )

            if requested_start_date is not None:
                result["requested_start_date"] = (
                    requested_start_date
                )

            if requested_end_date is not None:
                result["requested_end_date"] = (
                    requested_end_date
                )

        return result

    elif function_name == "analyze_inventory":
        result_df = analyze_inventory()

        # Convert the DataFrame into a format the LLM can read.
        return result_df.to_dict(orient="records")

    else:
        raise ValueError(f"Unknown tool: {function_name}")


TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "calculate_total",
            "description": (
                "Calculate total price by multiplying unit price and quantity."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "price": {"type": "number"},
                    "quantity": {"type": "integer"},
                },
                "required": ["price", "quantity"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_sales_kpis",
            "description": (
                "Calculate sales KPIs from the sales dataset. "
                "Use this tool when the user asks about total sales, "
                "total quantity, transaction count, average daily sales, "
                "or average transaction value. "
                "For requests about the last N days, set period_days "
                "to the requested number of days, from 1 to 365. "
                "For a specific date range, provide start_date and end_date "
                "in YYYY-MM-DD format. "
                "If no date range or period is specified, use the full "
                "available dataset. Never calculate dates yourself. "
                "The tool may limit the actual date range to available sales data. "
                "Always check the returned start_date, end_date, calendar_days, "
                "and data coverage metadata before describing the results. "
                "Never claim that the requested period is fully covered when "
                "data_coverage_complete is false. "
                "Clearly explain the actual data coverage to the user."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "period_days": {
                        "type": ["integer", "null"],
                        "description": (
                            "Number of recent days to analyze, from 1 to 365. "
                            "Use the exact number requested by the user. "
                            "Use null when the user specifies a date range or "
                            "does not request a specific period."
                        )
                    },
                    "start_date": {
                        "type": ["string", "null"],
                        "description": (
                            "Inclusive start date in YYYY-MM-DD format "
                            "for a specific date-range request, or null."
                        )
                    },
                    "end_date": {
                        "type": ["string", "null"],
                        "description": (
                            "Inclusive end date in YYYY-MM-DD format "
                            "for a specific date-range request, or null."
                        )
                    },
                },
                "required": ["period_days", "start_date", "end_date"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "analyze_inventory",
            "description": (
                "Analyze current inventory risk. Use this tool when "
                "the user asks which products require reorder, "
                "which products have the lowest estimated stock cover, "
                "or asks for an inventory risk summary. "
                "The tool returns the inventory snapshot, stock on hand, "
                "reorder level, average daily sales, inventory status, "
                "and estimated stock cover days."
            ),
            "parameters": {
                "type": "object",
                "properties": {},
                "required": [],
            },
        },
    },
]


def ask_agent(question: str) -> str:
    """Ask the LLM a question and execute permitted tool calls."""
    if not isinstance(question, str) or not question.strip():
        raise ValueError("Question cannot be empty")

    messages = [
        {
            "role": "system",
            "content": (
                "You are a sales analysis assistant. "
                "When answering numerical questions, use the exact values returned by tools. "
                "Do not describe a value as above, below, "
                "or equal to a threshold unless the returned data supports that comparison. "
                "Use tool results as the source of truth for business data. "
                "When a tool returns an error, explain the error briefly "
                "and accurately. Do not invent reasons, dates, data coverage, "
                "or system limitations. If no sales data is available for "
                "the requested date range, state that no sales data is "
                "available for that period and that the KPIs cannot be "
                "calculated. Do not add unrelated explanations or suggestions. "
                "Answer simple general-knowledge questions directly when appropriate. "
                "After answering a general question, briefly guide the user "
                "toward sales or inventory analysis when natural. "
                "If the input is unclear or meaningless, ask the user to "
                "clarify instead of inventing an answer. "
                "Only call tools when they are useful for answering the question. "
                "\nSALES DATA TOOL RULES:\n"
                "- For questions asking for sales totals, sales KPIs, or "
                "sales metrics for a specified date range, call "
                "get_sales_kpis with the requested date parameters.\n"
                "- Never assume that sales data is unavailable because a "
                "requested date is in the future or past.\n"
                "- Never claim that a date range has no sales data unless "
                "the actual tool result supports that conclusion.\n"
                "- Use the actual tool result to answer numerical questions.\n"
                "- Do not invent tool results or skip the tool by guessing."
                "- Answer the user's question directly using the actual tool result.\n"
                "- Do not add generic warnings about future dates or production systems "
                "unless they are relevant and supported by the actual context.\n"
                "- Do not describe a date as being in the future without checking it "
                "against the current date.\n"
            ),
        },
        {
            "role": "user",
            "content": question,
        },
    ]

    for _ in range(MAX_TOOL_ROUNDS + 1):

        response = ollama.chat(
            model=MODEL_NAME,
            messages=messages,
            tools=TOOLS,
        )

        message = response["message"]
        messages.append(message)

        tool_calls = message.get("tool_calls", [])

        if not tool_calls:
            return message.get("content", "")

        for tool_call in tool_calls:
            function_name = tool_call["function"]["name"]
            arguments = tool_call["function"]["arguments"]

            print(f"\nTool requested: {function_name}")
            print(f"Arguments: {arguments}")

            try:
                result = execute_tool(function_name, arguments)

                print(f"Actual Python result: {result}")

                tool_content = json.dumps(
                    result,
                    ensure_ascii=False,
                    default=str,
                )

                print(f"JSON tool result: {tool_content}")

            except (ValueError, TypeError) as error:
                tool_content = f"Tool error: {error}"
                print(tool_content)

            messages.append(
                {
                    "role": "tool",
                    "name": function_name,
                    "content": tool_content,
                }
            )

    return "Unable to complete the request within the tool-call limit."