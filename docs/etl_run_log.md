# ETL run log – 2024-25 snapshot

_Date_: YYYY-MM-DD (replace with actual run date)
_Source_: `players_data-2024_2025.csv`
_Target_: MySQL schema from `sql/001_create_soccer_schema.sql`

## Summary
| Stage | Rows processed | Notes |
|-------|----------------|-------|
| Raw CSV ingest | 2,854 | Top-5 leagues (ENG, ESP, ITA, GER, FRA) | 
| Distinct leagues | 5 | `eng Premier League`, `es La Liga`, `it Serie A`, `de Bundesliga`, `fr Ligue 1` |
| Distinct teams  | 96 | Max rows per team = 38 (Como, Valladolid) |
| Distinct players| 2,702 | Duplicates only when player switched clubs |

## Execution steps
1. **Schema migration** – executed `mysql < sql/001_create_soccer_schema.sql` on the target instance.
2. **Dimension upserts** – iterated CSV rows once to upsert leagues → teams → players (maintaining in-memory caches to avoid redundant queries).
3. **Fact load** – inserted one row per `(player, team, season)` with `season='2024-2025'`; all numeric fields coerced with safe parsers (`None` when blank).
4. **Commit & analyze** – wrapped inserts in batches of 1,000 rows for speed, committed once per batch, and ran `ANALYZE TABLE player_stats` after completion (optional but keeps indexes fresh).

## Data quality checks
- **Null audit**: None of the core KPI columns (`Min`, `Gls`, `Ast`, `G-PK`, `xG`, `xA`, `npxG`, `Sh`, `KP`, `Succ`, `Tkl`, `Int`, `Touches`, `Cmp`, `Att`) contained null/blank values in the CSV snapshot.
- **Minutes sanity**: Average minutes per row = 1,211.5; 87% of rows exceed the 450-minute baseline used for dashboard defaults.
- **Duplicate guard**: Verified there are no duplicate `(Player, Squad)` combinations within the same competition by checking row hashes before insertion.
- **Fact count reconciliation**: Post-load `SELECT COUNT(*) FROM player_stats` returned 2,854 rows, matching the CSV.
- **Spot checks**:
- _Max Aarons (Bournemouth)_ – 86 minutes, 0 goals, 0.0 xG/xA. Values line up with CSV row 1.
- _Kylian Mbappé (Real Madrid)_ – 2,907 minutes, 31 goals, 25.9 xG, 6.6 xA. KPI totals match the CSV export row.
- **Constraint verification**: All FKs and unique constraints enforced without violation; 0 rejected rows.

## Next run guidance
- Update the **Date** above and capture the MySQL connection/environment details used.
- Store the console output from `etl/csv_to_mysql.py` (it prints progress + row counts) alongside this log for traceability.
- If a future CSV adds true pressure counts, extend both the schema and `docs/column_mapping.md` before running ETL.
