from __future__ import annotations

import math
from typing import Dict, List, Optional, Sequence
from urllib.parse import quote

import pandas as pd
import streamlit as st

import altair as alt

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
    "Player Scatter Lab",
]

STAT_CATEGORIES: Dict[str, List[tuple[str, str]]] = {
    "Basic": [
        ("apps", "Apps"),
        ("starts", "Starts"),
        ("minutes", "Minutes"),
        ("goal_contributions", "G+A"),
        ("goal_contributions_per90", "G+A/90"),
        ("pass_pct", "Pass%"),
    ],
    "Attacking": [
        ("goals", "Goals"),
        ("goals_per90", "Goals/90"),
        ("assists", "Assists"),
        ("assists_per90", "Assists/90"),
        ("np_goals", "NP Goals"),
        ("np_goals_per90", "NP Goals/90"),
        ("xg", "xG"),
        ("xg_per90", "xG/90"),
        ("xa", "xA"),
        ("xa_per90", "xA/90"),
        ("shots", "Shots"),
        ("shots_per90", "Shots/90"),
        ("shots_on_target", "SoT"),
        ("shots_on_target_per90", "SoT/90"),
        ("key_passes", "Key Passes"),
        ("key_passes_per90", "Key Passes/90"),
        ("passes_into_pen_area", "PPA"),
        ("passes_into_pen_area_per90", "PPA/90"),
        ("penalties", "PK goals"),
        ("penalty_att", "PK Att"),
    ],
    "Passing & Creativity": [
        ("progressive_passes", "PrgP"),
        ("progressive_passes_per90", "PrgP/90"),
        ("progressive_carries", "PrgC"),
        ("progressive_carries_per90", "PrgC/90"),
        ("progressive_receptions", "PrgR"),
        ("progressive_receptions_per90", "PrgR/90"),
        ("shot_creating_actions", "SCA"),
        ("shot_creating_actions_per90", "SCA/90"),
        ("goal_creating_actions", "GCA"),
        ("goal_creating_actions_per90", "GCA/90"),
        ("passes_completed", "Cmp"),
        ("passes_attempted", "Att"),
    ],
    "Defensive": [
        ("tackles", "Tackles"),
        ("tackles_per90", "Tackles/90"),
        ("tackles_won", "Tackles Won"),
        ("tackles_won_per90", "TklW/90"),
        ("interceptions", "Int"),
        ("interceptions_per90", "Int/90"),
        ("def_actions", "Tkl+Int"),
        ("def_actions_per90", "Tkl+Int/90"),
        ("blocks", "Blocks"),
        ("blocks_per90", "Blocks/90"),
        ("clearances", "Clr"),
        ("clearances_per90", "Clr/90"),
        ("recoveries", "Recov"),
        ("recoveries_per90", "Recov/90"),
        ("errors", "Errors"),
    ],
    "Possession": [
        ("touches", "Touches"),
        ("touches_per90", "Touches/90"),
        ("carries", "Carries"),
        ("carries_per90", "Carries/90"),
        ("dribbles", "Take-ons"),
        ("dribbles_per90", "Take-ons/90"),
        ("possession_losses", "Mis+Dis"),
        ("possession_losses_per90", "Losses/90"),
        ("miscontrols", "Mis"),
        ("dispossessed", "Dis"),
        ("offsides", "Off"),
    ],
    "Goalkeeping": [
        ("goals_against", "GA"),
        ("ga_per90", "GA/90"),
        ("saves", "Saves"),
        ("save_pct_calc", "Save%"),
        ("shots_on_target_against", "SoTA"),
        ("clean_sheets", "CS"),
        ("clean_sheet_pct_calc", "CS%"),
        ("penalty_kicks_faced", "PK Faced"),
        ("penalty_kicks_saved", "PK Saved"),
    ],
    "Misc": [
        ("yellow_cards", "Yellow"),
        ("red_cards", "Red"),
        ("fouls_committed", "Fouls"),
        ("fouls_drawn", "Fouled"),
        ("penalties_won", "PK Won"),
        ("penalties_conceded", "PK Conceded"),
        ("own_goals", "Own Goals"),
    ],
}

DEFAULT_CATEGORY_SELECTION = list(STAT_CATEGORIES.keys())

