# AI Sales & Inventory Analyst

## 1. Project Overview

AI Sales & Inventory Analyst is a local business analytics proof of concept (POC) built with Python, Pandas, Streamlit, and Ollama.

The project combines a sales and inventory dashboard with a local LLM-powered AI Analyst. Users can review business performance through predefined analytics or ask questions in natural language. The AI Analyst can call Python tools to retrieve calculated results from the underlying datasets.

The project focuses on practical business analysis, tool calling, data handling, and integration between an LLM and Python functions.

## 2. Features

### Sales Dashboard

- Total sales revenue
- Total quantity sold
- Transaction count
- Average daily sales
- Daily sales trend
- Top five products by sales
- Reporting periods:
  - Last 14 full days
  - Last 30 full days
  - Custom date range
- Maximum reporting range of 365 calendar days

### Inventory Risk Analysis

- Inventory status overview
- Estimated stock cover in days
- Reorder risk identification
- Average daily sales used to estimate how long current inventory may last

Stock cover is an estimate based on historical sales and current inventory. It does not account for every factor that may affect future demand or replenishment.

### Supplementary Sales Analysis

A separate page provides additional views of sales patterns, including:

- Sales by month segment
- Weekday versus weekend performance
- Detailed weekday comparisons
- Shared date-range filtering

### AI Analyst

- Accepts natural-language questions
- Uses a local Ollama model
- Selects Python tools when business data or calculations are required
- Retrieves sales performance and inventory analysis results
- Serializes tool outputs for use in the LLM conversation
- Supports simple general-knowledge questions that do not require business data

The AI Analyst uses Python functions for numerical analysis rather than relying solely on the LLM to calculate business figures.

## 3. System Architecture

```text
Streamlit Application
        |
        v
     app.py
  Page Navigation
        |
        +------------------------------+
        |                              |
        v                              v
   main_page.py            Supplementary Sales Page
   Dashboard & AI UI       pages/1_Supplementary_Sales_Analysis.py
        |
        v
     agent.py
  Agent Orchestration
        |
        +------------------------------+
        |                              |
        v                              v
  Ollama / Qwen3:4B               Python Tools
  Language Model                       |
                                       +--> sales_analysis.py
                                       |
                                       +--> inventory_analysis.py
                                       |
                                       v
                                CSV Data Files
```

### Main Components

| File | Responsibility |
|---|---|
| `app.py` | Configures the Streamlit application and handles page navigation |
| `main_page.py` | Displays the main dashboard and AI Analyst interface |
| `pages/1_Supplementary_Sales_Analysis.py` | Displays supplementary sales analysis |
| `agent.py` | Coordinates LLM interactions and Python tool execution |
| `sales_analysis.py` | Contains sales analysis and calculation functions |
| `inventory_analysis.py` | Contains inventory risk and stock-cover calculations |
| `data/` | Stores the synthetic sales and inventory datasets |
| `tests/` | Contains automated tests |

### AI Agent Workflow

1. The user submits a question through the Streamlit interface.
2. The agent sends the conversation to the local Ollama model.
3. When business calculations or data retrieval are needed, the model can request a Python tool.
4. The agent executes the selected tool and serializes its result.
5. The tool result is returned to the LLM as part of the conversation.
6. The model produces a response for display in the application.

This design separates language understanding and response generation from the Python functions responsible for business calculations.

## 4. Technology Stack

- **Python 3.12.1** — Application logic and data processing
- **Pandas** — Data manipulation and analysis
- **Streamlit 1.66.0** — Dashboard and user interface
- **Ollama** — Local LLM runtime
- **Qwen3:4B** — Local language model
- **Git** — Version control
- **CSV** — Synthetic sales and inventory data storage

## 5. Setup and Usage

### Prerequisites

- Python 3.12
- Git
- Ollama installed locally
- Sufficient system resources to run the selected local model

### Install Dependencies

Create and activate a virtual environment if one does not already exist.

On Windows PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

Install the required packages:

```powershell
python -m pip install streamlit pandas ollama
```

### Download the Model

```powershell
ollama pull qwen3:4b
```

Ensure that Ollama is running and the model is available locally before using the AI Analyst.

### Launch the Application

From the project directory:

```powershell
.\.venv\Scripts\python.exe -m streamlit run app.py
```

Streamlit will provide a local URL in the terminal. Open that URL in a browser to use the application.

## 6. QA, Debugging, and Problem-Solving

Testing focused on verifying business calculations, tool execution, data serialization, date handling, and the final Streamlit user experience.

This was practical POC-level testing and debugging, not a formal enterprise QA process.

### 6.1 Tool Execution and Data Serialization

During development, the agent was tested to confirm that Python tools returned usable results to the LLM.

The debugging process included:

