# Soccer Analytics Dashboard (2024-25)

This repository contains the first-pass deliverables for the 2024–25 Top-5 league dashboard:

- Streamlit application with 5 functional pages (League Overview, Team Stats, Player Comparison, Leaderboards, Data Browser)
- MySQL migration script for the minimal schema and indexes
- CSV → MySQL ETL utility + run log/mapping docs
- Configuration instructions and a user guide for analysts

## Project layout

```
.
├── docs/                  # data mapping, ETL log, config, user guide
├── etl/                   # CSV → MySQL loader
├── sql/                   # schema + indexes
├── streamlit_app/         # Streamlit dashboard + helpers
├── players_data-2024_2025.csv
├── requirements.txt
└── README.md
```

## Environment configuration
Create a `.env` file (ignored by git) for your local credentials:

```
cp .env.example .env
```

Fill in the loader (read/write) credentials for ETL runs. For the Streamlit app, supply the read-only credentials via `.streamlit/secrets.toml` (see example in `docs/config_instructions.md`). Both follow the same naming convention: host `localhost`, database `soccer_analytics`, users `soccer_loader` (ETL) and `soccer_app` (app), with placeholder passwords `loader_password` / `app_password`.

See `docs/config_instructions.md` for setup, migrations, ETL, and app launch steps.
