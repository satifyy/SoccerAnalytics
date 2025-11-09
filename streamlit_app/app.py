from __future__ import annotations

import math
from typing import Dict, List, Optional
from urllib.parse import quote

import pandas as pd
import streamlit as st

from utils import charts
from utils import transforms as tf
from utils.data_access import (
    fetch_player_stats,
    fetch_team_summary,
    get_leagues,
    get_positions,
    get_seasons,
    get_teams,
)

PAGE_OPTIONS = [
    "League Overview",
    "Team Stats",
    "Player Comparison",
    "Leaderboards",
    "Data Browser",
]

DEFAULT_SEASON = "2024-2025"
DEFAULT_MIN_MINUTES = 450

st.set_page_config(page_title="Top-5 Dashboard", layout="wide", page_icon="⚽")


def pass_pct_from_df(df: pd.DataFrame) -> float:
    attempted = df["passes_attempted"].sum()
    if attempted == 0:
        return 0.0
    return (df["passes_completed"].sum() / attempted) * 100


def init_state() -> None:
    params = st.query_params
    default_page = params.get("page", [PAGE_OPTIONS[0]])[0]
    if default_page not in PAGE_OPTIONS:
        default_page = PAGE_OPTIONS[0]
    st.session_state.setdefault("current_page", default_page)


def update_query_params(**kwargs) -> None:
    qp = st.query_params
    for key, value in kwargs.items():
        if value is None:
            qp.pop(key, None)
        else:
            qp[key] = value


def get_default_index(options: List[str], target: str) -> int:
    if target in options:
        return options.index(target)
    return 0 if options else 0


def load_reference_data() -> Dict[str, List[str]]:
    try:
        seasons = get_seasons()
    except Exception as exc:  # pragma: no cover
        st.error(f"Database connection failed: {exc}")
        st.stop()
    if not seasons:
        st.warning("player_stats table is empty. Run the ETL before launching the dashboard.")
        st.stop()
    return {"seasons": seasons}


def sidebar_filters(page: str, ref: Dict[str, List[str]]):
    st.sidebar.title("Filters")
    seasons = ref["seasons"]
    default_season = DEFAULT_SEASON if DEFAULT_SEASON in seasons else seasons[0]
    season = st.sidebar.selectbox("Season", seasons, index=get_default_index(seasons, default_season), key=f"season_{page}")
    leagues = get_leagues(season)

    if page == "League Overview":
        selected_leagues = st.sidebar.multiselect("Leagues", leagues, default=leagues)
        min_minutes = st.sidebar.number_input("Min minutes", min_value=0, value=DEFAULT_MIN_MINUTES, step=90)
        per90 = st.sidebar.toggle("Per-90 view", value=True, key="per90_league")
        return {
            "season": season,
            "leagues": selected_leagues or leagues,
            "min_minutes": min_minutes,
            "per90": per90,
        }

    if page == "Team Stats":
        league = st.sidebar.selectbox("League", leagues, index=0)
        teams = get_teams(season, [league])
        team = st.sidebar.selectbox("Team", teams, index=0)
        min_minutes = st.sidebar.number_input("Min minutes", min_value=0, value=DEFAULT_MIN_MINUTES, step=90)
        return {
            "season": season,
            "league": league,
            "team": team,
            "min_minutes": min_minutes,
        }

    if page == "Player Comparison":
        selected_leagues = st.sidebar.multiselect("League(s)", leagues, default=leagues)
        teams = ["All teams"] + get_teams(season, selected_leagues)
        team = st.sidebar.selectbox("Team (optional)", teams, index=0)
        min_minutes = st.sidebar.number_input("Min minutes", min_value=0, value=DEFAULT_MIN_MINUTES, step=90)
        per90 = st.sidebar.toggle("Per-90 view", value=True, key="per90_pc")
        exclude_pk = st.sidebar.toggle("Exclude penalties (use NP Goals)", value=False, key="exclude_pk")
        return {
            "season": season,
            "leagues": selected_leagues or leagues,
            "team": None if team == "All teams" else team,
            "min_minutes": min_minutes,
            "per90": per90,
            "exclude_pk": exclude_pk,
        }

    if page == "Leaderboards":
        selected_leagues = st.sidebar.multiselect("League(s)", leagues, default=leagues)
        positions = get_positions(season)
        selected_positions = st.sidebar.multiselect("Position", positions)
        min_minutes = st.sidebar.number_input("Min minutes", min_value=0, value=DEFAULT_MIN_MINUTES, step=90)
        per90 = st.sidebar.toggle("Per-90 view", value=True, key="per90_lb")
        return {
            "season": season,
            "leagues": selected_leagues or leagues,
            "positions": selected_positions,
            "min_minutes": min_minutes,
            "per90": per90,
        }

    if page == "Data Browser":
        selected_leagues = st.sidebar.multiselect("League(s)", leagues, default=leagues)
        teams = get_teams(season, selected_leagues)
        selected_teams = st.sidebar.multiselect("Team", teams)
        positions = get_positions(season)
        selected_positions = st.sidebar.multiselect("Position", positions)
        min_minutes = st.sidebar.number_input("Min minutes", min_value=0, value=DEFAULT_MIN_MINUTES, step=90)
        per90 = st.sidebar.toggle("Include per-90 columns", value=True, key="per90_browser")
        return {
            "season": season,
            "leagues": selected_leagues or leagues,
            "teams": selected_teams,
            "positions": selected_positions,
            "min_minutes": min_minutes,
            "per90": per90,
        }

    return {"season": season}


