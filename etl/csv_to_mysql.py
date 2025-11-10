#!/usr/bin/env python3
"""Load the FBRef light CSV into the MySQL schema.

Usage:
    python etl/csv_to_mysql.py --csv ../players_data-2024_2025.csv

Environment variables (or .env file) must provide:
    DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD
"""

from __future__ import annotations

import argparse
import csv
import os
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Optional

import mysql.connector
from mysql.connector.connection import MySQLConnection
from mysql.connector.cursor import MySQLCursor
from dotenv import load_dotenv

SEASON = "2024-2025"
DEFAULT_CSV = Path(__file__).resolve().parents[1] / "players_data-2024_2025.csv"

@dataclass
class Caches:
    leagues: Dict[str, int]
    teams: Dict[tuple, int]
    players: Dict[tuple, int]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Load FBRef CSV into MySQL")
    parser.add_argument("--csv", type=Path, default=DEFAULT_CSV, help="Path to the CSV export")
    parser.add_argument("--season", default=SEASON, help="Season label to store")
    parser.add_argument("--batch-size", type=int, default=500, help="Commit interval")
    return parser.parse_args()


def get_db() -> MySQLConnection:
    load_dotenv()
    config = {
        "host": os.getenv("DB_HOST"),
        "port": int(os.getenv("DB_PORT", "3306")),
        "database": os.getenv("DB_NAME"),
        "user": os.getenv("DB_USER"),
        "password": os.getenv("DB_PASSWORD"),
        "autocommit": False,
    }
    missing = [k for k, v in config.items() if v in (None, "")]
    if missing:
        raise RuntimeError(f"Missing DB config values: {', '.join(missing)}")
    return mysql.connector.connect(**config)


def load_existing(cursor: MySQLCursor) -> Caches:
    cursor.execute("SELECT league_id, league_name FROM leagues")
    leagues = {name: lid for lid, name in cursor.fetchall()}

    cursor.execute("SELECT team_id, team_name, league_id FROM teams")
    teams = {(name, league_id): tid for tid, name, league_id in cursor.fetchall()}

    cursor.execute("SELECT player_id, player_name, COALESCE(nationality, '') FROM players")
    players = {(name, nat): pid for pid, name, nat in cursor.fetchall()}

    return Caches(leagues=leagues, teams=teams, players=players)


def upsert_league(cursor: MySQLCursor, caches: Caches, league_name: str) -> int:
    league_name = league_name.strip()
    if league_name in caches.leagues:
        return caches.leagues[league_name]
    cursor.execute(
        """
        INSERT INTO leagues (league_name)
        VALUES (%s)
        ON DUPLICATE KEY UPDATE league_id = LAST_INSERT_ID(league_id)
        """,
        (league_name,),
    )
    league_id = cursor.lastrowid
    caches.leagues[league_name] = league_id
    return league_id


def upsert_team(cursor: MySQLCursor, caches: Caches, team_name: str, league_id: int) -> int:
    key = (team_name, league_id)
    if key in caches.teams:
        return caches.teams[key]
    cursor.execute(
        """
        INSERT INTO teams (team_name, league_id)
        VALUES (%s, %s)
        ON DUPLICATE KEY UPDATE team_id = LAST_INSERT_ID(team_id)
        """,
        (team_name, league_id),
    )
    team_id = cursor.lastrowid
    caches.teams[key] = team_id
    return team_id


def upsert_player(cursor: MySQLCursor, caches: Caches, player_name: str, nationality: str, primary_position: str) -> int:
    key = (player_name, nationality)
    if key in caches.players:
        pid = caches.players[key]
    else:
        cursor.execute(
            """
            INSERT INTO players (player_name, nationality, primary_position)
            VALUES (%s, %s, %s)
            ON DUPLICATE KEY UPDATE
                primary_position = VALUES(primary_position),
                player_id = LAST_INSERT_ID(player_id)
            """,
            (player_name, nationality or None, primary_position or None),
        )
        pid = cursor.lastrowid
        caches.players[key] = pid
    return pid


def to_int(value: str) -> Optional[int]:
    value = (value or "").strip()
    if not value:
        return 0
    try:
        return int(round(float(value)))
    except ValueError:
        return 0


def to_float(value: str) -> Optional[float]:
    value = (value or "").strip()
    if not value:
        return 0.0
    try:
        return round(float(value), 3)
    except ValueError:
        return 0.0


def clean_position(pos: str) -> str:
    if not pos:
        return ""
    return pos.split(",")[0].strip()


