# Database_sys

Final project for database course. 校园外卖两段式配送数据库系统。

## Project Structure

```
├── app.py                          # Streamlit entry point
├── src/
│   └── campus_delivery/            # Python package
│       ├── __init__.py
│       ├── app.py                  # Main dashboard layout
│       ├── config.py               # Colors, CSS, page config, DB schema
│       ├── db.py                   # Database connection + query functions
│       ├── charts.py               # Matplotlib chart rendering
│       └── ai_assistant.py         # DeepSeek AI Text-to-SQL
├── sql/
│   └── campus_delivery_db.sql      # Full database DDL + triggers + procedures + seeds
├── scripts/
│   ├── generate_mock_data.py       # Mock data generator
│   ├── check_data.py               # Data integrity checker
│   └── reinit_db.py                # Database rebuild script
├── images/
│   └── er_diagram.png              # E-R diagram
├── requirements.txt
├── .env.example
├── .gitignore
├── .gitattributes
└── LICENSE
```

## Quick Start

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Create database
mysql -u root -p < sql/campus_delivery_db.sql
# or: python scripts/reinit_db.py

# 3. Configure environment
cp .env.example .env
# Edit .env with your database credentials

# 4. Generate mock data (optional)
python scripts/generate_mock_data.py

# 5. Launch dashboard
streamlit run app.py
```
