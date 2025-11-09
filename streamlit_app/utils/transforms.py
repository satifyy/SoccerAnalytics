from __future__ import annotations

import pandas as pd

PER90_BASE_COLS = [
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
            "touches",
            "passes_completed",
            "passes_attempted",
            "progressive_passes",
            "progressive_carries",
            "progressive_receptions",
            "shot_creating_actions",
            "goal_creating_actions",
        ],
    )
    df = add_per90(df)
    df = add_pass_pct(df)
    df = add_defensive_actions(df)
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
            key_passes=("key_passes", "sum"),
            dribbles=("dribbles", "sum"),
            tackles=("tackles", "sum"),
            interceptions=("interceptions", "sum"),
            passes_completed=("passes_completed", "sum"),
            passes_attempted=("passes_attempted", "sum"),
            touches=("touches", "sum"),
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
            "key_passes",
            "dribbles",
            "tackles",
            "interceptions",
        ],
    )
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
            key_passes=("key_passes", "sum"),
            dribbles=("dribbles", "sum"),
            tackles=("tackles", "sum"),
            interceptions=("interceptions", "sum"),
            passes_completed=("passes_completed", "sum"),
            passes_attempted=("passes_attempted", "sum"),
            touches=("touches", "sum"),
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
            "key_passes",
            "tackles",
            "interceptions",
        ],
    )
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
