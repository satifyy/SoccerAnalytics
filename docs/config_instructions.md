# Configuration & Runbook

## 1. Prerequisites
- Python 3.10+
- MySQL 8.x instance (schema owner for migrations + read-only app user)
- `players_data-2024_2025.csv` in the repository root (current snapshot)

Install Python deps locally:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## 2. Database setup
1. Create a dedicated database (e.g., `soccer_analytics`).
2. Apply the schema + indexes:
   ```bash
   mysql -u <admin_user> -p soccer_analytics < sql/001_create_soccer_schema.sql
   ```
3. Create users:
   ```sql
   CREATE USER 'soccer_loader'@'%' IDENTIFIED BY '***';
   GRANT INSERT, UPDATE, SELECT ON soccer_analytics.* TO 'soccer_loader'@'%';

   CREATE USER 'soccer_app'@'%' IDENTIFIED BY '***';
   GRANT SELECT ON soccer_analytics.* TO 'soccer_app'@'%';
   ```
4. (Optional) Run `ANALYZE TABLE player_stats;` after each ETL to keep statistics fresh.

## 3. ETL execution
1. Export credentials (or create a `.env` file) for the loader user:
   ```bash
   export DB_HOST=localhost
   export DB_PORT=3306
   export DB_NAME=soccer_analytics
   export DB_USER=soccer_loader
   export DB_PASSWORD=loader_password
   ```
2. Run the loader:
   ```bash
   python etl/csv_to_mysql.py --csv players_data-2024_2025.csv --season 2024-2025
   ```
   The script upserts leagues → teams → players and then ingests `player_stats` in batches of 500 rows.
3. Record the console output and update `docs/etl_run_log.md` with the actual run date/time.

## 4. Streamlit app configuration
Set the read-only credentials for the dashboard via Streamlit secrets (recommended) or by exporting the same keys (`DB_HOST`, `DB_PORT`, `DB_NAME`, `DB_USER`, `DB_PASSWORD`) in your shell before launching the app.

**Streamlit secrets** (`.streamlit/secrets.toml`)
```toml
[mysql]
host = "localhost"
port = 3306
database = "soccer_analytics"
user = "soccer_app"
password = "app_password"
```

## 5. Run the dashboard
```bash
streamlit run streamlit_app/app.py
```

Notes:
- All heavy queries are cached for 5 minutes via `st.cache_data`.
- The app enforces the 450-minute default but allows analysts to override it.
- No secrets are stored in the repository; everything comes from env vars or Streamlit secrets at runtime.
- The Streamlit service only needs read-only access; verify grants before deploying.
