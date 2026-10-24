# AI Sales & Inventory Analyst

A local AI-powered sales and inventory analysis dashboard built with Python, Streamlit, and a tool-calling LLM. This proof of concept (POC) combines structured business-data analysis with natural-language questions to support sales performance monitoring and inventory risk assessment.

## 1. Project Overview

Retail sales and inventory data can reveal important business signals, but manually reviewing figures across different reports takes time.

This project explores how an AI assistant can make structured sales and inventory analysis more accessible by combining a visual dashboard with natural-language interaction.

**Project goals**
- Monitor sales performance over a selectable reporting period.
- Identify top-performing products and inventory risks.
- Allow users to ask business questions in natural language.
- Use Python tools for structured calculations and data retrieval rather than relying on the LLM to invent business figures.
- Validate the integration between the dashboard, LLM, Python tools, and serialized tool results.

**Project type:** Personal project / Proof of Concept (POC)  
**Data:** Synthetic retail sales and inventory data  
**Environment:** Local development on Windows

## 2. Features

### Sales Performance Dashboard
- Sales KPIs: total sales, total quantity, transaction count, and average daily sales.
- Daily sales trend chart.
- Top 5 products by sales, with a horizontal bar chart and supporting table.
- Reporting periods: last 14 full days, last 30 full days, or a custom date range.
- Date-range validation, data-coverage information, and handling of periods without available sales data.
- Maximum reporting period of 365 calendar days.

### Inventory Risk Analysis
- Inventory overview showing total products, products requiring reorder, and products with estimable stock coverage.
- Inventory status based on current stock and reorder thresholds.
- Estimated stock-cover days based on average daily sales.
- Inventory risk details prioritised by reorder status and stock-cover days.
- Sales and inventory comparison by product.

### AI Analyst
- Natural-language question input through the Streamlit dashboard.
- LLM tool calling to request structured analysis from Python functions.
- Sales KPI and inventory analysis tools.
- JSON serialization of tool results before returning them to the LLM.
- System instructions designed to prioritise tool results, explain errors accurately, and improve numerical comparisons.

Example questions:
- `What are the total sales?`
- `Which products require reordering, and why?`
- `Which products have estimated stock cover below 1 day?`
- `Which product has the lowest estimated stock cover days?`

## 3. System Architecture

The project separates language understanding, business-data analysis, and presentation.

```text
User
  |
  v
Streamlit Dashboard (app.py)
  |
  v
AI Agent / Orchestration (agent.py)
  |
  v
Local LLM via Ollama
  |
  | Tool call with arguments
  v
Python Analysis Functions
  |
  +-----------------------+
  |                       |
  v                       v
Sales Analysis       Inventory Analysis
(sales_analysis.py)  (inventory_analysis.py)
  |                       |
  +-----------+-----------+
              |
              v
       Structured Results
              |
              v
       JSON Serialization
              |
              v
       LLM Final Response
              |
              v
       Streamlit Dashboard
```

### Component responsibilities

| Component | Responsibility |
|---|---|
| `app.py` | Displays the dashboard, charts, tables, reporting-period controls, and AI Analyst interface. |
| `agent.py` | Manages the LLM conversation, tool-calling loop, tool execution, result serialization, and response generation. |
| `sales_analysis.py` | Performs structured sales-data calculations and product-level analysis. |
| `inventory_analysis.py` | Analyses inventory status, reorder requirements, average daily sales, and estimated stock coverage. |
| `data/` | Contains the synthetic sales and inventory datasets. |
| Ollama | Runs the local language model used by the AI Analyst. |

### Why use Python tools with an LLM?

The LLM interprets the user's question and decides when to request a permitted tool. Python performs the underlying calculations using structured data. The LLM then turns the returned results into a readable explanation.

This separation helps keep business calculations explicit and verifiable, although the LLM can still misinterpret or incorrectly summarise results.

## 4. Technology Stack

- **Python 3.12.1** — application logic and data analysis.
- **Pandas** — data loading, transformation, aggregation, and analysis.
- **Streamlit 1.66.0** — interactive dashboard and AI question interface.
- **Ollama** — local LLM runtime.
- **Qwen3:4B** — language model used for the AI Analyst.
- **Git** — local version control.

## 5. Setup and Usage

### Prerequisites

- Python 3.12 or a compatible Python environment.
- Git.
- Ollama installed and running locally.
- The `qwen3:4b` model available in Ollama.