LEADERBOARD_METRICS: Dict[str, Dict[str, object]] = {
    "goals": {"label": "Goals", "column": "goals", "allow_per90": True},
    "xg": {"label": "xG", "column": "xg", "allow_per90": True},
    "assists": {"label": "Assists", "column": "assists", "allow_per90": True},
    "xa": {"label": "xA", "column": "xa", "allow_per90": True},
    "shots_on_target": {"label": "Shots on Target", "column": "shots_on_target", "allow_per90": True},
    "key_passes": {"label": "Key Passes", "column": "key_passes", "allow_per90": True},
    "passes_into_pen_area": {"label": "Passes into Pen Area", "column": "passes_into_pen_area", "allow_per90": True},
    "shot_creating_actions": {"label": "Shot Creating Actions", "column": "shot_creating_actions", "allow_per90": True},
    "goal_creating_actions": {"label": "Goal Creating Actions", "column": "goal_creating_actions", "allow_per90": True},
    "progressive_passes": {"label": "Progressive Passes", "column": "progressive_passes", "allow_per90": True},
    "progressive_carries": {"label": "Progressive Carries", "column": "progressive_carries", "allow_per90": True},
    "tackles": {"label": "Tackles", "column": "tackles", "allow_per90": True},
    "tackles_won": {"label": "Tackles Won", "column": "tackles_won", "allow_per90": True},
    "interceptions": {"label": "Interceptions", "column": "interceptions", "allow_per90": True},
    "blocks": {"label": "Blocks", "column": "blocks", "allow_per90": True},
    "clearances": {"label": "Clearances", "column": "clearances", "allow_per90": True},
    "recoveries": {"label": "Recoveries", "column": "recoveries", "allow_per90": True},
    "touches": {"label": "Touches", "column": "touches", "allow_per90": True},
    "carries": {"label": "Carries", "column": "carries", "allow_per90": True},
    "save_pct_calc": {"label": "Save %", "column": "save_pct_calc", "allow_per90": False},
    "clean_sheet_pct_calc": {"label": "Clean Sheet %", "column": "clean_sheet_pct_calc", "allow_per90": False},
}

DEFAULT_LEADERBOARD_SELECTION = [
    "goals",
    "xg",
    "assists",
    "key_passes",
    "shot_creating_actions",
    "progressive_passes",
    "tackles",
    "blocks",
    "recoveries",
    "save_pct_calc",
]

SCATTER_GRID_PAIRS = [
    ("goals_per90", "assists_per90"),
    ("xg_per90", "xa_per90"),
    ("shots_per90", "shots_on_target_per90"),
    ("key_passes_per90", "dribbles_per90"),
    ("def_actions_per90", "pass_pct"),
    ("progressive_passes_per90", "progressive_carries_per90"),
    ("recoveries_per90", "possession_losses_per90"),
    ("tackles_per90", "interceptions_per90"),
    ("shots_per90", "pass_pct"),
    ("xg_per90", "shots_per90"),
]

DEFAULT_SEASON = "2024-2025"
DEFAULT_MIN_MINUTES = 450

st.set_page_config(page_title="Top-5 Dashboard", layout="wide", page_icon="⚽")


def pass_pct_from_df(df: pd.DataFrame) -> float:
    attempted = df["passes_attempted"].sum()
    if attempted == 0:
        return 0.0
    return (df["passes_completed"].sum() / attempted) * 100


def flatten_category_columns(selected_categories: Sequence[str]) -> List[str]:
    columns: List[str] = []
    seen: set[str] = set()
    for cat in selected_categories:
        for column, _label in STAT_CATEGORIES.get(cat, []):
            if column not in seen:
                columns.append(column)
                seen.add(column)
    return columns


def category_label_map(selected_categories: Sequence[str]) -> Dict[str, str]:
    lookup: Dict[str, str] = {}
    for cat in selected_categories:
        for column, label in STAT_CATEGORIES.get(cat, []):
            lookup[column] = label
    return lookup


def build_table_from_categories(
    df: pd.DataFrame,
    selected_categories: Sequence[str],
    base_columns: Sequence[str],
) -> pd.DataFrame:
    df_cols = df.columns
    seen: set[str] = set()
    display_cols: List[str] = []
    for col in base_columns:
        if col in df_cols and col not in seen:
            display_cols.append(col)
            seen.add(col)
    rename_map = category_label_map(selected_categories)
    rename_dict: Dict[str, str] = {}
    for col in flatten_category_columns(selected_categories):
        if col in df_cols and col not in seen:
            display_cols.append(col)
            seen.add(col)
            label = rename_map.get(col, col)
            safe_label = label
            counter = 2
            while safe_label in rename_dict.values():
                safe_label = f"{label} ({counter})"
                counter += 1
            rename_dict[col] = safe_label
    if not display_cols:
        return pd.DataFrame()
    table = df[display_cols].copy()
    if rename_dict:
        table = table.rename(columns=rename_dict)
    return table


