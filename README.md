# Skylark Monday.com Business Intelligence Agent

**Live Hosted Prototype:** [https://15afa4b0267912.lhr.life](https://15afa4b0267912.lhr.life)  
**GitHub Repository:** [https://github.com/Elaina2005/skylark](https://github.com/Elaina2005/skylark)

An autonomous, founder-level AI Business Intelligence agent that integrates directly with **Monday.com GraphQL API v2** and utilizes **Anthropic Claude Tool Use** (`claude-3-7-sonnet` / `claude-3-5-sonnet`) to deliver instant, context-aware answers across sales pipeline and operational project execution data.

---

## System Architecture

```
                                  +---------------------------------------+
                                  |         Founder / Executive           |
                                  +---------------------------------------+
                                                     |
                                                     v
                                  +---------------------------------------+
                                  |       Streamlit UI (streamlit_app.py) |
                                  |   - Conversational Chat Interface     |
                                  |   - Live Tool Progress Visualizer     |
                                  |   - Leadership Update Download        |
                                  +---------------------------------------+
                                                     |
                                                     v
                                  +---------------------------------------+
                                  |       Agent Core (src/agent.py)       |
                                  |   - Anthropic Claude Tool Use Loop    |
                                  |   - Dynamic Live Schema Injection     |
                                  |   - Proactive Caveat & Ambiguity Check|
                                  +---------------------------------------+
                                                     |
                                                     v
                                  +---------------------------------------+
                                  |        Tools Layer (src/tools.py)     |
                                  |   - get_work_orders / get_deals       |
                                  |   - compute_metric (KPIs & Win Rates) |
                                  |   - cross_reference_boards            |
                                  |   - get_data_quality_report           |
                                  +---------------------------------------+
                                        |                           |
                                        v                           v
                      +-----------------------------+   +-----------------------------+
                      | Resilience / Normalizer     |   | Leadership Update Generator |
                      | (src/normalizer.py)         |   | (src/insights.py)           |
                      | - Fuzzy Text Resolution     |   | - Executive Markdown Report |
                      | - Date & Currency Parsing   |   | - Watch Items & Stale Deals |
                      | - Null & Caveat Accounting  |   | - Overdue Order Detection   |
                      +-----------------------------+   +-----------------------------+
                                        |
                                        v
                      +---------------------------------------------+
                      | Monday.com Client (src/monday_client.py)    |
                      | - Direct GraphQL API v2 Queries             |
                      | - Cursor Pagination (items_page)            |
                      | - Exponential Backoff & 429 Rate Limiting   |
                      | - In-Memory Cache (10-Minute TTL)           |
                      +---------------------------------------------+
                                        |
                                        v
                      +---------------------------------------------+
                      | Monday.com Live Boards                      |
                      |   1. Work Orders Board (Execution Data)     |
                      |   2. Deals Board (Commercial Pipeline Data) |
                      +---------------------------------------------+
```

---

## Quick Start and Setup Instructions

### 1. Prerequisites
- Python 3.11+
- Monday.com account with API access
- Anthropic API Key

### 2. Installation
Clone the repository and install the pinned dependencies:

```bash
git clone https://github.com/Elaina2005/skylark.git
cd skylark

# Create and activate virtual environment
python -m venv .venv
# On Windows:
.venv\Scripts\activate
# On macOS/Linux:
source .venv/bin/activate

# Install requirements
pip install -r requirements.txt
```

### 3. Environment Configuration
Copy the `.env.example` file to `.env`:

```bash
cp .env.example .env
```

Set your credentials in `.env`:
```ini
# Monday.com Personal API Token (monday.com -> Developers -> My Access Tokens)
MONDAY_API_TOKEN=your_monday_token_here

# Anthropic Claude API Key (https://console.anthropic.com)
ANTHROPIC_API_KEY=your_anthropic_key_here

# Optional: Board IDs if different from defaults
# MONDAY_WORK_ORDERS_BOARD_ID=1234567890
# MONDAY_DEALS_BOARD_ID=1234567891
```

### 4. Monday.com Board Configuration
1. Log into your Monday.com workspace.
2. In the left sidebar, click **Add (+)** -> **Import** -> **Excel / CSV**.
3. Upload `data/Deal Funnel Data.xlsx` as a board named `Deals`.
4. Upload `data/Work_Order_Tracker Data.xlsx` as a board named `Work Orders`.
5. Ensure the column types are mapped:
   - Dates (`Close Date`, `Tentative Close Date`, `Probable Start Date`, `Probable End Date`) -> **Date**
   - States (`Deal Status`, `Deal Stage`, `Execution Status`, `Invoice Status`) -> **Status**
   - Financials (`Masked Deal value`, `Amount in Rupees`, `Billed Value`) -> **Numbers**
   - Verticals (`Sector`, `Sector/service`) -> **Dropdown** / **Text**

### 5. Running the Application Locally
Launch the Streamlit web application:

```bash
streamlit run streamlit_app.py
```

Open your browser at `http://localhost:8501`.

---

## Streamlit Community Cloud Deployment

1. Push this repository to GitHub.
2. Go to share.streamlit.io and click **New App**.
3. Select your repository `Elaina2005/skylark`, branch `main`, and main file `streamlit_app.py`.
4. Under **Advanced Settings** -> **Secrets**, add your keys:
   ```toml
   MONDAY_API_TOKEN = "your_monday_token"
   ANTHROPIC_API_KEY = "your_anthropic_key"
   ```
5. Click **Deploy**. Your hosted application will be live immediately.

---

## Example Questions the Agent Can Answer

### Commercial and Sales Pipeline
- "What's our total deal pipeline value right now?"
- "How's our pipeline looking for the renewables and powerline sectors?"
- "What is our overall deal win rate on decided opportunities?"
- "Which sales reps have the highest open pipeline volume?"

### Operations and Execution
- "How many work orders are currently overdue?"
- "What is our operational project completion rate across all verticals?"
- "Show me all ongoing work orders in the Mining vertical."
- "What is the total billed vs receivable amount across active projects?"

### Cross-Board Intelligence
- "Which won deals haven't started work orders yet?"
- "Which sectors have the highest work order volume but the fewest won deals?"
- "Compare revenue in the deals pipeline with executed work order values by vertical."

### Executive Reporting and Quality
- "Generate a leadership update on our pipeline and operations."
- "What are our biggest data quality issues and unpopulated fields?"

---

## Known Limitations
1. **Unpopulated Historical Values:** Approximately 52% of historical deal records lack a recorded monetary value, and 66% of work orders lack an explicit delivery date in the raw dataset. The agent transparently cites these caveats when computing sums and averages.
2. **Entity Resolution on Monikers:** Deal matching across boards relies on anonymized deal monikers and rapidfuzz canonical sector mapping (threshold 85). Highly customized non-standard project names without consistent identifiers require manual correlation.
3. **API Rate Limits:** Free Monday.com accounts have rate limits; the agent includes automated backoff and 10-minute cache TTL to prevent hitting rate throttles.