def handle_empty(df: pd.DataFrame, message: str = "No data found for the current filters.") -> bool:
    if df.empty:
        st.info(message)
        return True
    return False


def render_league_overview(filters: dict) -> None:
    st.header("League Overview")
    df = fetch_player_stats(filters["season"], filters["min_minutes"], filters["leagues"])
    if handle_empty(df):
        return
    df = tf.enrich_players(df)
    league_df = tf.aggregate_by_league(df)

    per90_cols = ["goals_per90", "assists_per90", "xg_per90", "xa_per90", "shots_per90", "def_actions_per90"]
    cols = [col for col in per90_cols if col in league_df.columns]
    kpi_cols = {
        "Goals/90": league_df["goals_per90"].mean(),
        "Assists/90": league_df["assists_per90"].mean(),
        "xG/90": league_df["xg_per90"].mean(),
        "xA/90": league_df["xa_per90"].mean(),
        "Shots/90": league_df["shots_per90"].mean(),
        "Def actions/90": league_df["def_actions_per90"].mean(),
        "Pass%": league_df["pass_pct"].mean(),
    }

    kpi_cols = {k: round(v, 2) for k, v in kpi_cols.items() if not math.isnan(v)}
    cols_per_row = 3
    cols_container = st.columns(cols_per_row)
    for idx, (label, value) in enumerate(kpi_cols.items()):
        with cols_container[idx % cols_per_row]:
            st.metric(label, value)

    charts_cols = st.columns(3)
    with charts_cols[0]:
        st.altair_chart(charts.league_xg_bar(league_df, filters["per90"]), use_container_width=True)
    with charts_cols[1]:
        st.altair_chart(charts.league_goals_box(df), use_container_width=True)
    with charts_cols[2]:
        st.altair_chart(charts.league_scatter(league_df, filters["per90"]), use_container_width=True)

    st.subheader("League summary table")
    display_cols = [
        "league_name",
        "players",
        "minutes",
        "goals",
        "assists",
        "xg",
        "xa",
        "shots",
        "key_passes",
        "pass_pct",
        "goals_per90",
        "xg_per90",
        "shots_per90",
        "def_actions_per90",
    ]
    table = league_df[display_cols].round(2)
    st.dataframe(table, hide_index=True, use_container_width=True)