def insert_player_stat(cursor: MySQLCursor, record: dict) -> None:
    cursor.execute(
        """
        INSERT INTO player_stats (
            player_id, team_id, league_id, season, position, apps, starts, minutes,
            goals, assists, np_goals, penalties, penalty_att, yellow_cards, red_cards,
            xg, xa, npxg, shots, shots_on_target, key_passes, dribbles,
            tackles, interceptions, touches, passes_completed, passes_attempted,
            progressive_passes, progressive_carries, progressive_receptions,
            shot_creating_actions, goal_creating_actions, passes_into_pen_area,
            tackles_won, blocks, clearances, errors, fouls_committed,
            fouls_drawn, offsides, penalties_won, penalties_conceded,
            own_goals, recoveries, miscontrols, dispossessed, carries,
            goals_against, goals_against_per90, shots_on_target_against, saves,
            save_pct, wins, draws, losses, clean_sheets, clean_sheet_pct,
            penalty_kicks_faced, penalty_kicks_saved, penalty_kicks_missed_against
        ) VALUES (
            %(player_id)s, %(team_id)s, %(league_id)s, %(season)s, %(position)s,
            %(apps)s, %(starts)s, %(minutes)s, %(goals)s, %(assists)s, %(np_goals)s,
            %(penalties)s, %(penalty_att)s, %(yellow_cards)s, %(red_cards)s, %(xg)s, %(xa)s, %(npxg)s, %(shots)s,
            %(shots_on_target)s, %(key_passes)s, %(dribbles)s, %(tackles)s,
            %(interceptions)s, %(touches)s, %(passes_completed)s, %(passes_attempted)s,
            %(progressive_passes)s, %(progressive_carries)s, %(progressive_receptions)s,
            %(shot_creating_actions)s, %(goal_creating_actions)s, %(passes_into_pen_area)s,
            %(tackles_won)s, %(blocks)s, %(clearances)s, %(errors)s, %(fouls_committed)s,
            %(fouls_drawn)s, %(offsides)s, %(penalties_won)s, %(penalties_conceded)s,
            %(own_goals)s, %(recoveries)s, %(miscontrols)s, %(dispossessed)s, %(carries)s,
            %(goals_against)s, %(goals_against_per90)s, %(shots_on_target_against)s, %(saves)s,
            %(save_pct)s, %(wins)s, %(draws)s, %(losses)s, %(clean_sheets)s, %(clean_sheet_pct)s,
            %(penalty_kicks_faced)s, %(penalty_kicks_saved)s, %(penalty_kicks_missed_against)s
        )
        ON DUPLICATE KEY UPDATE
            position = VALUES(position),
            apps = VALUES(apps),
            starts = VALUES(starts),
            minutes = VALUES(minutes),
            goals = VALUES(goals),
            assists = VALUES(assists),
            np_goals = VALUES(np_goals),
            penalties = VALUES(penalties),
            penalty_att = VALUES(penalty_att),
            yellow_cards = VALUES(yellow_cards),
            red_cards = VALUES(red_cards),
            xg = VALUES(xg),
            xa = VALUES(xa),
            npxg = VALUES(npxg),
            shots = VALUES(shots),
            shots_on_target = VALUES(shots_on_target),
            key_passes = VALUES(key_passes),
            dribbles = VALUES(dribbles),
            tackles = VALUES(tackles),
            interceptions = VALUES(interceptions),
            touches = VALUES(touches),
            passes_completed = VALUES(passes_completed),
            passes_attempted = VALUES(passes_attempted),
            progressive_passes = VALUES(progressive_passes),
            progressive_carries = VALUES(progressive_carries),
            progressive_receptions = VALUES(progressive_receptions),
            shot_creating_actions = VALUES(shot_creating_actions),
            goal_creating_actions = VALUES(goal_creating_actions),
            passes_into_pen_area = VALUES(passes_into_pen_area),
            tackles_won = VALUES(tackles_won),
            blocks = VALUES(blocks),
            clearances = VALUES(clearances),
            errors = VALUES(errors),
            fouls_committed = VALUES(fouls_committed),
            fouls_drawn = VALUES(fouls_drawn),
            offsides = VALUES(offsides),
            penalties_won = VALUES(penalties_won),
            penalties_conceded = VALUES(penalties_conceded),
            own_goals = VALUES(own_goals),
            recoveries = VALUES(recoveries),
            miscontrols = VALUES(miscontrols),
            dispossessed = VALUES(dispossessed),
            carries = VALUES(carries),
            goals_against = VALUES(goals_against),
            goals_against_per90 = VALUES(goals_against_per90),
            shots_on_target_against = VALUES(shots_on_target_against),
            saves = VALUES(saves),
            save_pct = VALUES(save_pct),
            wins = VALUES(wins),
            draws = VALUES(draws),
            losses = VALUES(losses),
            clean_sheets = VALUES(clean_sheets),
            clean_sheet_pct = VALUES(clean_sheet_pct),
            penalty_kicks_faced = VALUES(penalty_kicks_faced),
            penalty_kicks_saved = VALUES(penalty_kicks_saved),
            penalty_kicks_missed_against = VALUES(penalty_kicks_missed_against),
            updated_at = CURRENT_TIMESTAMP
        """,
        record,
    )


