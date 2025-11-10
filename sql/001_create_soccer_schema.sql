CREATE TABLE IF NOT EXISTS leagues (
    league_id      INT AUTO_INCREMENT PRIMARY KEY,
    league_name    VARCHAR(64) NOT NULL,
    UNIQUE KEY uniq_league_name (league_name)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS teams (
    team_id     INT AUTO_INCREMENT PRIMARY KEY,
    team_name   VARCHAR(64) NOT NULL,
    league_id   INT NOT NULL,
    UNIQUE KEY uniq_team_league (team_name, league_id),
    KEY idx_team_league (league_id),
    CONSTRAINT fk_team_league FOREIGN KEY (league_id)
        REFERENCES leagues(league_id)
        ON UPDATE CASCADE ON DELETE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS players (
    player_id        INT AUTO_INCREMENT PRIMARY KEY,
    player_name      VARCHAR(96) NOT NULL,
    nationality      VARCHAR(32),
    primary_position VARCHAR(16),
    created_at       TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at       TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY uniq_player_nat (player_name, nationality)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS player_stats (
    stat_id                 BIGINT AUTO_INCREMENT PRIMARY KEY,
    player_id               INT NOT NULL,
    team_id                 INT NOT NULL,
    league_id               INT NOT NULL,
    season                  VARCHAR(16) NOT NULL,
    position                VARCHAR(16),
    apps                    SMALLINT DEFAULT 0,
    starts                  SMALLINT DEFAULT 0,
    minutes                 INT DEFAULT 0,
    goals                   SMALLINT DEFAULT 0,
    assists                 SMALLINT DEFAULT 0,
    np_goals                SMALLINT DEFAULT 0,
    penalties               SMALLINT DEFAULT 0,
    penalty_att             SMALLINT DEFAULT 0,
    yellow_cards            SMALLINT DEFAULT 0,
    red_cards               SMALLINT DEFAULT 0,
    xg                      DECIMAL(6,3) DEFAULT 0,
    xa                      DECIMAL(6,3) DEFAULT 0,
    npxg                    DECIMAL(6,3) DEFAULT 0,
    shots                   SMALLINT DEFAULT 0,
    shots_on_target         SMALLINT DEFAULT 0,
    key_passes              SMALLINT DEFAULT 0,
    dribbles                SMALLINT DEFAULT 0,
    tackles                 SMALLINT DEFAULT 0,
    interceptions           SMALLINT DEFAULT 0,
    touches                 INT DEFAULT 0,
    passes_completed        INT DEFAULT 0,
    passes_attempted        INT DEFAULT 0,
    progressive_passes      INT DEFAULT 0,
    progressive_carries     INT DEFAULT 0,
    progressive_receptions  INT DEFAULT 0,
    shot_creating_actions   SMALLINT DEFAULT 0,
    goal_creating_actions   SMALLINT DEFAULT 0,
    passes_into_pen_area    INT DEFAULT 0,
    tackles_won             SMALLINT DEFAULT 0,
    blocks                  SMALLINT DEFAULT 0,
    clearances              SMALLINT DEFAULT 0,
    errors                  SMALLINT DEFAULT 0,
    fouls_committed         SMALLINT DEFAULT 0,
    fouls_drawn             SMALLINT DEFAULT 0,
    offsides                SMALLINT DEFAULT 0,
    penalties_won           SMALLINT DEFAULT 0,
    penalties_conceded      SMALLINT DEFAULT 0,
    own_goals               SMALLINT DEFAULT 0,
    recoveries              SMALLINT DEFAULT 0,
    miscontrols             SMALLINT DEFAULT 0,
    dispossessed            SMALLINT DEFAULT 0,
    carries                 INT DEFAULT 0,
    goals_against           SMALLINT DEFAULT 0,
    goals_against_per90     DECIMAL(5,2) DEFAULT 0,
    shots_on_target_against SMALLINT DEFAULT 0,
    saves                   SMALLINT DEFAULT 0,
    save_pct                DECIMAL(5,2) DEFAULT 0,
    wins                    SMALLINT DEFAULT 0,
    draws                   SMALLINT DEFAULT 0,
    losses                  SMALLINT DEFAULT 0,
    clean_sheets            SMALLINT DEFAULT 0,
    clean_sheet_pct         DECIMAL(5,2) DEFAULT 0,
    penalty_kicks_faced     SMALLINT DEFAULT 0,
    penalty_kicks_saved     SMALLINT DEFAULT 0,
    penalty_kicks_missed_against SMALLINT DEFAULT 0,
    created_at              TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at              TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY uniq_player_team_season (player_id, team_id, season),
    KEY idx_ps_league_season (league_id, season),
    KEY idx_ps_team_season (team_id, season),
    KEY idx_ps_player_season (player_id, season),
    CONSTRAINT fk_ps_player FOREIGN KEY (player_id)
        REFERENCES players(player_id)
        ON UPDATE CASCADE ON DELETE RESTRICT,
    CONSTRAINT fk_ps_team FOREIGN KEY (team_id)
        REFERENCES teams(team_id)
        ON UPDATE CASCADE ON DELETE RESTRICT,
    CONSTRAINT fk_ps_league FOREIGN KEY (league_id)
        REFERENCES leagues(league_id)
        ON UPDATE CASCADE ON DELETE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