def render_team_stats(filters: dict) -> None:
    st.header("Team Stats")
    df = fetch_team_summary(filters["season"], filters["league"], filters["team"], filters["min_minutes"])
    if handle_empty(df, "Select another team or relax the minute filter."):
        return
    df = tf.enrich_players(df)
    total_minutes = max(df["minutes"].sum(), 1)
    team_totals = {
        "Minutes": int(total_minutes),
        "Goals": int(df["goals"].sum()),
        "xG": round(df["xg"].sum(), 2),
        "Assists": int(df["assists"].sum()),
        "xA": round(df["xa"].sum(), 2),
        "Shots": int(df["shots"].sum()),
        "Pass%": round(pass_pct_from_df(df), 2),
        "Def actions/90": round(((df["tackles"].sum() + df["interceptions"].sum()) / total_minutes) * 90, 2),
    }
    col_objs = st.columns(4)
    for idx, (label, value) in enumerate(team_totals.items()):
        with col_objs[idx % 4]:
            st.metric(label, value)

    st.markdown("### Top contributors (Goals/xG/xA)")
    top_players = df.sort_values("goals", ascending=False).head(5)[
        ["player_name", "goals", "xg", "assists", "xa"]
    ]
    st.altair_chart(charts.stacked_player_contributions(top_players), use_container_width=True)

    st.markdown("### Team vs league (per-90 deltas)")
    team_per90 = df.sum(numeric_only=True)
    minutes = total_minutes
    per90_metrics = {
        "Goals/90": (team_per90["goals"] / minutes) * 90,
        "xG/90": (team_per90["xg"] / minutes) * 90,
        "Assists/90": (team_per90["assists"] / minutes) * 90,
        "xA/90": (team_per90["xa"] / minutes) * 90,
        "Shots/90": (team_per90["shots"] / minutes) * 90,
        "Key passes/90": (team_per90["key_passes"] / minutes) * 90,
        "Def actions/90": ((team_per90["tackles"] + team_per90["interceptions"]) / minutes) * 90,
        "Pass%": pass_pct_from_df(df),
    }
    team_metric_df = pd.DataFrame({"metric": per90_metrics.keys(), "value": per90_metrics.values()})

    league_df = fetch_player_stats(filters["season"], filters["min_minutes"], [filters["league"]])
    league_df = tf.enrich_players(league_df)
    league_minutes = max(league_df["minutes"].sum(), 1)
    league_metric_values = {
        "Goals/90": (league_df["goals"].sum() / league_minutes) * 90,
        "xG/90": (league_df["xg"].sum() / league_minutes) * 90,
        "Assists/90": (league_df["assists"].sum() / league_minutes) * 90,
        "xA/90": (league_df["xa"].sum() / league_minutes) * 90,
        "Shots/90": (league_df["shots"].sum() / league_minutes) * 90,
        "Key passes/90": (league_df["key_passes"].sum() / league_minutes) * 90,
        "Def actions/90": ((league_df["tackles"].sum() + league_df["interceptions"].sum()) / league_minutes) * 90,
        "Pass%": pass_pct_from_df(league_df),
    }
    league_metric_df = pd.DataFrame({"metric": league_metric_values.keys(), "value": league_metric_values.values()})
    team_metric_df = team_metric_df.rename(columns={"value": "value_team"})
    league_metric_df = league_metric_df.rename(columns={"value": "value_league"})
    st.altair_chart(charts.team_heatmap(team_metric_df, league_metric_df), use_container_width=True)

    st.markdown("### Squad detail (per-90)")
    table_cols = [
        "player_name",
        "position",
        "apps",
        "minutes",
        "goals",
        "assists",
        "xg",
        "xa",
        "shots",
        "key_passes",
        "dribbles",
        "def_actions",
        "goals_per90",
        "xg_per90",
        "assists_per90",
        "shots_per90",
        "key_passes_per90",
        "def_actions_per90",
        "pass_pct",
    ]
    squad_table = df[table_cols].round(2)
    st.dataframe(squad_table, hide_index=True, use_container_width=True)
    csv = squad_table.to_csv(index=False).encode("utf-8")
    st.download_button("Download CSV", csv, file_name=f"{filters['team'].lower().replace(' ', '_')}_squad.csv")


def render_player_comparison(filters: dict) -> None:
    st.header("Player Comparison")
    df = fetch_player_stats(
        filters["season"],
        filters["min_minutes"],
        filters["leagues"],
        [filters["team"]] if filters.get("team") else None,
    )
    if handle_empty(df, "No players found for the current filter set."):
        return
    df = tf.enrich_players(df)
    players = df["player_name"].unique().tolist()

    params = st.query_params
    default_a = params.get("player_a", [players[0]] if players else [None])[0]
    default_b = params.get("player_b", [players[1]] if len(players) > 1 else [players[0]])[0]

    col_a, col_b = st.columns(2)
    with col_a:
        player_a = st.selectbox("Player A", players, index=get_default_index(players, default_a), key="player_a")
    with col_b:
        player_b = st.selectbox("Player B", players, index=get_default_index(players, default_b), key="player_b")

    update_query_params(page="Player Comparison", player_a=player_a, player_b=player_b)

    data_a = df[df["player_name"] == player_a]
    data_b = df[df["player_name"] == player_b]
    compare_df = pd.concat([data_a, data_b])

    if filters["exclude_pk"] and "np_goals" in compare_df.columns:
        compare_df = compare_df.assign(goals=compare_df["np_goals"])

    metrics = [
        "goals_per90",
        "xg_per90",
        "assists_per90",
        "xa_per90",
        "shots_per90",
        "key_passes_per90",
        "dribbles_per90",
        "def_actions_per90",
        "pass_pct",
    ]
    radar_df = compare_df[["player_name"] + metrics].groupby("player_name").mean().reset_index()
    st.plotly_chart(charts.player_radar(radar_df, metrics), use_container_width=True)

    st.altair_chart(charts.player_scatter(df, [player_a, player_b]), use_container_width=True)

    table_cols = [
        "player_name",
        "team_name",
        "minutes",
        "goals",
        "assists",
        "xg",
        "xa",
        "shots",
        "key_passes",
        "dribbles",
        "def_actions",
        "goals_per90",
        "xg_per90",
        "assists_per90",
        "xa_per90",
        "shots_per90",
        "key_passes_per90",
        "dribbles_per90",
        "def_actions_per90",
        "pass_pct",
    ]
    st.dataframe(compare_df[table_cols].round(2), hide_index=True, use_container_width=True)