def main() -> None:
    args = parse_args()
    if not args.csv.exists():
        raise FileNotFoundError(args.csv)

    conn = get_db()
    cursor = conn.cursor()
    caches = load_existing(cursor)

    inserted = 0
    with args.csv.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        batch = 0
        for row in reader:
            season = args.season
            league_name = row["Comp"].strip()
            team_name = row["Squad"].strip()
            player_name = row["Player"].strip()
            nationality = row.get("Nation", "").strip()
            position = row.get("Pos", "").strip()

            league_id = upsert_league(cursor, caches, league_name)
            team_id = upsert_team(cursor, caches, team_name, league_id)
            player_id = upsert_player(cursor, caches, player_name, nationality, clean_position(position))

            record = {
                "player_id": player_id,
                "team_id": team_id,
                "league_id": league_id,
                "season": season,
                "position": position,
                "apps": to_int(row.get("MP")),
                "starts": to_int(row.get("Starts")),
                "minutes": to_int(row.get("Min")),
                "goals": to_int(row.get("Gls")),
                "assists": to_int(row.get("Ast")),
                "np_goals": to_int(row.get("G-PK")),
                "penalties": to_int(row.get("PK")),
                "penalty_att": to_int(row.get("PKatt")),
                "yellow_cards": to_int(row.get("CrdY")),
                "red_cards": to_int(row.get("CrdR")),
                "xg": to_float(row.get("xG")),
                "xa": to_float(row.get("xA")),
                "npxg": to_float(row.get("npxG")),
                "shots": to_int(row.get("Sh")),
                "shots_on_target": to_int(row.get("SoT")),
                "key_passes": to_int(row.get("KP")),
                "dribbles": to_int(row.get("Succ")),
                "tackles": to_int(row.get("Tkl")),
                "interceptions": to_int(row.get("Int")),
                "touches": to_int(row.get("Touches")),
                "passes_completed": to_int(row.get("Cmp")),
                "passes_attempted": to_int(row.get("Att")),
                "progressive_passes": to_int(row.get("PrgP")),
                "progressive_carries": to_int(row.get("PrgC")),
                "progressive_receptions": to_int(row.get("PrgR")),
                "shot_creating_actions": to_int(row.get("SCA")),
                "goal_creating_actions": to_int(row.get("GCA")),
                "passes_into_pen_area": to_int(row.get("PPA")),
                "tackles_won": to_int(row.get("TklW")),
                "blocks": to_int(row.get("Blocks")),
                "clearances": to_int(row.get("Clr")),
                "errors": to_int(row.get("Err")),
                "fouls_committed": to_int(row.get("Fls")),
                "fouls_drawn": to_int(row.get("Fld")),
                "offsides": to_int(row.get("Off")),
                "penalties_won": to_int(row.get("PKwon")),
                "penalties_conceded": to_int(row.get("PKcon")),
                "own_goals": to_int(row.get("OG")),
                "recoveries": to_int(row.get("Recov")),
                "miscontrols": to_int(row.get("Mis")),
                "dispossessed": to_int(row.get("Dis")),
                "carries": to_int(row.get("Carries")),
                "goals_against": to_int(row.get("GA")),
                "goals_against_per90": to_float(row.get("GA90")),
                "shots_on_target_against": to_int(row.get("SoTA")),
                "saves": to_int(row.get("Saves")),
                "save_pct": to_float(row.get("Save%")),
                "wins": to_int(row.get("W")),
                "draws": to_int(row.get("D")),
                "losses": to_int(row.get("L")),
                "clean_sheets": to_int(row.get("CS")),
                "clean_sheet_pct": to_float(row.get("CS%")),
                "penalty_kicks_faced": to_int(row.get("PKA")),
                "penalty_kicks_saved": to_int(row.get("PKsv")),
                "penalty_kicks_missed_against": to_int(row.get("PKm")),
            }
            insert_player_stat(cursor, record)

            inserted += 1
            batch += 1
            if batch >= args.batch_size:
                conn.commit()
                batch = 0
                print(f"Committed {inserted} rows so far…")

    if batch:
        conn.commit()
    cursor.close()
    conn.close()
    print(f"Done. Upserted {inserted} player-season rows for {season}.")


if __name__ == "__main__":
    main()
