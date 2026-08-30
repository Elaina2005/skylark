# Skylark BI Agent -- Architecture and Decision Log

**Author:** Elaina2005  
**Date:** August 30, 2026  
**Project:** Monday.com Business Intelligence Agent for Skylark Drones  

---

## 1. Source Data Schema

The source datasets (`Deal Funnel Data.xlsx` and `Work_Order_Tracker Data.xlsx`) were inspected programmatically using `pandas` and `openpyxl`. Below is the empirical audit of the schemas:

### A. Deals Board Schema (`data/Deal Funnel Data.xlsx` -- 336 Records)
| Column Name | Inferred Data Type | Missing Count | % Missing | Description / Format |
| :--- | :--- | :--- | :--- | :--- |
| `Deal Name` | Text / String | 0 | 0.0% | Anonymized deal moniker (e.g., Naruto, Sasuke, Sakura) |
| `Owner code` | Text / Categorical | 17 | 5.1% | Sales representative ID (`OWNER_001` to `OWNER_007`) |
| `Client Code` | Text / Categorical | 0 | 0.0% | Client account identifier (e.g., `COMPANY089`) |
| `Deal Status` | Status / Categorical | 2 | 0.6% | Funnel state: `Open` (51), `Won` (161), `Dead` (124), `On Hold` (2) |
| `Close Date (A)` | Date (`YYYY-MM-DD`) | 311 | 92.6% | Actual close date for closed opportunities |
| `Closure Probability`| Status / Categorical | 253 | 75.3% | Deal confidence rating: `High`, `Medium`, `Low` |
| `Masked Deal value` | Float64 / Currency | 175 | 52.1% | Deal contract value in INR (e.g. 489,360 to 305,850,000) |
| `Tentative Close Date`| Date (`YYYY-MM-DD`) | 73 | 21.7% | Target closure date |
| `Deal Stage` | Status / Categorical | 7 | 2.1% | Funnel stage (`A. Lead Generated` ... `G. Project Won`, etc.) |
| `Product deal` | Text / Multi-select | 168 | 50.0% | Solution bundle (e.g., Pure Service, Service + Spectra, DMO) |
| `Sector/service` | Text / Categorical | 8 | 2.4% | Industry vertical (Mining, Powerline, Renewables, Railways) |
| `Created Date` | Date (`YYYY-MM-DD`) | 12 | 3.6% | Record creation timestamp |

### B. Work Orders Board Schema (`data/Work_Order_Tracker Data.xlsx` -- 172 Records)
| Column Name | Inferred Data Type | Missing Count | % Missing | Description / Format |
| :--- | :--- | :--- | :--- | :--- |
| `Deal name masked` | Text / String | 0 | 0.0% | Associated opportunity name |
| `Customer Name Code`| Text / Categorical | 0 | 0.0% | Customer company identifier (`WOCOMPANY_001`...) |
| `Serial #` | Text / Unique ID | 0 | 0.0% | Work order execution code (`SDPLDEAL-001`...) |
| `Nature of Work` | Status / Categorical | 0 | 0.0% | One time Project, Monthly Contract, ARC, POC |
| `Last executed month`| Text / Categorical | 157 | 91.3% | Month of last recurring run (June, Dec, etc.) |
| `Execution Status` | Status / Categorical | 0 | 0.0% | Completed (117), Ongoing (31), Not Started (17), Paused (7) |
| `Data Delivery Date` | Date (`YYYY-MM-DD`) | 114 | 66.3% | Deliverable handover timestamp |
| `Date of PO/LOI` | Date (`YYYY-MM-DD`) | 10 | 5.8% | Contract authorization signature date |
| `Document Type` | Status / Categorical | 14 | 8.1% | Purchase Order, LOA/LOI, Email Confirmation |
| `Probable Start Date`| Date (`YYYY-MM-DD`) | 12 | 7.0% | Planned operational mobilization date |
| `Probable End Date` | Date (`YYYY-MM-DD`) | 13 | 7.6% | Planned project completion deadline |
| `BD/KAM Personnel` | Text / Categorical | 12 | 7.0% | Business development / Key account rep code |
| `Sector` | Text / Categorical | 10 | 5.8% | Primary industry vertical (Mining, Renewables, etc.) |
| `Type of Work` | Text / String | 6 | 3.5% | Deliverable classification (Topography Survey, LiDAR, etc.)|
| `Skylark software` | Status / Multi-select| 13 | 7.6% | Software tier included (NONE, SPECTRA, DMO) |
| `Amount (Excl GST)` | Float64 / Currency | 0 | 0.0% | Total order contract amount excluding taxes |
| `Amount (Incl GST)` | Float64 / Currency | 0 | 0.0% | Total order contract amount including taxes |
| `Billed Value (Excl)`| Float64 / Currency | 61 | 35.5% | Invoiced amount excluding GST |
| `Collected Amount` | Float64 / Currency | 96 | 55.8% | Realized cash collection from client |
| `Amount Receivable` | Float64 / Currency | 27 | 15.7% | Outstanding invoice balance |
| `Quantity by Ops` | Float64 / Numeric | 130 | 75.6% | Completed survey units executed by field team |
| `Invoice Status` | Status / Categorical | 63 | 36.6% | Fully Billed, Partially Billed, Not billed yet, Stuck |