- Inspecting actual Python tool outputs
- Checking how tool results were serialized into JSON
- Handling Pandas values that are not directly JSON serializable
- Verifying that tool results were passed back into the conversation correctly
- Comparing AI responses with independently calculated results

For example, Pandas `Timestamp` values may require conversion before JSON serialization. The implementation uses:

```python
json.dumps(result, default=str)
```

This allows otherwise unsupported values to be converted to strings during serialization.

### 6.2 Sales Calculation Verification

The AI Analyst was tested with questions requiring sales data and calculations.

| Test scenario | Verification |
|---|---|
| Total sales across the available dataset | AI response matched the independently calculated total of `$77,861.76` |
| Sales over a selected date range | Compared tool results against independent calculations |
| Quantity sold over a recent period | The answer for the last two days was 241 items and matched an independent analysis |
| General-knowledge question | Checked that a business-data tool was not required |
| Invalid date range | Checked handling of invalid input |
| Slash-formatted dates | Tested date interpretation |
| Date range with no matching data | Checked the no-data response |

The full dataset covers 2026-07-21 to 2026-10-18. Its overall totals are based on the synthetic CSV data supplied with the project.

### 6.3 Inventory Analysis Verification

Inventory analysis was checked against the underlying inventory and sales data.

Example stock-cover estimates included:

- Laundry Detergent: approximately 0.51 days
- Potato Chips: approximately 0.86 days
- Shampoo: approximately 1.02 days
- Green Tea: approximately 1.17 days

These figures were used to check whether the AI response reflected the actual tool output. Prompt wording was also refined to reduce unsupported comparisons against thresholds that were not defined by the application.

### 6.4 AI Response Handling and UI Regression Check

During final integration testing, the AI Analyst encountered a `TypeError` indicating that a `NoneType` object had no length.

The issue occurred when the agent processed an LLM response whose optional `tool_calls` field could be `None`, rather than a list.

The response handling was updated to handle missing or `None` values more defensively:

```python
tool_calls = message.get("tool_calls") or []

if not tool_calls:
    return message.get("content") or ""
```

This prevents the agent from attempting to treat a `None` value as a tool-call list. It also provides an empty-string fallback when the response content is missing.

**Verification performed:**

- Asked for total sales and confirmed that the AI response returned `$77,861.76`.
- Asked how many items were sold in the last two days and confirmed that the answer of 241 matched an independent analysis.
- Confirmed that the question input cleared after submission.
- Switched between the Main Page and Supplementary Sales Analysis pages.
- Confirmed that the dashboard and page navigation remained operational after the changes.

These checks verified the expected behaviour in the tested scenarios. They do not guarantee that every possible LLM response or error condition is handled correctly.

### 6.5 Automated and Manual Testing

The project includes automated tests and manual integration checks.

The `tests/` directory contains tests covering areas including:

- Agent error handling
- General questions
- Unknown tool handling
- Inventory analysis with zero sales
- Sales moving-average calculations

A manual agent integration script, `manual_agent_integration.py`, was also used during development.

Earlier automated checks for agent error handling, general questions, unknown tools, and zero-sales inventory handling passed in the test run performed at that stage. The moving-average test was subsequently added; its inclusion in the test suite should not be interpreted as evidence that every test has passed in a single final run.

The overall testing approach was to identify an issue, inspect actual outputs, compare results against independent calculations, apply a targeted fix, and verify the affected behaviour again.

## 7. Limitations

- The datasets are synthetic and do not represent live business operations.
- The application does not connect to a live POS, ERP, or inventory management system.
- Local LLM response times depend on the available hardware and model.
- LLM-generated explanations may still be inaccurate or incomplete.
- Stock-cover estimates rely on historical sales and do not account for all demand or replenishment factors.
- Promotional effects are not incorporated into the inventory risk calculations.
- Reporting is limited to a maximum range of 365 calendar days.
- Automated test coverage is not comprehensive.
- The application is a local proof of concept rather than a production-ready business system.

## 8. Future Improvements

Potential improvements include:

- Expand automated test coverage for sales calculations, date handling, and agent response edge cases.
- Improve error reporting and recovery for unexpected LLM responses.
- Evaluate inventory forecasts that account for promotional periods and changes in demand.
- Add more analytical tools when supported by clear business requirements.
- Improve response speed through model and prompt evaluation.
- Explore integration with additional business data sources.

These improvements are outside the current V1.0 scope.

## 9. Project Status

**Version:** V1.0 POC

The current version demonstrates an integrated local analytics application combining:

- A Streamlit sales and inventory dashboard
- Supplementary sales analysis
- Python-based business calculation tools
- Local LLM tool calling
- Basic automated testing and manual verification
- Iterative debugging and targeted fixes

The project is intended to demonstrate practical software development, data analysis, debugging, and AI integration skills in a small business-oriented application.
