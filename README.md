# AI-Powered Sales & Inventory Analyst

## Project Overview

An AI-powered Proof of Concept (POC) that combines sales analysis, basic inventory risk monitoring, and Large Language Model (LLM) tool calling to support data-driven business decisions.

The application uses Python and pandas for data analysis, Streamlit for the interactive dashboard, and an LLM agent to interpret user questions and invoke the appropriate analysis tools.

### Objectives

- Analyse sales performance and product-level sales trends.
- Monitor inventory levels and identify products requiring replenishment.
- Enable natural-language questions through LLM tool calling.
- Demonstrate practical integration of Python data analysis, AI orchestration, and an interactive dashboard.

### Technology Stack

- **Language:** Python
- **Data Analysis:** pandas
- **Dashboard:** Streamlit
- **AI Integration:** LLM Tool Calling
- **Development Environment:** PyCharm

### Project Scope

This project focuses on sales analytics and basic inventory risk monitoring. It is a Proof of Concept (POC), not a full Enterprise Resource Planning (ERP) system.

Features such as supplier management, purchasing workflows, inventory costing, multi-warehouse management, and advanced forecasting are outside the current V1.0 scope.

## System Architecture

The application separates natural-language interaction, tool orchestration, and data analysis into distinct responsibilities.

### Architecture Components

| Component | Responsibility |
|---|---|
| LLM | Interprets user questions and generates natural-language responses. |
| Agent / Orchestration | Coordinates the interaction between the LLM and available analysis tools. |
| Analysis Tools | Execute Python functions to calculate sales metrics and retrieve inventory-related insights. |
| Data Processing | Uses pandas to process and analyse structured sales and inventory data. |
| Streamlit Dashboard | Provides the user interface for viewing analysis results and interacting with the application. |

### Typical Interaction Flow

1. The user submits a business question through the application.
2. The LLM interprets the question and determines whether an available tool is needed.
3. The agent coordinates the tool-calling process.
4. The selected Python analysis function processes the relevant data and returns its result.
5. The LLM uses the tool result to formulate a response for the user.

The actual execution flow depends on the application's implemented tool-calling logic and available tools.

### Design Approach

The project follows an incremental development approach. Individual analysis features are implemented and tested before being integrated into the wider application.

This separation of responsibilities helps make the application easier to understand, test, debug, and extend.

## Features

### 1. Sales Performance Dashboard

- Displays key sales performance indicators through KPI cards.
- Summarises total sales, total quantity sold, total transactions, and average daily sales.
- Supports different reporting periods for reviewing sales performance.

### 2. Flexible Date-Range Analysis

- **Last 14 Full Days:** Analyses the most recent 14 complete days.
- **Last 30 Full Days:** Analyses the most recent 30 complete days.
- **Custom Date Range:** Allows users to select a reporting period within the available dataset.
- Validates date selections and handles invalid or unsupported reporting ranges.

### 3. Inventory Risk Monitoring

- Identifies products that require replenishment based on the implemented inventory rules.
- Displays inventory risk details in a structured table.
- Prioritises products marked as requiring reorder.
- Supports configurable analysis periods for reviewing inventory-related sales data.

### 4. Data Analysis and Validation

- Uses Python and pandas to process structured sales and inventory data.
- Applies data validation and date-range checks before performing analysis.
- Supports testing of edge cases, including zero-sales products and date ranges with no overlapping data.

### 5. AI Tool-Calling Integration

- Integrates an LLM with Python-based analysis tools.
- Supports a tool-calling workflow in which the model can request analysis and use returned results to formulate an answer.
- Separates language-model interaction from the underlying data-analysis logic.

The scope of AI-assisted analysis is limited to the tools and workflows implemented in the current version.

## QA, Debugging and Problem Solving

The project follows an iterative development and testing approach. Issues are investigated using actual execution results, followed by targeted fixes and verification.

### Debugging Workflow

1. **Identify the issue** — Reproduce the unexpected behaviour and identify the affected feature or component.
2. **Inspect execution results** — Examine actual Python tool outputs and intermediate results instead of relying solely on the final LLM response.
3. **Verify data serialization and parsing** — Check whether tool results can be correctly serialized into JSON and parsed by the receiving component, including handling pandas `Timestamp` values where applicable.
4. **Cross-check analytical results** — Compare tool outputs against independently executed Python analysis to help identify discrepancies.
5. **Apply targeted fixes** — Correct the underlying issue while keeping changes focused on the affected functionality.
6. **Retest and document evidence** — Re-run the relevant test and record the observed result to confirm whether the fix resolves the issue.

### Testing Principles

- Validate actual execution behaviour rather than assuming that a successful model response guarantees correct analysis.
- Check the consistency between Python analysis results and the information presented to the user.
- Test relevant edge cases and data-format conversions.
- Prefer small, incremental changes that can be verified before proceeding to the next feature.

### Scope of Testing

Testing is performed as part of the project's development and debugging workflow. This documentation describes practical development testing and troubleshooting; it does not claim formal enterprise QA certification or comprehensive automated test coverage.

## Setup and Usage

### Prerequisites

- Windows
- Python 3.12.1
- A Python virtual environment
- Streamlit

### Project Structure

The main application and analysis modules are organised as follows:

```text
myPythonProject/
├── app.py
├── generate_data.py
├── validate_data.py
├── sales_analysis.py
├── inventory_analysis.py
├── data/
│   ├── sales.csv
│   └── inventory.csv
└── README.md
```

Additional application pages and supporting files may be added as development progresses.

### Environment Setup

Open a terminal in the project root directory:

```powershell
cd "cd path\to\myPythonProject"
```

Activate the existing virtual environment:

```powershell
.\.venv\Scripts\Activate.ps1
```

Verify the Python and Streamlit versions:

```powershell
python --version
python -m streamlit --version
```

If Streamlit is not installed in the active environment, install it using:

```powershell
python -m pip install streamlit
```

### Run the Application

Start the Streamlit application from the project root:

```powershell
python -m streamlit run app.py
```

Streamlit will provide a local URL in the terminal. Open that URL in a web browser to access the application.

### Development Workflow

The project is developed incrementally. Individual features are implemented and tested before further integration, with debugging and validation performed throughout development.