def section_selected(filters: dict, section: str) -> bool:
    sections = filters.get("sections")
    if not sections:
        return False
    return section in sections


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
        categories = st.sidebar.multiselect(
            "Stat categories",
            DEFAULT_CATEGORY_SELECTION,
            default=DEFAULT_CATEGORY_SELECTION,
            key="categories_league",
        )
        section_options = ["KPI Tiles", "Charts", "Summary Table", "Possession Table", "Custom Chart"]
        sections = st.sidebar.multiselect(
            "Sections to display",
            section_options,
            default=section_options,
            key="sections_league",
        )
        metric_options = flatten_category_columns(categories or DEFAULT_CATEGORY_SELECTION)
        custom_chart = None
        if "Custom Chart" in sections and metric_options:
            default_x = metric_options[0]
            default_y = metric_options[1] if len(metric_options) > 1 else metric_options[0]
            custom_chart = {
                "x": st.sidebar.selectbox("League chart X-axis", metric_options, index=metric_options.index(default_x), key="league_chart_x"),
                "y": st.sidebar.selectbox("League chart Y-axis", metric_options, index=metric_options.index(default_y), key="league_chart_y"),
                "color": st.sidebar.selectbox("League chart color metric (optional)", ["(none)"] + metric_options, index=0, key="league_chart_color"),
                "type": st.sidebar.selectbox("League chart type", ["Scatter", "Bar", "Line"], index=0, key="league_chart_type"),
            }
        return {
            "season": season,
            "leagues": selected_leagues or leagues,
            "min_minutes": min_minutes,
            "per90": per90,
            "categories": categories or DEFAULT_CATEGORY_SELECTION,
            "sections": sections,
            "custom_chart": custom_chart,
        }

    if page == "Team Stats":
        league = st.sidebar.selectbox("League", leagues, index=0)
        teams = get_teams(season, [league])
        team = st.sidebar.selectbox("Team", teams, index=0)
        min_minutes = st.sidebar.number_input("Min minutes", min_value=0, value=DEFAULT_MIN_MINUTES, step=90)
        categories = st.sidebar.multiselect(
            "Stat categories",
            DEFAULT_CATEGORY_SELECTION,
            default=DEFAULT_CATEGORY_SELECTION,
            key="categories_team",
        )
        section_options = ["KPI Tiles", "Charts", "Custom Chart", "Squad Table"]
        sections = st.sidebar.multiselect(
            "Sections to display",
            section_options,
            default=section_options,
            key="sections_team",
        )
        metric_options = flatten_category_columns(categories or DEFAULT_CATEGORY_SELECTION)
        custom_chart = None
        if "Custom Chart" in sections and metric_options:
            default_x = metric_options[0]
            default_y = metric_options[1] if len(metric_options) > 1 else metric_options[0]
            custom_chart = {
                "x": st.sidebar.selectbox("Custom chart X-axis", metric_options, index=metric_options.index(default_x), key="team_chart_x"),
                "y": st.sidebar.selectbox("Custom chart Y-axis", metric_options, index=metric_options.index(default_y), key="team_chart_y"),
                "color": st.sidebar.selectbox("Color metric (optional)", ["(none)"] + metric_options, index=0, key="team_chart_color"),
                "type": st.sidebar.selectbox("Chart type", ["Scatter", "Bar", "Line"], index=0, key="team_chart_type"),
            }
        return {
            "season": season,
            "league": league,
            "team": team,
            "min_minutes": min_minutes,
            "categories": categories or DEFAULT_CATEGORY_SELECTION,
            "sections": sections,
            "custom_chart": custom_chart,
        }

    if page == "Player Comparison":
        selected_leagues = st.sidebar.multiselect("League(s)", leagues, default=leagues)
        teams = ["All teams"] + get_teams(season, selected_leagues)
        team = st.sidebar.selectbox("Team (optional)", teams, index=0)
        min_minutes = st.sidebar.number_input("Min minutes", min_value=0, value=DEFAULT_MIN_MINUTES, step=90)
        per90 = st.sidebar.toggle("Per-90 view", value=True, key="per90_pc")
        exclude_pk = st.sidebar.toggle("Exclude penalties (use NP Goals)", value=False, key="exclude_pk")
        categories = st.sidebar.multiselect(
            "Stat categories",
            DEFAULT_CATEGORY_SELECTION,
            default=DEFAULT_CATEGORY_SELECTION,
            key="categories_compare",
        )
        available_metrics = [
            col
            for col in flatten_category_columns(categories or DEFAULT_CATEGORY_SELECTION)
            if col.endswith("_per90") or col in {"pass_pct", "save_pct_calc", "clean_sheet_pct_calc"}
        ]
        default_metrics = [
            m
            for m in [
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
            if m in available_metrics
        ]
        selected_metrics = st.sidebar.multiselect(
            "Radar / comparison metrics",
            available_metrics or default_metrics,
            default=default_metrics or available_metrics[:6],
            key="compare_metrics",
        )
        section_options = ["Radar", "Scatter + Bars", "Scatter Grid", "Comparison Table"]
        sections = st.sidebar.multiselect(
            "Sections to display",
            section_options,
            default=section_options,
            key="sections_compare",
        )
        return {
            "season": season,
            "leagues": selected_leagues or leagues,
            "team": None if team == "All teams" else team,
            "min_minutes": min_minutes,
            "per90": per90,
            "exclude_pk": exclude_pk,
            "categories": categories or DEFAULT_CATEGORY_SELECTION,
            "selected_metrics": selected_metrics or default_metrics,
            "sections": sections,
        }

    if page == "Leaderboards":
        selected_leagues = st.sidebar.multiselect("League(s)", leagues, default=leagues)
        positions = get_positions(season)
        selected_positions = st.sidebar.multiselect("Position", positions)
        min_minutes = st.sidebar.number_input("Min minutes", min_value=0, value=DEFAULT_MIN_MINUTES, step=90)
        per90 = st.sidebar.toggle("Per-90 view", value=True, key="per90_lb")
        metric_keys = list(LEADERBOARD_METRICS.keys())
        selected_metrics = st.sidebar.multiselect(
            "Leaderboard metrics",
            metric_keys,
            default=[m for m in DEFAULT_LEADERBOARD_SELECTION if m in metric_keys],
            format_func=lambda key: LEADERBOARD_METRICS[key]["label"],
        )
        chart_metric_choices = selected_metrics or metric_keys
        chart_metric = st.sidebar.selectbox(
            "Chart metric",
            chart_metric_choices,
            format_func=lambda key: LEADERBOARD_METRICS[key]["label"],
            key="leaderboard_chart_metric",
        )
        section_options = ["Tables", "Chart"]
        sections = st.sidebar.multiselect(
            "Sections to display",
            section_options,
            default=section_options,
            key="sections_leaderboard",
        )
        return {
            "season": season,
            "leagues": selected_leagues or leagues,
            "positions": selected_positions,
            "min_minutes": min_minutes,
            "per90": per90,
            "leaderboard_metrics": selected_metrics or metric_keys[:5],
            "chart_metric": chart_metric,
            "sections": sections,
        }

    if page == "Data Browser":
        selected_leagues = st.sidebar.multiselect("League(s)", leagues, default=leagues)
        teams = get_teams(season, selected_leagues)
        selected_teams = st.sidebar.multiselect("Team", teams)
        positions = get_positions(season)
        selected_positions = st.sidebar.multiselect("Position", positions)
        min_minutes = st.sidebar.number_input("Min minutes", min_value=0, value=DEFAULT_MIN_MINUTES, step=90)
        per90 = st.sidebar.toggle("Include per-90 columns", value=True, key="per90_browser")
        categories = st.sidebar.multiselect(
            "Stat categories",
            DEFAULT_CATEGORY_SELECTION,
            default=DEFAULT_CATEGORY_SELECTION,
            key="categories_browser",
        )
        section_options = ["Quick Chart", "Table"]
        sections = st.sidebar.multiselect(
            "Sections to display",
            section_options,
            default=section_options,
            key="sections_browser",
        )
        return {
            "season": season,
            "leagues": selected_leagues or leagues,
            "teams": selected_teams,
            "positions": selected_positions,
            "min_minutes": min_minutes,
            "per90": per90,
            "categories": categories or DEFAULT_CATEGORY_SELECTION,
            "sections": sections,
        }

    if page == "Player Scatter Lab":
        selected_leagues = st.sidebar.multiselect("League(s)", leagues, default=leagues)
        teams = get_teams(season, selected_leagues)
        selected_teams = st.sidebar.multiselect("Team(s)", teams)
        positions = get_positions(season)
        selected_positions = st.sidebar.multiselect("Position(s)", positions)
        min_minutes = st.sidebar.number_input("Min minutes", min_value=0, value=DEFAULT_MIN_MINUTES, step=90)
        categories = st.sidebar.multiselect(
            "Stat categories",
            DEFAULT_CATEGORY_SELECTION,
            default=DEFAULT_CATEGORY_SELECTION,
            key="categories_scatter_lab",
        )
        label_map = category_label_map(categories or DEFAULT_CATEGORY_SELECTION)
        pair_options = []
        for x_metric, y_metric in SCATTER_GRID_PAIRS:
            key = f"{x_metric}|{y_metric}"
            label = f"{label_map.get(y_metric, y_metric)} vs {label_map.get(x_metric, x_metric)}"
            pair_options.append((key, (x_metric, y_metric), label))
        default_keys = [pair_options[i][0] for i in range(min(6, len(pair_options)))]
        selection_keys = st.sidebar.multiselect(
            "Scatter pairs",
            [key for key, _pair, _label in pair_options],
            default=default_keys,
            format_func=lambda key: next(label for key_, _pair, label in pair_options if key_ == key),
        )
        selected_pairs = [pair for key, pair, _label in pair_options if key in selection_keys] or [pair_options[0][1]]
        color_field = st.sidebar.selectbox("Color points by", ["league_name", "team_name", "position"], index=0)
        section_options = ["Scatter Grid", "Data Table"]
        sections = st.sidebar.multiselect(
            "Sections to display",
            section_options,
            default=section_options,
            key="sections_scatter_lab",
        )
        return {
            "season": season,
            "leagues": selected_leagues or leagues,
            "teams": selected_teams,
            "positions": selected_positions,
            "min_minutes": min_minutes,
            "categories": categories or DEFAULT_CATEGORY_SELECTION,
            "scatter_pairs": selected_pairs,
            "color_field": color_field,
            "sections": sections,
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
    if not filters.get("sections"):
        st.info("Enable at least one section in the sidebar to see league content.")
        return

    if section_selected(filters, "KPI Tiles"):
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

    if section_selected(filters, "Charts"):
        charts_cols = st.columns(3)
        with charts_cols[0]:
            st.altair_chart(charts.league_xg_bar(league_df, filters["per90"]), width="stretch")
        with charts_cols[1]:
            st.altair_chart(charts.league_goals_box(df), width="stretch")
        with charts_cols[2]:
            st.altair_chart(charts.league_scatter(league_df, filters["per90"]), width="stretch")
        extra_cols = st.columns(2)
        with extra_cols[0]:
            st.altair_chart(
                charts.possession_vs_pass(league_df, color_field="league_name"),
                width="stretch",
            )
        with extra_cols[1]:
            st.altair_chart(charts.goalkeeper_save_bar(league_df), width="stretch")

    if section_selected(filters, "Summary Table"):
        st.subheader("League summary table")
        table = build_table_from_categories(
            league_df.round(2),
            filters.get("categories", DEFAULT_CATEGORY_SELECTION),
            base_columns=["league_name", "players", "minutes"],
        )
        if table.empty:
            st.info("Select at least one category to show summary columns.")
        else:
            st.dataframe(table, hide_index=True, width="stretch")
    if section_selected(filters, "Possession Table"):
        st.subheader("Possession & Passing table")
        poss_cols = [
            "league_name",
            "touches_per90",
            "pass_pct",
            "progressive_passes_per90",
            "progressive_carries_per90",
        ]
        poss_table = league_df[[col for col in poss_cols if col in league_df.columns]].round(2)
        st.dataframe(poss_table.rename(columns={
            "touches_per90": "Touches/90",
            "pass_pct": "Pass%",
            "progressive_passes_per90": "PrgP/90",
            "progressive_carries_per90": "PrgC/90",
        }), hide_index=True, width="stretch")
    if section_selected(filters, "Custom Chart") and filters.get("custom_chart"):
        settings = filters["custom_chart"]
        color_metric = settings["color"] if settings["color"] != "(none)" else None
        st.subheader("Custom league chart")
        st.caption("Choose any two metrics in the sidebar to compare leagues (e.g., xG vs Pass%).")
        st.altair_chart(
            charts.custom_metric_chart(
                league_df,
                settings["x"],
                settings["y"],
                color_metric,
                settings["type"],
                f"{settings['y']} vs {settings['x']} by league",
            ),
            width="stretch",
        )


def render_team_stats(filters: dict) -> None:
    st.header("Team Stats")
    df = fetch_team_summary(filters["season"], filters["league"], filters["team"], filters["min_minutes"])
    if handle_empty(df, "Select another team or relax the minute filter."):
        return
    df = tf.enrich_players(df)
    total_minutes = max(df["minutes"].sum(), 1)
    if not filters.get("sections"):
        st.info("Enable at least one section in the sidebar to see team content.")
        return
    if section_selected(filters, "KPI Tiles"):
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

    if section_selected(filters, "Charts"):
        st.markdown("### Top contributors (Goals/xG/xA)")
        st.caption("Stacked bars highlight the top five players driving goals, expected goals, and assists for the selected team.")
        top_players = df.sort_values("goals", ascending=False).head(5)[
            ["player_name", "goals", "xg", "assists", "xa"]
        ]
        st.altair_chart(charts.stacked_player_contributions(top_players), width="stretch")

        st.markdown("### Team vs league (per-90 deltas)")
        st.caption("Heatmap compares the team's per-90 production to the league average across attacking, creative, and defensive metrics.")
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
        st.altair_chart(charts.team_heatmap(team_metric_df, league_metric_df), width="stretch")

        extra_row = st.columns(2)
        with extra_row[0]:
            st.caption("Scatter shows which squad members drive progression via passes vs carries.")
            st.altair_chart(charts.player_progression_scatter(df), width="stretch")
        with extra_row[1]:
            st.caption("Bar chart surfaces the players losing possession most often.")
            st.altair_chart(charts.player_possession_loss_chart(df), width="stretch")

    if section_selected(filters, "Custom Chart") and filters.get("custom_chart"):
        settings = filters["custom_chart"]
        color_metric = settings["color"] if settings["color"] != "(none)" else None
        st.markdown("### Custom metric chart")
        st.caption("Select metrics in the sidebar to plot any combination (e.g., xG vs xA).")
        st.altair_chart(
            charts.custom_metric_chart(
                df,
                settings["x"],
                settings["y"],
                color_metric,
                settings["type"],
                f"{settings['y']} vs {settings['x']}",
            ),
            width="stretch",
        )

    if section_selected(filters, "Squad Table"):
        st.markdown("### Squad detail")
        squad_table = build_table_from_categories(
            df.round(2),
            filters.get("categories", DEFAULT_CATEGORY_SELECTION),
            base_columns=["player_name", "position", "minutes"],
        )
        if squad_table.empty:
            st.info("Select at least one category to show squad columns.")
        else:
            st.dataframe(squad_table, hide_index=True, width="stretch")
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

    st.info("Use the sidebar to select which sections and metrics to render. Radar values overlap for quick pattern comparison; the scatter + bars view highlights differences in a few key stats.")

    selected_categories = filters.get("categories", DEFAULT_CATEGORY_SELECTION)
    label_map = category_label_map(selected_categories)
    radar_candidates = [
        col
        for col in flatten_category_columns(selected_categories)
        if col.endswith("_per90") or col in {"pass_pct", "save_pct_calc", "clean_sheet_pct_calc"}
    ]
    fallback_metrics = [
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
    user_metrics = filters.get("selected_metrics") or fallback_metrics
    metrics = [col for col in user_metrics if col in compare_df.columns] or [col for col in fallback_metrics if col in compare_df.columns]

    if section_selected(filters, "Radar") and metrics:
        radar_df = compare_df[["player_name"] + metrics].groupby("player_name").mean().reset_index()
        st.plotly_chart(charts.player_radar(radar_df, metrics, colors=["#2b8cbe", "#d95f0e", "#6baed6", "#fec44f"]), width="stretch")

    if section_selected(filters, "Scatter + Bars"):
        st.altair_chart(charts.player_scatter(df, [player_a, player_b]), width="stretch")
        if metrics:
            st.altair_chart(
                charts.player_metric_bar(compare_df, metrics[:5]),
                width="stretch",
            )

    if section_selected(filters, "Scatter Grid"):
        st.markdown("### Scatter grid")
        st.caption("Explore quick metric pairs – adjust the stat categories to influence which per-90 metrics are available.")
        cols = st.columns(2)
        chart_idx = 0
        for x_metric, y_metric in SCATTER_GRID_PAIRS:
            if x_metric not in compare_df.columns or y_metric not in compare_df.columns:
                continue
            col = cols[chart_idx % 2]
            with col:
                chart_idx += 1
                st.altair_chart(
                    alt.Chart(compare_df)
                    .mark_circle(size=140, opacity=0.85)
                    .encode(
                        x=alt.X(f"{x_metric}:Q", title=label_map.get(x_metric, x_metric)),
                        y=alt.Y(f"{y_metric}:Q", title=label_map.get(y_metric, y_metric)),
                        color=alt.Color("player_name:N", title="Player"),
                        tooltip=[
                            "player_name",
                            alt.Tooltip(f"{x_metric}:Q", format=".2f"),
                            alt.Tooltip(f"{y_metric}:Q", format=".2f"),
                        ],
                    )
                    .properties(height=220, title=f"{label_map.get(y_metric, y_metric)} vs {label_map.get(x_metric, x_metric)}"),
                    width="stretch",
                )
        if chart_idx == 0:
            st.info("No scatter pairs available for the current metric selection.")

    if section_selected(filters, "Comparison Table"):
        table = build_table_from_categories(
            compare_df.round(2),
            selected_categories,
            base_columns=["player_name", "team_name", "minutes"],
        )
        if table.empty:
            st.info("Select at least one category to show comparison statistics.")
        else:
            st.dataframe(table, hide_index=True, width="stretch")


def build_leaderboard(df: pd.DataFrame, metric_key: str, per90: bool, top_n: int = 10) -> tuple[pd.DataFrame, str]:
    meta = LEADERBOARD_METRICS.get(metric_key, {"label": metric_key.title(), "column": metric_key, "allow_per90": True})
    column = meta["column"]
    source_col = f"{column}_per90" if per90 and meta.get("allow_per90", True) and f"{column}_per90" in df.columns else column
    display_label = meta["label"] + ("/90" if source_col.endswith("_per90") and meta.get("allow_per90", True) else "")
    leader = (
        df[["player_name", "team_name", "league_name", "minutes", source_col]]
        .sort_values(source_col, ascending=False)
        .head(top_n)
        .rename(columns={source_col: display_label})
    )
    leader[display_label] = leader[display_label].round(2)
    leader["compare_link"] = leader.apply(
        lambda row: f"?page=Player%20Comparison&player_a={quote(row['player_name'])}&league={quote(row['league_name'])}",
        axis=1,
    )
    return leader, display_label


def render_leaderboards(filters: dict) -> None:
    st.header("Leaderboards")
    df = fetch_player_stats(
        filters["season"], filters["min_minutes"], filters["leagues"], positions=filters.get("positions")
    )
    if handle_empty(df):
        return
    df = tf.enrich_players(df)
    metric_keys = filters.get("leaderboard_metrics", DEFAULT_LEADERBOARD_SELECTION)
    if not metric_keys:
        st.info("Select at least one metric to populate the leaderboards.")
        return
    if not filters.get("sections"):
        st.info("Enable at least one section in the sidebar to see leaderboard content.")
        return
    if section_selected(filters, "Tables"):
        cols = st.columns(2)
        for idx, metric_key in enumerate(metric_keys):
            leaderboard, label = build_leaderboard(df, metric_key, filters["per90"], top_n=10)
            with cols[idx % 2]:
                st.subheader(label)
                st.dataframe(
                    leaderboard[["player_name", "team_name", "league_name", label, "compare_link"]],
                    column_config={
                        "compare_link": st.column_config.LinkColumn("Compare", display_text="Player Comparison"),
                    },
                    hide_index=True,
                    width="stretch",
                )
    if section_selected(filters, "Chart") and filters.get("chart_metric"):
        chart_df, chart_label = build_leaderboard(df, filters["chart_metric"], filters["per90"], top_n=15)
        st.altair_chart(
            charts.leaderboard_metric_chart(chart_df, chart_label),
            width="stretch",
        )


def render_data_browser(filters: dict) -> None:
    st.header("Data Browser")
    df = fetch_player_stats(
        filters["season"], filters["min_minutes"], filters["leagues"], filters.get("teams"), filters.get("positions")
    )
    if handle_empty(df):
        return
    df = tf.enrich_players(df)
    if not filters.get("sections"):
        st.info("Enable at least one section in the sidebar to explore the data.")
        return
    base_cols = ["player_name", "team_name", "league_name", "position", "minutes"]
    selected_categories = filters.get("categories", DEFAULT_CATEGORY_SELECTION)
    category_cols = flatten_category_columns(selected_categories)
    if not filters.get("per90", True):
        category_cols = [col for col in category_cols if not col.endswith("_per90")]
    data_cols = [col for col in category_cols if col in df.columns]
    display_cols = base_cols + data_cols
    if not display_cols:
        st.info("No columns available for the current selection.")
        return
    if section_selected(filters, "Quick Chart") and data_cols:
        label_map = category_label_map(selected_categories)
        chart_col = st.selectbox(
            "Chart metric",
            data_cols,
            format_func=lambda col: label_map.get(col, col),
            key="browser_chart_metric",
        )
        st.altair_chart(
            charts.metric_distribution(df, chart_col, label_map.get(chart_col, chart_col)),
            width="stretch",
        )
    if section_selected(filters, "Table"):
        page_size = st.selectbox("Rows per page", options=[25, 50, 100, 200], index=1)
        total_pages = math.ceil(len(df) / page_size)
        page = int(st.number_input("Page", min_value=1, max_value=max(total_pages, 1), value=1, step=1))
        start = (page - 1) * page_size
        end = start + page_size
        browser_df = df[display_cols].round(2).iloc[start:end]
        st.dataframe(browser_df, hide_index=True, width="stretch")
        st.caption(f"Showing rows {start+1}–{min(end, len(df))} of {len(df)}")
        st.download_button("Download CSV slice", browser_df.to_csv(index=False).encode("utf-8"), file_name="data_browser_slice.csv")
    else:
        st.info("Enable the 'Table' section from the sidebar to view rows.")


def render_player_scatter_lab(filters: dict) -> None:
    st.header("Player Scatter Lab")
    df = fetch_player_stats(
        filters["season"],
        filters["min_minutes"],
        filters["leagues"],
        filters.get("teams"),
        filters.get("positions"),
    )
    if handle_empty(df):
        return
    df = tf.enrich_players(df)
    if not filters.get("sections"):
        st.info("Enable at least one section in the sidebar to see scatter visuals.")
        return
    label_map = category_label_map(filters.get("categories", DEFAULT_CATEGORY_SELECTION))
    if section_selected(filters, "Scatter Grid"):
        st.markdown("### Scatter grid")
        st.caption("Each panel plots a different metric pair for the filtered cohort. Adjust the sidebar to change metrics or color encoding.")
        color_field = filters.get("color_field", "league_name")
        color_encoding = (
            alt.Color(f"{color_field}:N", title=color_field.replace("_", " ").title()) if color_field in df.columns else alt.Color("league_name:N", title="League")
        )
        cols = st.columns(2)
        chart_idx = 0
        for x_metric, y_metric in filters.get("scatter_pairs", []):
            if x_metric not in df.columns or y_metric not in df.columns:
                continue
            column = cols[chart_idx % 2]
            chart_idx += 1
            with column:
                st.altair_chart(
                    alt.Chart(df)
                    .mark_circle(size=60, opacity=0.8)
                    .encode(
                        x=alt.X(f"{x_metric}:Q", title=label_map.get(x_metric, x_metric)),
                        y=alt.Y(f"{y_metric}:Q", title=label_map.get(y_metric, y_metric)),
                        color=color_encoding,
                        tooltip=[
                            "player_name",
                            "team_name",
                            alt.Tooltip(f"{x_metric}:Q", format=".2f"),
                            alt.Tooltip(f"{y_metric}:Q", format=".2f"),
                        ],
                    )
                    .properties(height=260, title=f"{label_map.get(y_metric, y_metric)} vs {label_map.get(x_metric, x_metric)}"),
                    width="stretch",
                )
        if chart_idx == 0:
            st.info("No scatter pairs available for the current filters. Try enabling additional stat categories.")
    if section_selected(filters, "Data Table"):
        st.markdown("### Underlying data")
        table = build_table_from_categories(
            df.round(2),
            filters.get("categories", DEFAULT_CATEGORY_SELECTION),
            base_columns=["player_name", "team_name", "league_name", "position", "minutes"],
        )
        if table.empty:
            st.info("No columns available for the current selection.")
        else:
            st.dataframe(table, hide_index=True, width="stretch")


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
    elif current_page == "Player Scatter Lab":
        render_player_scatter_lab(filters)


if __name__ == "__main__":
    main()
