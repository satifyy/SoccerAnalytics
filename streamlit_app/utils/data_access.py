from __future__ import annotations

import os
from typing import Iterable, List, Optional, Sequence, Tuple

import mysql.connector
import pandas as pd
import streamlit as st

CACHE_TTL_SECONDS = 300

REQUIRED_ENV = ["DB_HOST", "DB_PORT", "DB_NAME", "DB_USER", "DB_PASSWORD"]


def _db_config() -> Tuple[dict, List[str]]:
    """Read DB config from env vars or Streamlit secrets."""
    secrets = st.secrets.get("mysql", {}) if hasattr(st, "secrets") and "mysql" in st.secrets else {}
    config = {
        "host": secrets.get("host") or os.getenv("DB_HOST"),
        "port": int(secrets.get("port") or os.getenv("DB_PORT", "3306")),
        "database": secrets.get("database") or os.getenv("DB_NAME"),
        "user": secrets.get("user") or os.getenv("DB_USER"),
        "password": secrets.get("password") or os.getenv("DB_PASSWORD"),
    }
    missing = [k for k in ["host", "port", "database", "user", "password"] if not config.get(k)]
    return config, missing


@st.cache_resource(show_spinner=False)
def get_connection():
    config, missing = _db_config()
    if missing:
        missing_env = [env for env in REQUIRED_ENV if os.getenv(env) in (None, "")]
        raise RuntimeError(
            "Missing DB configuration. Set env vars DB_HOST/DB_PORT/DB_NAME/DB_USER/DB_PASSWORD "
            "or define [mysql] secrets. Missing: " + ", ".join(missing_env or missing)
        )
    return mysql.connector.connect(**config)


def _execute_dataframe(query: str, params: Optional[Sequence] = None) -> pd.DataFrame:
    conn = get_connection()
    try:
        conn.ping(reconnect=True, attempts=3, delay=2)
    except mysql.connector.Error:
        get_connection.clear()
        conn = get_connection()
    df = pd.read_sql(query, conn, params=params)
    return df


@st.cache_data(ttl=CACHE_TTL_SECONDS, show_spinner=False)
def get_seasons() -> List[str]:
    query = "SELECT DISTINCT season FROM player_stats ORDER BY season DESC"
    df = _execute_dataframe(query)
    return df["season"].tolist()


@st.cache_data(ttl=CACHE_TTL_SECONDS, show_spinner=False)
def get_leagues(season: str) -> List[str]:
    query = (
        "SELECT DISTINCT l.league_name FROM player_stats ps "
        "JOIN leagues l ON ps.league_id = l.league_id "
        "WHERE ps.season = %s ORDER BY l.league_name"
    )
    df = _execute_dataframe(query, (season,))
    return df["league_name"].tolist()


@st.cache_data(ttl=CACHE_TTL_SECONDS, show_spinner=False)
def get_teams(season: str, leagues: Optional[Sequence[str]] = None) -> List[str]:
    if leagues:
        leagues = tuple(leagues)
    params: List = [season]
    where = ["ps.season = %s"]
    if leagues:
        placeholders = ",".join(["%s"] * len(leagues))
        where.append(f"l.league_name IN ({placeholders})")
        params.extend(leagues)
    query = (
        "SELECT DISTINCT t.team_name FROM player_stats ps "
        "JOIN teams t ON ps.team_id = t.team_id "
        "JOIN leagues l ON ps.league_id = l.league_id "
        f"WHERE {' AND '.join(where)} ORDER BY t.team_name"
    )
    df = _execute_dataframe(query, params)
    return df["team_name"].tolist()


@st.cache_data(ttl=CACHE_TTL_SECONDS, show_spinner=False)
def get_positions(season: str) -> List[str]:
    query = (
        "SELECT DISTINCT position FROM player_stats "
        "WHERE position IS NOT NULL AND position <> '' AND season = %s ORDER BY position"
    )
    df = _execute_dataframe(query, (season,))
    return df["position"].tolist()