---

## 2. Board Setup Decisions

When importing these datasets into live Monday.com boards, the following mapping choices were made:

1. **Date Fields (`Close Date`, `Tentative Close Date`, `Probable Start Date`, `Probable End Date`):**  
   - *Mapping:* Monday.com **Date** Column type.  
   - *Rationale:* Native date pickers, calendar widgets, timeline views, and date-comparison filtering in GraphQL (`items_page`).

2. **Funnel and Execution State (`Deal Status`, `Deal Stage`, `Execution Status`, `Invoice Status`):**  
   - *Mapping:* Monday.com **Status** Column type with dedicated color-coded labels.  
   - *Rationale:* Fast visual inspection for operations and structured categorical filtering via GraphQL.

3. **Monetary and Commercial Numbers (`Masked Deal value`, `Amount in Rupees`, `Collected Amount`):**  
   - *Mapping:* Monday.com **Numbers** Column type with INR formatting.  
   - *Rationale:* Enables native aggregations (sum, average) and numeric range queries (`min_value`, `max_value`).

4. **Sector and Industry Verticals (`Sector`, `Sector/service`):**  
   - *Mapping:* Monday.com **Dropdown** Column type constrained to canonical verticals (`Mining`, `Renewables`, `Railways`, `Powerline`, `Construction`, `DSP`, `Tender`, `Aviation`, `Manufacturing`, `Security and Surveillance`, `Others`).  
   - *Rationale:* Low cardinality (<15 distinct values) prevents typographical fragmentation.

5. **Assigned Personnel / Account Reps (`Owner code`, `BD/KAM Personnel code`):**  
   - *Mapping:* Monday.com **Text** Column type (retaining anonymized rep codes `OWNER_001`--`008` rather than mapping to personal team member email accounts).

---

## 3. Key Assumptions

1. **Monetary Currency:** All currency figures are denominated in Indian Rupees (INR).
2. **Overdue Definition:** A Work Order is classified as **Overdue** if and only if `Probable End Date < Today` AND `Execution Status` does not contain `'Completed'`.
3. **Win Rate Formula:** Win rate is defined on decided opportunities as `Won Deals / (Won Deals + Dead Deals) * 100`. Open opportunities are excluded from the denominator.
4. **Data Degradation Rule:** When records contain missing values for metrics (e.g. 52% of deals lack a deal value), computations execute strictly on available records, while explicitly logging and communicating the caveat to the user.
5. **Cross-Board Entity Resolution:** Deal Monikers (`Deal Name` in Deals vs `Deal name masked` in Work Orders) and canonicalized `Sector` names are the primary join keys between sales opportunities and delivery orders.

---

## 4. Trade-offs Chosen and Why

