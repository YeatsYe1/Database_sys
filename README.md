<p align="center">
  <img src="https://img.shields.io/badge/Python-3.8%2B-3776AB?style=for-the-badge&logo=python&logoColor=white" alt="Python">
  <img src="https://img.shields.io/badge/Streamlit-1.28%2B-FF4B4B?style=for-the-badge&logo=streamlit&logoColor=white" alt="Streamlit">
  <img src="https://img.shields.io/badge/MySQL-8.0%2B-4479A1?style=for-the-badge&logo=mysql&logoColor=white" alt="MySQL">
  <img src="https://img.shields.io/badge/DeepSeek-Text--to--SQL-4F46E5?style=for-the-badge&logo=data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMjQiIGhlaWdodD0iMjQiIHZpZXdCb3g9IjAgMCAyNCAyNCIgZmlsbD0ibm9uZSIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48cGF0aCBkPSJNMTIgMkM2LjQ4IDIgMiA2LjQ4IDIgMTJzNC40OCAxMCAxMCAxMCAxMC00LjQ4IDEwLTEwUzE3LjUyIDIgMTIgMnptMCAxOGMtNC40MSAwLTgtMy41OS04LThzMy41OS04IDgtOCA4IDMuNTkgOCA4LTMuNTkgOC04IDh6IiBmaWxsPSJ3aGl0ZSIvPjwvc3ZnPg==" alt="DeepSeek AI">
  <img src="https://img.shields.io/badge/Matplotlib-3.5%2B-11557C?style=for-the-badge&logo=plotly&logoColor=white" alt="Matplotlib">
  <img src="https://img.shields.io/badge/Seaborn-0.12%2B-7C6B8E?style=for-the-badge&logo=python&logoColor=white" alt="Seaborn">
  <img src="https://img.shields.io/badge/Status-Defense%20Passed-22C55E?style=for-the-badge&logo=checkmarx&logoColor=white" alt="Status">
</p>

<h1 align="center">校园外卖两段式配送数据库系统</h1>

<p align="center">
  <strong>Campus Delivery Two-Stage Distribution Database System</strong><br>
  Final Defense Project · Full-Stack Data Visualization Dashboard based on MySQL + Streamlit + DeepSeek AI
</p>

<p align="center">
  <img src="https://img.shields.io/github/last-commit/your-repo/campus_delivery_project?style=flat-square&color=4F46E5" alt="Last Commit">
  <img src="https://img.shields.io/github/repo-size/your-repo/campus_delivery_project?style=flat-square&color=06B6D4" alt="Repo Size">
  <img src="https://img.shields.io/badge/license-MIT-blue?style=flat-square" alt="License">
  <img src="https://img.shields.io/badge/PRs-welcome-brightgreen?style=flat-square" alt="PRs Welcome">
</p>

---

## Project Overview

This project designs and implements a **Campus Delivery Two-Stage Distribution Database System**, integrating database engineering, real-time data visualization, and AI-powered natural language query capabilities:

| Core Feature | Description |
|-------------|-------------|
| **Two-Stage Delivery Model** | Trunk riders (merchant to pickup point) + Floor riders (pickup point to dormitory), solving the "last 500 meters" challenge in campus food delivery |
| **High-Concurrency Anti-Overselling** | MySQL row-level locking (`SELECT ... FOR UPDATE`) combined with triggers for safe inventory deduction under high concurrency |
| **Full-Lifecycle State Machine** | 6 fine-grained order status transitions with dual-rider composite tracking and full-process visualization |
| **Real-Time Data Dashboard** | Streamlit-based visualization dashboard with 5 tabs covering all operational dimensions |
| **AI-Powered Natural Language Query** | DeepSeek Text-to-SQL inference engine: input Chinese questions, automatically generate SQL queries and return result tables |

---

## Project Structure

```
campus_delivery_project/
├── campus_delivery_db.sql      # Complete database schema (DDL + stored procedures + views + seed data)
├── dashboard_app.py            # Streamlit data visualization dashboard (with AI assistant)
├── generate_mock_data.py       # Mock data generator (Faker)
├── requirements.txt            # Python dependency list
├── .env.example                # Environment variable configuration template
├── .env                        # Local environment variables (in .gitignore, never committed)
├── .gitignore                  # Git ignore rules
└── README.md                   # Project documentation (you are here)
```

---

## Quick Start

### Prerequisites

