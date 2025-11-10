from __future__ import annotations

from typing import Iterable, List, Optional, Sequence

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


def player_radar(data: pd.DataFrame, metrics: List[str], colors: Optional[Sequence[str]] = None) -> go.Figure:
    fig = go.Figure()
    palette = colors or ["#1f77b4", "#ff7f0e", "#2ca02c", "#d62728"]
    for idx, (_, row) in enumerate(data.iterrows()):
        values = [row[m] for m in metrics]
        fig.add_trace(
            go.Scatterpolar(
                r=values + [values[0]],
                theta=metrics + [metrics[0]],
                fill="toself",
                name=row["player_name"],
                line=dict(color=palette[idx % len(palette)], width=2),
                fillcolor=palette[idx % len(palette)],
                opacity=0.4,
            )
        )
    fig.update_layout(
        polar=dict(radialaxis=dict(visible=True, linewidth=0.5, gridcolor="#cccccc")),
        legend=dict(orientation="h"),
        title="Per-90 comparison",
    )
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


def possession_vs_pass(df: pd.DataFrame, color_field: str = "league_name") -> alt.Chart:
    data = df.copy()
    if "touches_per90" not in data.columns and {"touches", "minutes"}.issubset(data.columns):
        data["touches_per90"] = (data["touches"] / data["minutes"].clip(lower=1)) * 90
    if "progressive_passes_per90" not in data.columns and {"progressive_passes", "minutes"}.issubset(data.columns):
        data["progressive_passes_per90"] = (data["progressive_passes"] / data["minutes"].clip(lower=1)) * 90
    color_field = color_field if color_field in data.columns else None
    plot = (
        alt.Chart(data.dropna(subset=["touches_per90", "pass_pct"]))
        .mark_circle()
        .encode(
            x=alt.X("touches_per90:Q", title="Touches/90"),
            y=alt.Y("pass_pct:Q", title="Pass %"),
            size=alt.Size("progressive_passes_per90:Q", title="PrgP/90", legend=None),
            tooltip=[
                "league_name",
                alt.Tooltip("touches_per90:Q", format=".1f"),
                alt.Tooltip("pass_pct:Q", format=".1f"),
                alt.Tooltip("progressive_passes_per90:Q", format=".1f"),
            ],
        )
        .properties(title="Possession vs Pass %", height=360)
    )
    if color_field:
        plot = plot.encode(color=alt.Color(f"{color_field}:N", title=color_field.replace("_", " ").title()))
    return plot


def goalkeeper_save_bar(df: pd.DataFrame) -> alt.Chart:
    data = df.copy()
    metric = "save_pct_calc" if "save_pct_calc" in data.columns else "save_pct"
    ga_metric = "ga_per90" if "ga_per90" in data.columns else "goals_against"
    data = data.fillna({metric: 0, ga_metric: 0})
    return (
        alt.Chart(data)
        .mark_bar()
        .encode(
            x=alt.X("league_name:N", title="League", sort="-y"),
            y=alt.Y(f"{metric}:Q", title="Save %"),
            color=alt.Color("league_name:N", legend=None),
            tooltip=["league_name", alt.Tooltip(metric, format=".1f"), alt.Tooltip(ga_metric, title="GA/90", format=".2f")],
        )
        .properties(title="Goalkeeper save % by league", height=320)
    )


def player_possession_loss_chart(df: pd.DataFrame) -> alt.Chart:
    data = df.copy()
    metric = "possession_losses_per90" if "possession_losses_per90" in data.columns else "possession_losses"
    data = data.nlargest(10, metric)
    return (
        alt.Chart(data)
        .mark_bar()
        .encode(
            x=alt.X(f"{metric}:Q", title="Losses"),
            y=alt.Y("player_name:N", sort="-x", title="Player"),
            color=alt.Color(f"{metric}:Q", legend=None, scale=alt.Scale(scheme="orangered")),
            tooltip=["player_name", "minutes", alt.Tooltip(metric, format=".2f")],
        )
        .properties(title="Possession losses (top 10)", height=320)
    )


