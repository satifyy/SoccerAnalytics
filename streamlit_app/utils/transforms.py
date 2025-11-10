from __future__ import annotations

import pandas as pd

PER90_BASE_COLS = [
    "goals",
    "assists",
    "np_goals",
    "xg",
    "xa",
    "shots",
    "shots_on_target",
    "key_passes",
    "dribbles",
    "touches",
    "tackles",
    "tackles_won",
    "interceptions",
    "blocks",
    "clearances",
    "passes_into_pen_area",
    "progressive_passes",
    "progressive_carries",
    "progressive_receptions",
    "shot_creating_actions",
    "goal_creating_actions",
    "recoveries",
    "carries",
]


def ensure_numeric(df: pd.DataFrame, columns: list[str]) -> pd.DataFrame:
    for col in columns:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)
    return df


def add_per90(df: pd.DataFrame, columns: list[str] | None = None) -> pd.DataFrame:
    columns = columns or PER90_BASE_COLS
    df = df.copy()
    minutes = df["minutes"].clip(lower=1)
    for col in columns:
        if col in df.columns:
            df[f"{col}_per90"] = (df[col] / minutes) * 90
    return df


def add_pass_pct(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    if {"passes_completed", "passes_attempted"}.issubset(df.columns):
        df["pass_pct"] = (df["passes_completed"] / df["passes_attempted"].replace(0, pd.NA)) * 100
        df["pass_pct"] = df["pass_pct"].fillna(0)
    return df


def add_defensive_actions(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    if {"tackles", "interceptions"}.issubset(df.columns):
        df["def_actions"] = df["tackles"] + df["interceptions"]
        df["def_actions_per90"] = (df["def_actions"] / df["minutes"].clip(lower=1)) * 90
    return df


def add_goal_contributions(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    if {"goals", "assists"}.issubset(df.columns):
        df["goal_contributions"] = df["goals"] + df["assists"]
        df["goal_contributions_per90"] = (df["goal_contributions"] / df["minutes"].clip(lower=1)) * 90
    return df


def add_goalkeeping_metrics(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    minutes = df["minutes"].clip(lower=1)
    if "goals_against" in df.columns:
        df["ga_per90"] = (df["goals_against"] / minutes) * 90
    if {"saves", "shots_on_target_against"}.issubset(df.columns):
        df["save_pct_calc"] = (df["saves"] / df["shots_on_target_against"].replace(0, pd.NA)) * 100
        df["save_pct_calc"] = df["save_pct_calc"].fillna(0).astype(float)
    if {"clean_sheets", "apps"}.issubset(df.columns):
        df["clean_sheet_pct_calc"] = (df["clean_sheets"] / df["apps"].replace(0, pd.NA)) * 100
        df["clean_sheet_pct_calc"] = df["clean_sheet_pct_calc"].fillna(0).astype(float)
    return df


def add_possession_losses(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    if {"miscontrols", "dispossessed"}.issubset(df.columns):
        df["possession_losses"] = df["miscontrols"] + df["dispossessed"]
        df["possession_losses_per90"] = (df["possession_losses"] / df["minutes"].clip(lower=1)) * 90
    return df


def enrich_players(df: pd.DataFrame) -> pd.DataFrame:
    df = ensure_numeric(
        df,
        [
            "apps",
            "starts",
            "minutes",
            "goals",
            "assists",
            "np_goals",
            "xg",
            "xa",
            "npxg",
            "shots",
            "shots_on_target",
            "key_passes",
            "dribbles",
            "tackles",
            "interceptions",
            "yellow_cards",
            "red_cards",
            "touches",
            "passes_completed",
            "passes_attempted",
            "progressive_passes",
            "progressive_carries",
            "progressive_receptions",
            "shot_creating_actions",
            "goal_creating_actions",
            "passes_into_pen_area",
            "tackles_won",
            "blocks",
            "clearances",
            "errors",
            "fouls_committed",
            "fouls_drawn",
            "offsides",
            "penalties_won",
            "penalties_conceded",
            "own_goals",
            "recoveries",
            "miscontrols",
            "dispossessed",
            "carries",
            "goals_against",
            "goals_against_per90",
            "shots_on_target_against",
            "saves",
            "save_pct",
            "wins",
            "draws",
            "losses",
            "clean_sheets",
            "clean_sheet_pct",
            "penalty_kicks_faced",
            "penalty_kicks_saved",
            "penalty_kicks_missed_against",
        ],
    )
    df = add_defensive_actions(df)
    df = add_per90(df)
    df = add_pass_pct(df)
    df = add_goal_contributions(df)
    df = add_goalkeeping_metrics(df)
    df = add_possession_losses(df)
    return df


def aggregate_by_league(df: pd.DataFrame) -> pd.DataFrame:
    group_cols = [
        "league_name",
    ]
    agg = (
        df.groupby(group_cols)
        .agg(
            minutes=("minutes", "sum"),
            goals=("goals", "sum"),
            assists=("assists", "sum"),
            np_goals=("np_goals", "sum"),
            xg=("xg", "sum"),
            xa=("xa", "sum"),
            shots=("shots", "sum"),
            shots_on_target=("shots_on_target", "sum"),
            key_passes=("key_passes", "sum"),
            dribbles=("dribbles", "sum"),
            tackles=("tackles", "sum"),
            tackles_won=("tackles_won", "sum"),
            interceptions=("interceptions", "sum"),
            blocks=("blocks", "sum"),
            clearances=("clearances", "sum"),
            passes_into_pen_area=("passes_into_pen_area", "sum"),
            passes_completed=("passes_completed", "sum"),
            passes_attempted=("passes_attempted", "sum"),
            touches=("touches", "sum"),
            carries=("carries", "sum"),
            shot_creating_actions=("shot_creating_actions", "sum"),
            goal_creating_actions=("goal_creating_actions", "sum"),
            recoveries=("recoveries", "sum"),
            fouls_committed=("fouls_committed", "sum"),
            fouls_drawn=("fouls_drawn", "sum"),
            miscontrols=("miscontrols", "sum"),
            dispossessed=("dispossessed", "sum"),
            yellow_cards=("yellow_cards", "sum"),
            red_cards=("red_cards", "sum"),
            goals_against=("goals_against", "sum"),
            shots_on_target_against=("shots_on_target_against", "sum"),
            saves=("saves", "sum"),
            clean_sheets=("clean_sheets", "sum"),
            apps=("apps", "sum"),
            players=("player_name", "nunique"),
        )
        .reset_index()
    )
    agg = add_pass_pct(agg)
    agg = add_defensive_actions(agg)
    agg = add_per90(
        agg,
        [
            "goals",
            "assists",
            "np_goals",
            "xg",
            "xa",
            "shots",
            "shots_on_target",
            "key_passes",
            "dribbles",
            "tackles",
            "tackles_won",
            "interceptions",
            "blocks",
            "clearances",
            "passes_into_pen_area",
            "shot_creating_actions",
            "goal_creating_actions",
            "recoveries",
            "carries",
        ],
    )
    agg = add_goalkeeping_metrics(agg)
    agg = add_goal_contributions(agg)
    agg = add_possession_losses(agg)
    return agg


def aggregate_by_team(df: pd.DataFrame) -> pd.DataFrame:
    group_cols = ["league_name", "team_name"]
    agg = (
        df.groupby(group_cols)
        .agg(
            minutes=("minutes", "sum"),
            goals=("goals", "sum"),
            assists=("assists", "sum"),
            np_goals=("np_goals", "sum"),
            xg=("xg", "sum"),
            xa=("xa", "sum"),
            shots=("shots", "sum"),
            shots_on_target=("shots_on_target", "sum"),
            key_passes=("key_passes", "sum"),
            dribbles=("dribbles", "sum"),
            tackles=("tackles", "sum"),
            tackles_won=("tackles_won", "sum"),
            interceptions=("interceptions", "sum"),
            blocks=("blocks", "sum"),
            clearances=("clearances", "sum"),
            passes_completed=("passes_completed", "sum"),
            passes_attempted=("passes_attempted", "sum"),
            touches=("touches", "sum"),
            carries=("carries", "sum"),
            passes_into_pen_area=("passes_into_pen_area", "sum"),
            shot_creating_actions=("shot_creating_actions", "sum"),
            goal_creating_actions=("goal_creating_actions", "sum"),
            recoveries=("recoveries", "sum"),
            fouls_committed=("fouls_committed", "sum"),
            fouls_drawn=("fouls_drawn", "sum"),
            miscontrols=("miscontrols", "sum"),
            dispossessed=("dispossessed", "sum"),
            yellow_cards=("yellow_cards", "sum"),
            red_cards=("red_cards", "sum"),
            goals_against=("goals_against", "sum"),
            shots_on_target_against=("shots_on_target_against", "sum"),
            saves=("saves", "sum"),
            clean_sheets=("clean_sheets", "sum"),
            apps=("apps", "sum"),
        )
        .reset_index()
    )
    agg = add_pass_pct(agg)
    agg = add_defensive_actions(agg)
    agg = add_per90(
        agg,
        [
            "goals",
            "assists",
            "xg",
            "xa",
            "shots",
            "shots_on_target",
            "key_passes",
            "tackles",
            "tackles_won",
            "interceptions",
            "blocks",
            "clearances",
            "passes_into_pen_area",
            "shot_creating_actions",
            "goal_creating_actions",
            "recoveries",
            "carries",
        ],
    )
    agg = add_goalkeeping_metrics(agg)
    agg = add_goal_contributions(agg)
    agg = add_possession_losses(agg)
    return agg


def per90_columns(per90: bool) -> list[str]:
    if per90:
        return [f"{col}_per90" for col in PER90_BASE_COLS]
    return PER90_BASE_COLS


def format_metric(df: pd.DataFrame, cols: list[str], decimals: int = 2) -> pd.DataFrame:
    df = df.copy()
    for col in cols:
        if col in df.columns:
            df[col] = (df[col]).round(decimals)
    return df


def filter_min_minutes(df: pd.DataFrame, min_minutes: int) -> pd.DataFrame:
    return df[df["minutes"] >= min_minutes]