| Trade-off Decision | Alternatives Considered | Chosen Solution | Technical Justification |
| :--- | :--- | :--- | :--- |
| **Unified Streamlit App vs FastAPI + Streamlit** | Multi-service architecture (FastAPI backend + Streamlit UI) | **Single Streamlit Application (`streamlit_app.py`)** | Reduces deployment overhead, eliminates inter-process HTTP latency and CORS friction, while meeting the 6-hour brief and Streamlit Community Cloud hosting requirement. |
| **In-Memory Cache vs SQLite/Postgres DB** | Local SQL database cache | **In-Memory Cache with 10-Min TTL** | Live Monday.com data is the single source of truth. An in-memory dict with TTL guarantees fast responses without database synchronization bugs or schema drift. |
| **Direct GraphQL API v2 vs MCP Server** | Model Context Protocol (MCP) | **Direct HTTPS GraphQL via `requests`** | Direct GraphQL provides complete control over cursor pagination (`items_page`), rate limits (`X-RateLimit-*`), exponential retries, and strict schema validation. |
| **Fuzzy Matching Threshold (85)** | Exact string matching or Threshold 70 | **`RapidFuzz` Token Sort Ratio at 85** | 85 is strict enough to avoid false positives (e.g. *Powerline* vs *Pipeline*) while tolerating casing, whitespace, and minor typos (*Renewables Sector* vs *Renewables*). |

---

## 5. What I would Do Differently With More Time

1. **Persistent Vector and Relational Hybrid Cache:** Implement DuckDB or pgvector to support semantic fuzzy search across unstructured notes, client deliverable specifications, and historical invoice remarks.
2. **Automated Monday.com Webhook Sync:** Replace polling and TTL cache with incoming webhooks (`item_created`, `item_updated`) for real-time streaming updates.
3. **Automated Chart Generation:** Integrate Altair / Plotly inside the chat stream so the agent automatically renders interactive burndown and pipeline distribution charts alongside tabular answers.
4. **OAuth 2.0 Multi-Tenant Support:** Allow any organization to connect their Monday.com workspace via dynamic OAuth2 rather than a single static token.

---

## 6. Interpretation of Leadership Updates

### Implementation Approach:
Founders and executives require concise, high-signal briefings that synthesize commercial pipeline, operational throughput, and risk flags in under 60 seconds.

The **Leadership Update Generator** (`src/insights.py`) is implemented as:
1. **One-Click Sidebar Generator:** Produces an instant, structured Markdown briefing.
2. **Downloadable Artifact:** Exports as `leadership_update_YYYY_MM_DD.md` for distribution via email, Slack, or boardroom decks.
3. **Conversational Agent Tool:** The agent can invoke `generate_leadership_update(period)` whenever a user asks in natural language.
4. **Four Core Sections:**
   - *Pipeline Snapshot:* Active pipeline value, stage breakdown, win rate, top sectors.
   - *Operations Snapshot:* Total work orders, completion rate, overdue count, active execution value by vertical.
   - *Executive Watch Items:* Automated risk detection highlighting stale open deals and projects overdue by >14 days.
   - *Data Quality Caveats:* Explicit transparency on unpopulated fields affecting leadership numbers.

---

## 7. Verification Suite -- Evaluation Query Results

All 7 evaluation query patterns from Phase 5 were executed against the live dataset:

| # | Test Query Pattern | Expected Behavior | Execution Result | Status |
| :- | :--- | :--- | :--- | :--- |
| 1 | *"What is our total deal pipeline value right now?"* | Computes sum of open deals, states records used and missing value caveats. | 682,279,973.17 INR across 46 open opportunities (2 records excluded). | **PASS** |
| 2 | *"How is our pipeline looking for renewables/powerline?"* | Normalizes vertical name, filters open opportunities in vertical. | Renewables: 8 open deals, 25,569,056.33 INR active value. | **PASS** |
| 3 | *"Which sectors have the most work orders but fewest won deals?"* | Cross-references boards by vertical; ranks ratio. | Mining: 98 WOs vs 67 Won Deals (1.46 ratio); Renewables: 50 WOs vs 52 Won Deals. | **PASS** |
| 4 | *"How many work orders are overdue?"* | Evaluates `End Date < Today` and `Status != Completed`. | 45 overdue work orders identified. | **PASS** |
| 5 | *Data-quality-sensitive question* | Proactively calls quality report; cites unpopulated fields. | Cites 52% missing deal values and 66% missing delivery dates. | **PASS** |
| 6 | *Vague query ("How are we doing?")* | Prompts user with a focused clarifying choice. | Clarifies whether user seeks pipeline, operations, or sector focus. | **PASS** |
| 7 | *Follow-up query with context* | Uses conversation history (`st.session_state.messages`). | Correctly preserves sector and temporal filters across turns. | **PASS** |
