# Analyst user guide

## Global filters
- **Season** – defaults to 2024-2025; options pulled from `player_stats.season`.
- **Min minutes** – defaults to 450; works across every page to reduce small-sample noise.
- **League / Team / Position** – multi-select everywhere except Team Stats (single team focus).
- **Stat categories** – choose which metric groups (Attacking, Passing, Defensive, Goalkeeping, Possession, Misc) appear in tables across pages.
- **Show/Hide toggles** – each page provides switches to display KPI tiles, charts, and/or data tables so analysts can focus on the slice they need.
- **Per-90 toggle** – converts KPI tiles and charts to per-90 values using `value / max(minutes, 1) * 90`.
- **Exclude penalties** – Player Comparison only; swaps `goals` with `np_goals`.

## Pages
### 1. League Overview
- KPIs show the *average* of selected leagues for Goals/90, Assists/90, xG/90, xA/90, Shots/90, Defensive Actions/90 (`tackles + interceptions`), and Pass%.
- Visuals: xG/90 bar chart, Goals/90 distribution, xG vs Goals scatter, plus new possession vs pass% and goalkeeper save% views.
- Summary table includes raw totals plus per-90 metrics for every league slice.

### 2. Team Stats
- Pick a league and team to see totals, per-90 deltas vs league average, and the top five contributors to goals/xG/xA.
- The heatmap highlights where the team outperforms / underperforms its league (blue = above league avg, red = below). Additional charts cover progression (PrgP vs PrgC) and possession losses per player.
- Squad table is fully sortable and downloadable; includes per-90 metrics and Pass%.

### 3. Player Comparison
- Filter down to a league (multi-select) and optional team, then pick two players.
- Radar chart now respects your selected categories (per-90 metrics + Pass% / GK % where applicable).
- Scatter plot shows where both players land in the broader player pool (xG/90 vs xA/90, bubble size = Shots/90) and a small multiples bar view highlights key stats.
- The detail table includes both raw and per-90 stats; penalties can be excluded via the toggle.

### 4. Leaderboards
- Pick any combination of metrics (attacking, possession, defensive, goalkeeping) to build multiple Top-10 tables; each one deep-links into Player Comparison.
- Optional leaderboard chart visualises the selected metric across the top 15 players.
- Respect the global filters (season, leagues, positions, minutes, per-90).

### 5. Data Browser
- Power-user filter for any combination of Season/League/Team/Position and minute threshold.
- Choose the stat categories you want, paginate (25/50/100/200 rows per page), and export the current slice via the download button. A quick metric histogram is available for any numeric column.

## KPI definitions
- **Pass%** – completed passes / attempted passes.
- **Defensive actions** – tackles + interceptions (pressures are not available in the light CSV; this proxy is surfaced in KPI labels and documentation).
- **Per-90** – `metric / max(minutes, 1) * 90` computed client-side for transparency.
- **Team defensive intensity** – squad-wide defensive actions divided by team minutes, then multiplied by 90.

## Known limits & follow-ups
- CSV source lacks pressure counts; replacing the defensive proxy with true pressures is first priority when richer data is available.
- `player_stats` currently holds a single season. Adding 2023-24 (and beyond) simply requires re-running the ETL with a different `--season` flag.
- Radar scaling mixes Pass% (0-100) with per-90 counts; for Phase 2 consider normalization/z-scores.
- Leaderboard deep links rely on Streamlit query parameters. If deploying behind a proxy, ensure URL rewriting preserves `?page=...` parameters.
- Role-based radars, player clustering, xGD, and bookmarkable URLs are outlined in the Phase-2 section of the product brief.