def build_leaderboard(df: pd.DataFrame, column: str, per90: bool, top_n: int = 10, allow_per90: bool = True) -> pd.DataFrame:
    col = f"{column}_per90" if per90 and allow_per90 and f"{column}_per90" in df.columns else column
    leader = (
        df[["player_name", "team_name", "league_name", "minutes", col]]
        .sort_values(col, ascending=False)
        .head(top_n)
        .rename(columns={col: column})
    )
    leader[column] = leader[column].round(2)
    leader["compare_link"] = leader.apply(
        lambda row: f"?page=Player%20Comparison&player_a={quote(row['player_name'])}&league={quote(row['league_name'])}",
        axis=1,
    )
    return leader


def render_leaderboards(filters: dict) -> None:
    st.header("Leaderboards")
    df = fetch_player_stats(
        filters["season"], filters["min_minutes"], filters["leagues"], positions=filters.get("positions")
    )
    if handle_empty(df):
        return
    df = tf.enrich_players(df)
    metric_groups = [
        ("Goals", "goals", True),
        ("xG", "xg", True),
        ("Assists", "assists", True),
        ("xA", "xa", True),
        ("Key Passes", "key_passes", True),
        ("Dribbles", "dribbles", True),
        ("Def Actions", "def_actions", True),
        ("Pass%", "pass_pct", False),
    ]
    cols = st.columns(2)
    for idx, (label, metric, allow_per90) in enumerate(metric_groups):
        leaderboard = build_leaderboard(df, metric, filters["per90"], top_n=10, allow_per90=allow_per90)
        with cols[idx % 2]:
            st.subheader(label)
            st.dataframe(
                leaderboard[["player_name", "team_name", "league_name", metric, "compare_link"]],
                column_config={
                    "compare_link": st.column_config.LinkColumn("Compare", display_text="Player Comparison"),
                },
                hide_index=True,
                use_container_width=True,
            )


def render_data_browser(filters: dict) -> None:
    st.header("Data Browser")
    df = fetch_player_stats(
        filters["season"], filters["min_minutes"], filters["leagues"], filters.get("teams"), filters.get("positions")
    )
    if handle_empty(df):
        return
    df = tf.enrich_players(df)
    base_cols = [
        "player_name",
        "team_name",
        "league_name",
        "position",
        "minutes",
        "goals",
        "assists",
        "np_goals",
        "xg",
        "xa",
        "shots",
        "key_passes",
        "dribbles",
        "tackles",
        "interceptions",
        "passes_completed",
        "passes_attempted",
        "pass_pct",
    ]
    per90_cols = [col for col in df.columns if col.endswith("_per90")]
    available_cols = base_cols + (per90_cols if filters["per90"] else [])
    selected_cols = st.multiselect("Columns", available_cols, default=available_cols, key="browser_cols")
    if not selected_cols:
        selected_cols = available_cols
    page_size = st.selectbox("Rows per page", options=[25, 50, 100, 200], index=1)
    total_pages = math.ceil(len(df) / page_size)
    page = int(st.number_input("Page", min_value=1, max_value=max(total_pages, 1), value=1, step=1))
    start = (page - 1) * page_size
    end = start + page_size
    browser_df = df[selected_cols].round(2).iloc[start:end]
    st.dataframe(browser_df, hide_index=True, use_container_width=True)
    st.caption(f"Showing rows {start+1}–{min(end, len(df))} of {len(df)}")
    st.download_button("Download CSV slice", browser_df.to_csv(index=False).encode("utf-8"), file_name="data_browser_slice.csv")


def main():
    init_state()
    ref = load_reference_data()
    current_page = st.sidebar.radio("Pages", PAGE_OPTIONS, index=get_default_index(PAGE_OPTIONS, st.session_state["current_page"]))
    st.session_state["current_page"] = current_page
    update_query_params(page=current_page)
    filters = sidebar_filters(current_page, ref)

    if current_page == "League Overview":
        render_league_overview(filters)
    elif current_page == "Team Stats":
        render_team_stats(filters)
    elif current_page == "Player Comparison":
        render_player_comparison(filters)
    elif current_page == "Leaderboards":
        render_leaderboards(filters)
    elif current_page == "Data Browser":
        render_data_browser(filters)


if __name__ == "__main__":
    main()