def player_progression_scatter(df: pd.DataFrame) -> alt.Chart:
    data = df.copy()
    if "progressive_passes_per90" not in data.columns and {"progressive_passes", "minutes"}.issubset(data.columns):
        data["progressive_passes_per90"] = (data["progressive_passes"] / data["minutes"].clip(lower=1)) * 90
    if "progressive_carries_per90" not in data.columns and {"progressive_carries", "minutes"}.issubset(data.columns):
        data["progressive_carries_per90"] = (data["progressive_carries"] / data["minutes"].clip(lower=1)) * 90
    return (
        alt.Chart(data)
        .mark_circle()
        .encode(
            x=alt.X("progressive_passes_per90:Q", title="Progressive passes/90"),
            y=alt.Y("progressive_carries_per90:Q", title="Progressive carries/90"),
            size=alt.Size("minutes:Q", title="Minutes", legend=None),
            color=alt.Color("player_name:N", legend=None),
            tooltip=["player_name", alt.Tooltip("progressive_passes_per90:Q", format=".2f"), alt.Tooltip("progressive_carries_per90:Q", format=".2f")],
        )
        .properties(title="Progression map", height=320)
    )


def player_metric_bar(df: pd.DataFrame, metrics: Sequence[str]) -> alt.Chart:
    if not metrics:
        return alt.Chart(pd.DataFrame({"player_name": [], "metric": [], "value": []})).mark_bar()
    subset_cols = ["player_name"] + [col for col in metrics if col in df.columns]
    data = df[subset_cols].melt(id_vars="player_name", var_name="metric", value_name="value")
    return (
        alt.Chart(data)
        .mark_bar()
        .encode(
            x=alt.X("metric:N", title="Metric"),
            y=alt.Y("value:Q", title="Value"),
            color=alt.Color("player_name:N", title="Player"),
            column=alt.Column("player_name:N", title=""),
            tooltip=["player_name", "metric", alt.Tooltip("value:Q", format=".2f")],
        )
        .properties(height=320, title="Selected metric comparison")
    )


def leaderboard_metric_chart(df: pd.DataFrame, metric_label: str) -> alt.Chart:
    data = df.copy()
    return (
        alt.Chart(data)
        .mark_bar()
        .encode(
            x=alt.X(f"{metric_label}:Q", title=metric_label),
            y=alt.Y("player_name:N", sort="-x"),
            color=alt.Color("league_name:N", title="League"),
            tooltip=["player_name", "team_name", "league_name", alt.Tooltip(metric_label, format=".2f")],
        )
        .properties(title=f"Top performers – {metric_label}", height=360)
    )


def metric_distribution(df: pd.DataFrame, column: str, label: str) -> alt.Chart:
    data = df[[column]].dropna()
    return (
        alt.Chart(data)
        .mark_bar()
        .encode(
            x=alt.X(f"{column}:Q", title=label, bin=alt.Bin(maxbins=30)),
            y=alt.Y("count()", title="Frequency"),
        )
        .properties(title=f"{label} distribution", height=300)
    )


def custom_metric_chart(
    df: pd.DataFrame,
    x_col: str,
    y_col: str,
    color_col: Optional[str],
    chart_type: str,
    title: str,
) -> alt.Chart:
    data = df[[c for c in [x_col, y_col, color_col] if c and c in df.columns]].copy()
    base = alt.Chart(data).encode(
        x=alt.X(f"{x_col}:Q", title=x_col),
        y=alt.Y(f"{y_col}:Q", title=y_col),
        tooltip=[alt.Tooltip(f"{x_col}:Q", format=".2f"), alt.Tooltip(f"{y_col}:Q", format=".2f")],
    )
    if color_col and color_col in data.columns:
        base = base.encode(color=alt.Color(f"{color_col}:Q", title=color_col))
    chart_type = chart_type.lower()
    if chart_type == "bar":
        chart = base.mark_bar()
    elif chart_type == "line":
        chart = base.mark_line(point=True)
    else:
        chart = base.mark_circle(size=80, opacity=0.8)
    return chart.properties(title=title, height=360)
