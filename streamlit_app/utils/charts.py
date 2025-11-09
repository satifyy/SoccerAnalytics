from __future__ import annotations

from typing import Iterable, List, Optional

import altair as alt
import pandas as pd
import plotly.graph_objects as go


def league_xg_bar(df: pd.DataFrame, per90: bool = True) -> alt.Chart:
    metric = "xg_per90" if per90 and "xg_per90" in df.columns else "xg"
    title = "Avg xG/90 by league" if metric.endswith("per90") else "Total xG by league"
    return (
        alt.Chart(df)
        .mark_bar(cornerRadiusTopLeft=4, cornerRadiusTopRight=4)
        .encode(
            x=alt.X("league_name:N", sort="-y"),
            y=alt.Y(f"{metric}:Q", title="xG"),
            tooltip=["league_name", alt.Tooltip(metric, format=".2f")],
            color=alt.Color("league_name:N", legend=None),
        )
        .properties(height=300, title=title)
    )


def league_goals_box(df: pd.DataFrame) -> alt.Chart:
    base = df.copy()
    if "goals_per90" not in base.columns:
        base["goals_per90"] = (base["goals"] / base["minutes"].clip(lower=1)) * 90
    return (
        alt.Chart(base)
        .mark_boxplot(extent="min-max")
        .encode(
            x=alt.X("league_name:N", title="League"),
            y=alt.Y("goals_per90:Q", title="Goals/90"),
            color=alt.Color("league_name:N", legend=None),
        )
        .properties(height=320, title="Goals/90 distribution by league")
    )


def league_scatter(df: pd.DataFrame, per90: bool = True) -> alt.Chart:
    x_metric = "xg_per90" if per90 and "xg_per90" in df.columns else "xg"
    y_metric = "goals_per90" if per90 and "goals_per90" in df.columns else "goals"
    size_metric = "shots_per90" if per90 and "shots_per90" in df.columns else "shots"
    tooltip = ["league_name", alt.Tooltip(x_metric, format=".2f"), alt.Tooltip(y_metric, format=".2f")]
    return (
        alt.Chart(df)
        .mark_circle(opacity=0.85)
        .encode(
            x=alt.X(f"{x_metric}:Q", title="xG"),
            y=alt.Y(f"{y_metric}:Q", title="Goals"),
            size=alt.Size(f"{size_metric}:Q", title="Shots", legend=None),
            color=alt.Color("league_name:N", legend=None),
            tooltip=tooltip,
        )
        .properties(height=360, title="xG vs Goals by league")
    )


def stacked_player_contributions(df: pd.DataFrame) -> alt.Chart:
    melted = df.melt(
        id_vars=["player_name"],
        value_vars=["goals", "xg", "assists", "xa"],
        var_name="metric",
        value_name="value",
    )
    return (
        alt.Chart(melted)
        .mark_bar()
        .encode(
            x=alt.X("player_name:N", title="Player"),
            y=alt.Y("value:Q", stack="zero", title="Contribution"),
            color=alt.Color("metric:N", title="Metric"),
            tooltip=["player_name", "metric", alt.Tooltip("value:Q", format=".2f")],
        )
        .properties(height=360)
    )


def team_heatmap(team_df: pd.DataFrame, league_df: pd.DataFrame) -> alt.Chart:
    merged = team_df.merge(league_df, on="metric", suffixes=("_team", "_league"))
    merged["delta"] = merged["value_team"] - merged["value_league"]
    return (
        alt.Chart(merged)
        .mark_rect()
        .encode(
            y=alt.Y("metric:N", title="Metric"),
            color=alt.Color("delta:Q", scale=alt.Scale(scheme="redblue"), title="Δ vs league"),
            tooltip=["metric", alt.Tooltip("value_team:Q", title="Team"), alt.Tooltip("value_league:Q", title="League"), alt.Tooltip("delta:Q", title="Δ")],
        )
        .properties(height=220, title="Team vs league average (per-90)")
    )


def player_radar(data: pd.DataFrame, metrics: List[str]) -> go.Figure:
    fig = go.Figure()
    for _, row in data.iterrows():
        values = [row[m] for m in metrics]
        fig.add_trace(
            go.Scatterpolar(r=values + [values[0]], theta=metrics + [metrics[0]], fill="toself", name=row["player_name"])
        )
    fig.update_layout(polar=dict(radialaxis=dict(visible=True)), showlegend=True, title="Per-90 comparison")
    return fig


def player_scatter(df: pd.DataFrame, highlight: Iterable[str]) -> alt.Chart:
    df = df.copy()
    df["is_target"] = df["player_name"].isin(list(highlight))
    return (
        alt.Chart(df)
        .mark_circle()
        .encode(
            x=alt.X("xg_per90:Q", title="xG/90"),
            y=alt.Y("xa_per90:Q", title="xA/90"),
            size=alt.Size("shots_per90:Q", title="Shots/90", legend=None),
            color=alt.Color("is_target:N", scale=alt.Scale(range=["#BBBBBB", "#2b83ba"]), legend=None),
            tooltip=["player_name", "team_name", alt.Tooltip("xg_per90:Q", format=".2f"), alt.Tooltip("xa_per90:Q", format=".2f")],
        )
        .properties(height=360, title="xG vs xA (per-90)")
    )
