# CSV → MySQL column mapping

Source file: `players_data-2024_2025.csv` (FBRef export snapshot, 2,854 rows).
Season enforced as `2024-2025` for all records.

| Target table.column        | Type             | Source column            | Notes/Transformations |
|---------------------------|------------------|--------------------------|-----------------------|
| leagues.league_name       | VARCHAR(64)      | `Comp`                   | Trim whitespace, unique constraint. |
| teams.team_name           | VARCHAR(64)      | `Squad`                  | Stored alongside `league_id` to disambiguate duplicates. |
| players.player_name       | VARCHAR(96)      | `Player`                 | UTF-8 safe; keep FBRef spelling. |
| players.nationality       | VARCHAR(32)      | `Nation`                 | Leave compound codes as-is (`eng ENG`). |
| players.primary_position  | VARCHAR(16)      | `Pos`                    | First value before comma if multiple roles exist. |
| player_stats.season       | VARCHAR(16)      | literal                  | Hard-coded to `2024-2025`. |
| player_stats.player_id    | FK               | lookup                   | From `players`. |
| player_stats.team_id      | FK               | lookup                   | From `teams`. |
| player_stats.league_id    | FK               | lookup                   | From `leagues`. |
| player_stats.position     | VARCHAR(16)      | `Pos`                    | Entire string preserved for per-team context. |
| player_stats.apps         | SMALLINT         | `MP`                     | Parsed as int; null → 0. |
| player_stats.starts       | SMALLINT         | `Starts`                 | Parsed as int; null → 0. |
| player_stats.minutes      | INT              | `Min`                    | Parsed as int; null → 0. |
| player_stats.goals        | SMALLINT         | `Gls`                    | Parsed as int. |
| player_stats.assists      | SMALLINT         | `Ast`                    | Parsed as int. |
| player_stats.np_goals     | SMALLINT         | `G-PK`                   | FBRef already removes PKs. |
| player_stats.penalties    | SMALLINT         | `PK`                     | PK goals. |
| player_stats.penalty_att  | SMALLINT         | `PKatt`                  | Penalty attempts. |
| player_stats.xg           | DECIMAL(6,3)     | `xG`                     | 3 decimal precision. |
| player_stats.xa           | DECIMAL(6,3)     | `xA`                     | From passing table, captures expected assists. |
| player_stats.npxg         | DECIMAL(6,3)     | `npxG`                   | Used when penalties excluded. |
| player_stats.shots        | SMALLINT         | `Sh`                     | Total shot attempts. |
| player_stats.shots_on_target| SMALLINT       | `SoT`                    | Enables SoT% if needed later. |
| player_stats.key_passes   | SMALLINT         | `KP`                     | Key passes from passing table. |
| player_stats.dribbles     | SMALLINT         | `Succ`                   | Successful take-ons; dataset lacks raw "pressures" so dribbles proxy is successes. |
| player_stats.tackles      | SMALLINT         | `Tkl`                    | Tackles attempted. |
| player_stats.interceptions| SMALLINT         | `Int`                    | Interceptions column from defense block. |
| player_stats.touches      | SMALLINT         | `Touches`                | Total touches. |
| player_stats.passes_completed| SMALLINT      | `Cmp`                    | Total completed passes. |
| player_stats.passes_attempted| SMALLINT      | `Att`                    | Passing attempts. |
| player_stats.progressive_passes| SMALLINT    | `PrgP`                   | Progressive passes completed. |
| player_stats.progressive_carries| SMALLINT   | `PrgC`                   | Progressive carries. |
| player_stats.progressive_receptions| SMALLINT| `PrgR`                   | Enables receiving focus later. |
| player_stats.shot_creating_actions| SMALLINT | `SCA`                    | Not core KPI but retained for enrichment. |
| player_stats.goal_creating_actions| SMALLINT | `GCA`                    | Optional KPI on Team Stats page. |

### Additional categorical stats
- `player_stats.yellow_cards` / `player_stats.red_cards` ← `CrdY`, `CrdR`
- `player_stats.passes_into_pen_area` ← `PPA`
- `player_stats.tackles_won` ← `TklW`
- `player_stats.blocks` ← `Blocks`
- `player_stats.clearances` ← `Clr`
- `player_stats.errors` ← `Err`
- `player_stats.fouls_committed` / `fouls_drawn` ← `Fls`, `Fld`
- `player_stats.offsides` ← `Off`
- `player_stats.penalties_won` / `penalties_conceded` ← `PKwon`, `PKcon`
- `player_stats.own_goals` ← `OG`
- `player_stats.recoveries` ← `Recov`
- `player_stats.miscontrols` / `dispossessed` ← `Mis`, `Dis`
- `player_stats.carries` ← `Carries`
- Goalkeeping: `goals_against (GA)`, `goals_against_per90 (GA90)`, `shots_on_target_against (SoTA)`, `saves`, `save_pct`, `wins (W)`, `draws (D)`, `losses (L)`, `clean_sheets (CS)`, `clean_sheet_pct (CS%)`, `penalty_kicks_faced (PKA)`, `penalty_kicks_saved (PKsv)`, `penalty_kicks_missed_against (PKm)`

## Missing / derived fields
- **Pressures** are not provided in the light CSV export. Defensive intensity metrics use `(tackles + interceptions)` as the closest available proxy and this is documented wherever surfaced in the app.
- `Pass%` is computed in the app as `passes_completed / NULLIF(passes_attempted, 0)`.
- Per-90 metrics are computed client-side using `metric / max(minutes, 1) * 90`.
- Team aggregates and league averages are calculated on demand in the Streamlit layer to keep the warehouse minimal.