### Step 1: Create and activate a virtual environment

From the project root in PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

### Step 2: Install the required Python packages

If the project does not yet include a dependency file, install the packages used by the application:

```powershell
python -m pip install streamlit pandas ollama
```

### Step 3: Download the local model

```powershell
ollama pull qwen3:4b
```

Ensure Ollama is running before using the AI Analyst.

### Step 4: Launch the dashboard

From the project root:

```powershell
.\.venv\Scripts\python.exe -m streamlit run app.py
```

Streamlit will provide a local URL in the terminal. Open that URL in a browser to access the dashboard.

### Step 5: Try the AI Analyst

Enter a question in the AI Analyst section and select **Ask AI**. The application sends the question to the agent, which may invoke Python analysis tools before generating its response.

## 6. QA, Debugging, and Problem-Solving

Testing was performed incrementally as features were developed and integrated. The process focused on observing actual outputs, checking data consistency, reproducing issues, and validating targeted changes.

### Tool execution and data serialization

During AI integration, the tool-calling flow was inspected using actual Python console output.

Checks included:
- Confirming that the LLM requested the expected tool, such as `analyze_inventory`.
- Inspecting the actual Python result returned by the analysis function.
- Comparing the Python result with the JSON-serialised tool result.
- Verifying that pandas `Timestamp` values were converted into JSON-compatible strings using the serialization fallback.
- Checking that the final AI response reflected the returned business data.

### Numerical reasoning issue and targeted improvement

An initial inventory question produced an inaccurate summary: the AI correctly identified products requiring reorder, but incorrectly described all of them as having less than one day of estimated stock coverage.

The underlying Python results showed:

| Product | Estimated stock cover | Correct classification |
|---|---:|---|
| Laundry Detergent | 0.51 days | Below 1 day |
| Potato Chips | 0.86 days | Below 1 day |
| Shampoo | 1.02 days | At least 1 day |
| Green Tea | 1.17 days | At least 1 day |

The issue was investigated by reviewing the tool output rather than assuming the Python calculations were incorrect.

A targeted system-prompt change was then introduced to instruct the LLM to use exact tool-returned values and avoid unsupported numerical comparisons.

Follow-up checks used both sides of the threshold:

- Products with estimated stock cover below one day.
- Products requiring reorder with estimated stock cover of at least one day.
- The product with the lowest estimated stock cover.

The follow-up answers matched the observed tool results in these cases. This provided evidence that the targeted change improved the tested responses, but did not establish that all possible LLM answers would be accurate.

### Testing approach

The development process used practical, incremental checks:

1. Identify an unexpected result.
2. Inspect actual Python output and execution logs.
3. Verify serialization and the data passed between components.
4. Compare the AI answer with the underlying analysis results.
5. Apply a focused change rather than broadly rewriting the application.
6. Repeat the relevant test and record the observed result.

These are manual development and debugging checks for a POC; they should not be interpreted as a formal enterprise QA process or a comprehensive automated test suite.

## 7. Limitations

- The application uses synthetic data and has not been validated against a live retail POS or inventory system.
- The LLM runs locally and response latency depends on the available hardware and model performance.
- LLM-generated explanations can still contain inaccuracies, especially for broad or ambiguous questions.
- Estimated stock-cover days are projections based on average daily sales, not guaranteed stockout times.
- Promotional effects are not currently adjusted in the average daily sales baseline.
- The dashboard limits the requested sales reporting period to 365 calendar days.
- Automated evaluation of LLM responses and comprehensive regression testing have not yet been established.

## 8. Future Improvements

Potential next steps include:

- Add a dependency file and improve fresh-environment setup.
- Organise tests into a dedicated test directory and expand repeatable automated checks.
- Add more regression tests for numerical thresholds, missing data, and ambiguous questions.
- Improve structured validation of LLM tool arguments and returned results.
- Explore more robust answer validation for numerical claims.
- Evaluate performance and response latency across different local models.
- Integrate with a real data source after validating data quality, access controls, and business requirements.

## 9. Project Status

This project is an evolving personal POC demonstrating practical experience with Python data analysis, Streamlit dashboard development, local LLM integration, tool calling, Git version control, and iterative debugging.

The emphasis is on building and validating one feature at a time, keeping business calculations in explicit Python functions, and improving the reliability of AI-generated explanations through observed test results.