- Python 3.8+
- MySQL 8.0+ (with Window Function and SIGNAL syntax support)
- Git (optional, for version control)
- DeepSeek API Key (optional, for AI assistant, [free access](https://platform.deepseek.com/))

### Step 1: Clone / Download

```bash
git clone <repository-url>
cd campus_delivery_project
```

### Step 2: Configure Database

Execute the schema script in MySQL:

```bash
mysql -u root -p < campus_delivery_db.sql
```

This script will automatically:
- Create the database `campus_delivery_db`
- Create all tables, indexes, views, triggers, and stored procedures
- Insert preset seed data

### Step 3: Configure Environment Variables

```bash
cp .env.example .env
```

Edit the `.env` file with your configuration:

```ini
# MySQL Database Configuration
MYSQL_HOST=localhost
MYSQL_USER=root
MYSQL_PASSWORD=your_database_password
MYSQL_DATABASE=campus_delivery_db
MYSQL_CHARSET=utf8mb4

# DeepSeek AI Configuration (optional)
DEEPSEEK_API_KEY=your_deepseek_api_key
DEEPSEEK_BASE_URL=https://api.deepseek.com
DEEPSEEK_MODEL=deepseek-chat
```

> **Security Notice**: The `.env` file is listed in `.gitignore`. Do not commit it to the Git repository.

### Step 4: Install Python Dependencies

```bash
pip install -r requirements.txt
```

> It is recommended to use a virtual environment: `python -m venv venv`

### Step 5: Generate Mock Data (Optional)

```bash
python generate_mock_data.py
```

This will generate:
- **50** student users
- **15** merchants (5 dishes each)
- **1000** historical order records

### Step 6: Launch the Dashboard

```bash
streamlit run dashboard_app.py
```

The browser will open automatically. Visit **http://localhost:8501** to view the real-time data monitoring dashboard.

---

## Database Core Design

### Entity-Relationship Diagram

> **Note**: Place the E-R diagram file `er_diagram.png` in the `images/` directory. It is recommended to export using MySQL Workbench or dbdiagram.io.

<p align="center">
  <img src="images/er_diagram.png" alt="E-R Diagram" width="80%" style="border-radius: 12px; box-shadow: 0 4px 20px rgba(0,0,0,0.1);">
  <br>
  <em>Placeholder — Please export your E-R diagram as <code>images/er_diagram.png</code> to replace this placeholder</em>
</p>

### Two-Stage State Machine

```
Paid ---> Stage1_Assigned ---> Arrived_At_Point ---> Stage2_Assigned ---> Completed
  |                              |                        |
  +------------ Cancelled <------+------------------------+
```

| Status | Meaning | Description |
|--------|---------|-------------|
| `Paid` | Payment Completed | Student placed and paid for the order |
| `Stage1_Assigned` | Trunk Delivery | Trunk rider picks up from merchant and delivers to pickup point |
| `Arrived_At_Point` | Arrived at Pickup Point | Food arrives at the transfer point, awaiting floor rider |
| `Stage2_Assigned` | Floor Delivery | Floor rider picks up from point and delivers to dormitory |
| `Completed` | Completed | Student successfully received the order |
| `Cancelled` | Cancelled | Order cancelled at any stage |

### Core Table Structure

| Table | Description | Key Fields |
|-------|-------------|------------|
| `users` | Student users | `balance` (campus card), `dorm_building` |
| `merchants` | Merchant information | `rating`, `address` |
| `dishes` | Menu items | `stock` (real-time inventory), `status` (listing status) |
| `pickup_points` | Pickup transfer points | `capacity` (max slots), `current_packages` (current occupancy) |
| `riders` | Two-stage riders | `rider_type` (trunk/floor), `status` (working status) |
| `orders` | Order master table (core) | `order_status` (state machine), dual-rider ID tracking |
| `order_items` | Order line items | `quantity`, `price_at_order` (price snapshot) |

### High-Concurrency Safety Mechanisms

- **Anti-Overselling Trigger**: `trg_check_dish_stock_before_order` uses `SELECT ... FOR UPDATE` for row-level locking before inserting order items
- **Auto Stock Deduction Trigger**: `trg_reduce_dish_stock_after_order` automatically deducts inventory upon successful order placement
- **Transaction Protection**: All stored procedures include complete transaction rollback mechanisms

---

## Dashboard Features

| Tab | Functionality | Technical Implementation |
|-----|--------------|------------------------|
| **Pickup Point Saturation** | Capacity usage bar chart with overflow thresholds and status cards | Matplotlib with conditional coloring |
| **Merchant Sales Ranking** | Top 10 horizontal bar chart with data table | Seaborn gradient palette + Pandas |
| **Two-Stage Capacity Monitoring** | Order status distribution donut chart with health progress bars | Matplotlib donut chart + custom CSS |
| **Recent Order Flow** | Latest 10 order details table with colored status labels | Custom HTML table rendering |
| **AI-Powered Data Assistant** | Input Chinese questions, AI generates SQL and returns results | DeepSeek Text-to-SQL inference engine |

### AI-Powered Data Assistant -- Core Features

> **Query data in natural language -- no SQL knowledge required.**

- **Natural Language to SQL**: Integrates DeepSeek Chat model to automatically convert Chinese questions into MySQL queries
- **Schema-Aware Intelligence**: AI is pre-loaded with complete database schema information, understanding field semantics and relationships
- **Safety Interception**: Only SELECT queries are permitted; INSERT/UPDATE/DELETE operations are automatically blocked
- **Conversational Interaction**: Supports multi-turn dialogue history with one-click example questions
- **Result Visualization**: Query results displayed as Pandas DataFrames alongside the generated SQL statements

**Example Questions:**
- "Which merchant has the highest sales revenue?"
- "How many students are registered in total?"
- "What is the saturation level of each pickup point?"
- "Which dormitory building has the most orders?"

---

## Technology Stack

| Technology | Purpose |
|------------|---------|
| **Python 3.8+** | Backend logic and data processing |
| **Streamlit** | Real-time data visualization dashboard framework |
| **MySQL 8.0+** | Relational database (Window Functions, triggers, stored procedures) |
| **DeepSeek Chat** | AI Text-to-SQL inference engine |
| **Pandas** | Data cleaning and analysis |
| **Matplotlib + Seaborn** | Chart visualization |
| **PyMySQL** | Python MySQL database driver |
| **Faker** | Mock data generation |
| **python-dotenv** | Environment variable security management |

---

## Contributing

1. Fork this repository
2. Create your feature branch: `git checkout -b feature/amazing-feature`
3. Commit your changes: `git commit -m 'Add amazing feature'`
4. Push to the branch: `git push origin feature/amazing-feature`
5. Open a Pull Request

---

## License

This project is for educational purposes only.

---

<p align="center">
  <img src="https://capsule-render.vercel.app/api?type=waving&color=gradient&height=100&section=footer"/>
</p>

<p align="center">
  Campus Delivery Two-Stage Distribution Database System · Final Defense Project<br>
  Powered by Streamlit & MySQL & DeepSeek AI
</p>