def _build_filters(
    season: str,
    min_minutes: int,
    leagues: Optional[Sequence[str]] = None,
    teams: Optional[Sequence[str]] = None,
    positions: Optional[Sequence[str]] = None,
) -> Tuple[str, List]:
    where = ["ps.season = %s", "ps.minutes >= %s"]
    params: List = [season, min_minutes]
    if leagues:
        placeholders = ",".join(["%s"] * len(leagues))
        where.append(f"l.league_name IN ({placeholders})")
        params.extend(leagues)
    if teams:
        placeholders = ",".join(["%s"] * len(teams))
        where.append(f"t.team_name IN ({placeholders})")
        params.extend(teams)
    if positions:
        placeholders = ",".join(["%s"] * len(positions))
        where.append(f"ps.position IN ({placeholders})")
        params.extend(positions)
    clause = " AND ".join(where)
    return clause, params


PLAYER_COLUMNS_SQL = """
    ps.stat_id,
    ps.season,
    l.league_name,
    t.team_name,
    p.player_name,
    p.nationality,
    ps.position,
    ps.apps,
    ps.starts,
    ps.minutes,
    ps.goals,
    ps.assists,
    ps.np_goals,
    ps.penalties,
    ps.penalty_att,
    ps.yellow_cards,
    ps.red_cards,
    ps.xg,
    ps.xa,
    ps.npxg,
    ps.shots,
    ps.shots_on_target,
    ps.key_passes,
    ps.dribbles,
    ps.tackles,
    ps.interceptions,
    ps.touches,
    ps.passes_completed,
    ps.passes_attempted,
    ps.progressive_passes,
    ps.progressive_carries,
    ps.progressive_receptions,
    ps.shot_creating_actions,
    ps.goal_creating_actions,
    ps.passes_into_pen_area,
    ps.tackles_won,
    ps.blocks,
    ps.clearances,
    ps.errors,
    ps.fouls_committed,
    ps.fouls_drawn,
    ps.offsides,
    ps.penalties_won,
    ps.penalties_conceded,
    ps.own_goals,
    ps.recoveries,
    ps.miscontrols,
    ps.dispossessed,
    ps.carries,
    ps.goals_against,
    ps.goals_against_per90,
    ps.shots_on_target_against,
    ps.saves,
    ps.save_pct,
    ps.wins,
    ps.draws,
    ps.losses,
    ps.clean_sheets,
    ps.clean_sheet_pct,
    ps.penalty_kicks_faced,
    ps.penalty_kicks_saved,
    ps.penalty_kicks_missed_against
"""


@st.cache_data(ttl=CACHE_TTL_SECONDS, show_spinner=False)
def fetch_player_stats(
    season: str,
    min_minutes: int,
    leagues: Optional[Sequence[str]] = None,
    teams: Optional[Sequence[str]] = None,
    positions: Optional[Sequence[str]] = None,
) -> pd.DataFrame:
    if leagues:
        leagues = tuple(leagues)
    if teams:
        teams = tuple(teams)
    if positions:
        positions = tuple(positions)
    where, params = _build_filters(season, min_minutes, leagues, teams, positions)
    query = (
        "SELECT "
        + PLAYER_COLUMNS_SQL
        + " FROM player_stats ps "
        + "JOIN players p ON ps.player_id = p.player_id "
        + "JOIN teams t ON ps.team_id = t.team_id "
        + "JOIN leagues l ON ps.league_id = l.league_id "
        + f"WHERE {where}"
    )
    return _execute_dataframe(query, params)


@st.cache_data(ttl=CACHE_TTL_SECONDS, show_spinner=False)
def fetch_team_summary(season: str, league: str, team: str, min_minutes: int) -> pd.DataFrame:
    return fetch_player_stats(season, min_minutes, leagues=[league], teams=[team])
