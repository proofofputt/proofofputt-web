import os
import logging
import sqlalchemy
import json
import bcrypt
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta, timezone
import pytz # Import pytz for timezone handling
from sqlalchemy.exc import IntegrityError, OperationalError

logger = logging.getLogger('debug_logger')

# Global connector and connection pool to be initialized once.
connector = None
pool = None

def get_db_connection():
    """
    Initializes a connection pool. Uses a PostgreSQL database if DATABASE_URL is set,
    otherwise falls back to a local SQLite database file.
    """
    global pool
    if pool:
        return pool

    db_url = os.environ.get("DATABASE_URL")

    if db_url:
        logger.info("DATABASE_URL found. Connecting to PostgreSQL database.")
        # Add pool_pre_ping to handle dropped connections, common in serverless environments.
        pool = sqlalchemy.create_engine(
            db_url,
            pool_pre_ping=True,
            pool_recycle=300 # Recycle connections every 5 minutes
        )
    else:
        db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "proofofputt_data.db")
        logger.warning(f"DATABASE_URL not set. Falling back to local SQLite DB: {db_path}")
        pool = sqlalchemy.create_engine(f"sqlite:///{db_path}")

    return pool


def initialize_database():
    """Creates the database tables if they don't exist and ensures the default user is present."""
    pool = get_db_connection()
    db_type = pool.dialect.name

    with pool.connect() as conn:
        player_id_type = "SERIAL PRIMARY KEY" if db_type == "postgresql" else "INTEGER PRIMARY KEY"
        session_id_type = "SERIAL PRIMARY KEY" if db_type == "postgresql" else "INTEGER PRIMARY KEY"
        timestamp_type = "TIMESTAMP WITH TIME ZONE" if db_type == "postgresql" else "DATETIME"
        default_timestamp = "CURRENT_TIMESTAMP" if db_type == "postgresql" else "CURRENT_TIMESTAMP"

        with conn.begin() as trans: # Use a single transaction for the entire setup
            conn.execute(sqlalchemy.text(f'''
                    CREATE TABLE IF NOT EXISTS players (
                        player_id {player_id_type},
                        email TEXT UNIQUE NOT NULL,
                        name TEXT NOT NULL,
                        password_hash TEXT NOT NULL,
                        created_at {timestamp_type} DEFAULT {default_timestamp},
                        subscription_status TEXT DEFAULT 'free',
                        zaprite_subscription_id TEXT,
                        timezone TEXT DEFAULT 'UTC',
                        x_url TEXT,
                        tiktok_url TEXT,
                        website_url TEXT,
                        notification_preferences TEXT,
                        calibration_data TEXT
                    )
            '''))

            if db_type == "sqlite":
                columns_to_add = {
                    "x_url": "TEXT",
                    "tiktok_url": "TEXT",
                    "website_url": "TEXT",
                    "notification_preferences": "TEXT",
                    "calibration_data": "TEXT"
                }
                for column, col_type in columns_to_add.items():
                    try:
                        conn.execute(sqlalchemy.text(f"ALTER TABLE players ADD COLUMN {column} {col_type}"))
                        logger.info(f"Added column '{column}' to 'players' table.")
                    except OperationalError as e:
                        if "duplicate column name" in str(e).lower():
                            logger.info(f"Column '{column}' already exists in 'players' table. Skipping.")
                        else:
                            logger.error(f"Error adding column '{column}' to 'players' table: {e}")

            elif db_type == "postgresql":
                # Check if the column exists first to avoid a failing statement within the transaction
                inspector = sqlalchemy.inspect(conn)
                columns = [c['name'] for c in inspector.get_columns('players')]
                if 'calibration_data' not in columns:
                    conn.execute(sqlalchemy.text("ALTER TABLE players ADD COLUMN calibration_data TEXT"))
                    logger.info("Migration: Added column 'calibration_data' to 'players' table.")
                else:
                    logger.info("Migration: Column 'calibration_data' already exists in 'players' table. Skipping.")

            conn.execute(sqlalchemy.text(f'''
                    CREATE TABLE IF NOT EXISTS sessions (
                        session_id {session_id_type},
                        player_id INTEGER NOT NULL,
                        start_time {timestamp_type} DEFAULT {default_timestamp},
                        end_time {timestamp_type},
                        status TEXT,
                        total_putts INTEGER,
                        total_makes INTEGER,
                        total_misses INTEGER,
                        best_streak INTEGER,
                        fastest_21_makes REAL,
                        putts_per_minute REAL,
                        makes_per_minute REAL,
                        most_makes_in_60_seconds INTEGER,
                        session_duration REAL,
                        putt_list TEXT,
                        makes_by_category TEXT,
                        misses_by_category TEXT,
                        FOREIGN KEY (player_id) REFERENCES players (player_id) ON DELETE CASCADE
                    )
            '''))

            conn.execute(sqlalchemy.text(f'''
                    CREATE TABLE IF NOT EXISTS leagues (
                        league_id {session_id_type},
                        creator_id INTEGER NOT NULL,
                        name TEXT NOT NULL,
                        description TEXT,
                        privacy_type TEXT NOT NULL DEFAULT 'private',
                        status TEXT NOT NULL DEFAULT 'registering',
                        settings TEXT,
                        start_time {timestamp_type},
                        created_at {timestamp_type} DEFAULT {default_timestamp},
                        FOREIGN KEY (creator_id) REFERENCES players (player_id) ON DELETE CASCADE
                    )
            '''))

            # Password reset tokens table
            conn.execute(sqlalchemy.text(f'''
                    CREATE TABLE IF NOT EXISTS password_reset_tokens (
                        token_id {session_id_type},
                        player_id INTEGER NOT NULL,
                        token TEXT UNIQUE NOT NULL,
                        expires_at {timestamp_type} NOT NULL,
                        used BOOLEAN DEFAULT FALSE,
                        created_at {timestamp_type} DEFAULT {default_timestamp},
                        FOREIGN KEY (player_id) REFERENCES players (player_id) ON DELETE CASCADE
                    )
            '''))

            # Fundraisers table
            conn.execute(sqlalchemy.text(f'''
                    CREATE TABLE IF NOT EXISTS fundraisers (
                        fundraiser_id {session_id_type},
                        creator_id INTEGER NOT NULL,
                        title TEXT NOT NULL,
                        description TEXT,
                        charity_name TEXT NOT NULL,
                        charity_wallet_address TEXT,
                        target_amount REAL,
                        current_amount REAL DEFAULT 0,
                        sat_per_putt INTEGER DEFAULT 100,
                        start_date {timestamp_type},
                        end_date {timestamp_type},
                        status TEXT DEFAULT 'active',
                        created_at {timestamp_type} DEFAULT {default_timestamp},
                        FOREIGN KEY (creator_id) REFERENCES players (player_id) ON DELETE CASCADE
                    )
            '''))

            # Pledges table
            conn.execute(sqlalchemy.text(f'''
                    CREATE TABLE IF NOT EXISTS pledges (
                        pledge_id {session_id_type},
                        fundraiser_id INTEGER NOT NULL,
                        pledger_id INTEGER NOT NULL,
                        amount_per_putt INTEGER NOT NULL,
                        max_amount REAL,
                        total_pledged REAL DEFAULT 0,
                        total_paid REAL DEFAULT 0,
                        status TEXT DEFAULT 'active',
                        created_at {timestamp_type} DEFAULT {default_timestamp},
                        FOREIGN KEY (fundraiser_id) REFERENCES fundraisers (fundraiser_id) ON DELETE CASCADE,
                        FOREIGN KEY (pledger_id) REFERENCES players (player_id) ON DELETE CASCADE
                    )
            '''))

            if db_type == "sqlite":
                league_columns_to_add = {
                    "name": "TEXT",
                    "description": "TEXT",
                    "privacy_type": "TEXT",
                    "status": "TEXT",
                    "settings": "TEXT",
                    "start_time": "DATETIME",
                    "final_notifications_sent": "BOOLEAN"
                }
                for column, col_type in league_columns_to_add.items():
                    try:
                        conn.execute(sqlalchemy.text(f"ALTER TABLE leagues ADD COLUMN {column} {col_type} DEFAULT ''"))
                        logger.info(f"Added column '{column}' to 'leagues' table.")
                    except OperationalError as e:
                        if "duplicate column name" in str(e).lower():
                            logger.info(f"Column '{column}' already exists in 'leagues' table. Skipping.")
                        else:
                            logger.error(f"Error adding column '{column}' to 'leagues' table: {e}")

            conn.execute(sqlalchemy.text(f'''
                    CREATE TABLE IF NOT EXISTS league_members (
                        member_id INTEGER,
                        league_id INTEGER NOT NULL,
                        player_id INTEGER NOT NULL,
                        status TEXT DEFAULT 'active',
                        created_at {timestamp_type} DEFAULT {default_timestamp},
                        PRIMARY KEY (league_id, player_id),
                        FOREIGN KEY (league_id) REFERENCES leagues (league_id) ON DELETE CASCADE,
                        FOREIGN KEY (player_id) REFERENCES players (player_id) ON DELETE CASCADE
                    )
            '''))

            conn.execute(sqlalchemy.text(f'''
                    CREATE TABLE IF NOT EXISTS league_rounds (
                        round_id {session_id_type},
                        league_id INTEGER NOT NULL,
                        round_number INTEGER NOT NULL,
                        status TEXT DEFAULT 'scheduled',
                        start_time {timestamp_type},
                        end_time {timestamp_type},
                        FOREIGN KEY (league_id) REFERENCES leagues (league_id) ON DELETE CASCADE
                    )
            '''))

            if db_type == "sqlite":
                round_columns_to_add = {
                    "round_number": "INTEGER",
                    "status": "TEXT"
                }
                for column, col_type in round_columns_to_add.items():
                    try:
                        conn.execute(sqlalchemy.text(f"ALTER TABLE league_rounds ADD COLUMN {column} {col_type}"))
                        logger.info(f"Added column '{column}' to 'league_rounds' table.")
                    except OperationalError as e:
                        if "duplicate column name" in str(e).lower():
                            logger.info(f"Column '{column}' already exists in 'league_rounds' table. Skipping.")
                        else:
                            logger.error(f"Error adding column '{column}' to 'league_rounds' table: {e}")

            conn.execute(sqlalchemy.text(f'''
                    CREATE TABLE IF NOT EXISTS league_round_submissions (
                        submission_id {session_id_type},
                        round_id INTEGER NOT NULL,
                        player_id INTEGER NOT NULL,
                        session_id INTEGER NOT NULL,
                        score INTEGER NOT NULL,
                        points_awarded INTEGER NOT NULL,
                        submitted_at {timestamp_type} DEFAULT {default_timestamp},
                        FOREIGN KEY (player_id) REFERENCES players (player_id) ON DELETE CASCADE,
                        FOREIGN KEY (session_id) REFERENCES sessions (session_id) ON DELETE CASCADE,
                        FOREIGN KEY (round_id) REFERENCES league_rounds (round_id) ON DELETE CASCADE
                    )
            '''))

            if db_type == "sqlite":
                submission_columns_to_add = {
                    "player_id": "INTEGER",
                    "session_id": "INTEGER",
                    "score": "INTEGER",
                    "points_awarded": "INTEGER",
                    "submitted_at": "DATETIME"
                }
                for column, col_type in submission_columns_to_add.items():
                    try:
                        conn.execute(sqlalchemy.text(f"ALTER TABLE league_round_submissions ADD COLUMN {column} {col_type}"))
                        logger.info(f"Added column '{column}' to 'league_round_submissions' table.")
                    except OperationalError as e:
                        if "duplicate column name" in str(e).lower():
                            logger.info(f"Column '{column}' already exists in 'league_round_submissions' table. Skipping.")
                        else:
                            logger.error(f"Error adding column '{column}' to 'league_round_submissions' table: {e}")

            conn.execute(sqlalchemy.text(f'''
                    CREATE TABLE IF NOT EXISTS player_stats (
                        player_id INTEGER PRIMARY KEY,
                        total_makes INTEGER DEFAULT 0,
                        total_misses INTEGER DEFAULT 0,
                        total_putts INTEGER DEFAULT 0,
                        best_streak INTEGER DEFAULT 0,
                        fastest_21_makes REAL DEFAULT 0,
                        total_duration REAL DEFAULT 0,
                        last_updated {timestamp_type} DEFAULT {default_timestamp},
                        FOREIGN KEY (player_id) REFERENCES players (player_id) ON DELETE CASCADE
                    )
            '''))
            
            # Add missing columns for existing player_stats tables
            if db_type == "postgresql":
                inspector = sqlalchemy.inspect(conn)
                if inspector.has_table('player_stats'):
                    existing_columns = [c['name'] for c in inspector.get_columns('player_stats')]
                    missing_columns = {
                        'total_makes': 'INTEGER DEFAULT 0',
                        'total_misses': 'INTEGER DEFAULT 0',
                        'best_streak': 'INTEGER DEFAULT 0',
                        'total_duration': 'REAL DEFAULT 0',
                        'last_updated': f'{timestamp_type} DEFAULT {default_timestamp}'
                    }
                    for col_name, col_def in missing_columns.items():
                        if col_name not in existing_columns:
                            try:
                                conn.execute(sqlalchemy.text(f'ALTER TABLE player_stats ADD COLUMN {col_name} {col_def}'))
                                logger.info(f"Added column '{col_name}' to 'player_stats' table.")
                            except Exception as e:
                                logger.error(f"Error adding column '{col_name}' to 'player_stats' table: {e}")

            conn.execute(sqlalchemy.text(f'''
                    CREATE TABLE IF NOT EXISTS coach_conversations (
                        conversation_id {session_id_type},
                        player_id INTEGER NOT NULL,
                        last_updated {timestamp_type} DEFAULT {default_timestamp},
                        FOREIGN KEY (player_id) REFERENCES players (player_id) ON DELETE CASCADE
                    )
            '''))

            conn.execute(sqlalchemy.text(f'''
                    CREATE TABLE IF NOT EXISTS duels (
                        duel_id {session_id_type},
                        creator_id INTEGER NOT NULL,
                        invited_player_id INTEGER NOT NULL,
                        status TEXT DEFAULT 'pending',
                        settings TEXT,
                        creator_submitted_session_id INTEGER,
                        invited_submitted_session_id INTEGER,
                        winner_id INTEGER,
                        created_at {timestamp_type} DEFAULT {default_timestamp},
                        FOREIGN KEY (creator_id) REFERENCES players (player_id) ON DELETE CASCADE,
                        FOREIGN KEY (invited_player_id) REFERENCES players (player_id) ON DELETE CASCADE,
                        FOREIGN KEY (creator_submitted_session_id) REFERENCES sessions (session_id),
                        FOREIGN KEY (invited_submitted_session_id) REFERENCES sessions (session_id),
                        FOREIGN KEY (winner_id) REFERENCES players (player_id)
                    )
            '''))

            if db_type == "sqlite":
                try:
                    duel_table_info = conn.execute(sqlalchemy.text("PRAGMA table_info(duels)")).mappings().fetchall()
                    duel_column_names = [col['name'] for col in duel_table_info]
                    duel_columns_to_add = {
                        "invitation_expiry_minutes": "INTEGER",
                        "session_duration_limit_minutes": "INTEGER",
                        "invitation_expires_at": "DATETIME"
                    }
                    for column, col_type in duel_columns_to_add.items():
                        if column not in duel_column_names:
                            conn.execute(sqlalchemy.text(f"ALTER TABLE duels ADD COLUMN {column} {col_type}"))
                            logger.info(f"Migration: Added column '{column}' to 'duels' table.")
                    if 'time_limit_minutes' in duel_column_names:
                        logger.info("Migration: Found obsolete 'time_limit_minutes' column in 'duels' table. Dropping it.")
                        conn.execute(sqlalchemy.text("ALTER TABLE duels DROP COLUMN time_limit_minutes"))
                        logger.info("Migration: Successfully dropped 'time_limit_minutes' column.")
                except Exception as e:
                    logger.warning(f"A non-critical error occurred during 'duels' table migration. This is often safe to ignore. Error: {e}")

            conn.execute(sqlalchemy.text(f'''
                    CREATE TABLE IF NOT EXISTS notifications (
                        id {session_id_type},
                        player_id INTEGER NOT NULL,
                        email_sent BOOLEAN DEFAULT FALSE,
                        FOREIGN KEY (player_id) REFERENCES players (player_id) ON DELETE CASCADE
                    )
            '''))

            if db_type == "sqlite":
                notification_columns_to_add = {
                    "email_sent": "BOOLEAN"
                }
                for column, col_type in notification_columns_to_add.items():
                    try:
                        conn.execute(sqlalchemy.text(f"ALTER TABLE notifications ADD COLUMN {column} {col_type}"))
                        logger.info(f"Added column '{column}' to 'notifications' table.")
                    except OperationalError as e:
                        if "duplicate column name" in str(e).lower():
                            logger.info(f"Column '{column}' already exists in 'notifications' table. Skipping.")
                        else:
                            logger.error(f"Error adding column '{column}' to 'notifications' table: {e}")

            conn.execute(sqlalchemy.text(f'''
                    CREATE TABLE IF NOT EXISTS fundraisers (
                        fundraiser_id {session_id_type},
                        creator_id INTEGER NOT NULL,
                        title TEXT NOT NULL,
                        description TEXT,
                        charity_name TEXT NOT NULL,
                        charity_wallet_address TEXT,
                        target_amount REAL,
                        current_amount REAL DEFAULT 0,
                        sat_per_putt INTEGER DEFAULT 100,
                        start_date {timestamp_type},
                        end_date {timestamp_type},
                        status TEXT DEFAULT 'active',
                        created_at {timestamp_type} DEFAULT {default_timestamp},
                        FOREIGN KEY (creator_id) REFERENCES players (player_id) ON DELETE CASCADE
                    )
            '''))

            conn.execute(sqlalchemy.text(f'''
                    CREATE TABLE IF NOT EXISTS pledges (
                        pledge_id {session_id_type},
                        fundraiser_id INTEGER NOT NULL,
                        pledger_id INTEGER NOT NULL,
                        amount_per_putt INTEGER NOT NULL,
                        max_amount REAL,
                        total_pledged REAL DEFAULT 0,
                        total_paid REAL DEFAULT 0,
                        status TEXT DEFAULT 'active',
                        created_at {timestamp_type} DEFAULT {default_timestamp},
                        FOREIGN KEY (fundraiser_id) REFERENCES fundraisers (fundraiser_id) ON DELETE CASCADE,
                        FOREIGN KEY (pledger_id) REFERENCES players (player_id) ON DELETE CASCADE
                    )
            '''))

            if db_type == "sqlite":
                fundraiser_columns_to_add = {
                    "last_notified_milestone": "INTEGER",
                    "conclusion_notification_sent": "BOOLEAN"
                }
                for column, col_type in fundraiser_columns_to_add.items():
                    try:
                        conn.execute(sqlalchemy.text(f"ALTER TABLE fundraisers ADD COLUMN {column} {col_type} DEFAULT 0"))
                        logger.info(f"Added column '{column}' to 'fundraisers' table.")
                    except OperationalError as e:
                        if "duplicate column name" in str(e).lower():
                            logger.info(f"Column '{column}' already exists in 'fundraisers' table. Skipping.")
                        else:
                            logger.error(f"Error adding column '{column}' to 'fundraisers' table: {e}")

            conn.execute(sqlalchemy.text(f'''
                    CREATE TABLE IF NOT EXISTS player_relationships (
                        follower_id INTEGER NOT NULL,
                        followed_id INTEGER NOT NULL,
                        created_at {timestamp_type} DEFAULT {default_timestamp},
                        PRIMARY KEY (follower_id, followed_id),
                        FOREIGN KEY (follower_id) REFERENCES players (player_id) ON DELETE CASCADE,
                        FOREIGN KEY (followed_id) REFERENCES players (player_id) ON DELETE CASCADE
                    )
            '''))

            # --- Create Default User Logic ---
            pop_user = conn.execute(
                sqlalchemy.text("SELECT player_id, subscription_status FROM players WHERE email = :email"),
                {"email": "pop@proofofputt.com"}
            ).mappings().first()

            if not pop_user:
                logger.info("Default user 'pop@proofofputt.com' not found. Creating...")
                password_hash = bcrypt.hashpw("passwordpop123".encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
                
                if db_type == "postgresql":
                    insert_sql = "INSERT INTO players (email, name, password_hash, timezone) VALUES (:email, :name, :password_hash, :timezone) RETURNING player_id"
                    result = conn.execute(sqlalchemy.text(insert_sql), {
                        "email": "pop@proofofputt.com",
                        "name": "POP",
                        "password_hash": password_hash,
                        "timezone": "UTC"
                    })
                    player_id = result.scalar()
                else:
                    insert_sql = "INSERT INTO players (email, name, password_hash, timezone) VALUES (:email, :name, :password_hash, :timezone)"
                    result = conn.execute(sqlalchemy.text(insert_sql), {
                        "email": "pop@proofofputt.com",
                        "name": "POP",
                        "password_hash": password_hash,
                        "timezone": "UTC"
                    })
                    player_id = result.lastrowid
                
                # Initialize player stats with zeros
                conn.execute(sqlalchemy.text('''
                    INSERT INTO player_stats (
                        player_id, total_makes, total_misses, total_putts, 
                        best_streak, fastest_21_makes, total_duration, last_updated
                    ) VALUES (
                        :player_id, 0, 0, 0, 0, 0, 0.0, :current_time
                    )
                '''), {
                    "player_id": player_id, 
                    "current_time": datetime.utcnow()
                })
                
                pop_user = {'player_id': player_id, 'subscription_status': 'free'}
                logger.info(f"Registered new default player 'POP' with ID {player_id}.")
# create_default_session_if_needed(player_id, conn) - Removed as requested

            else:
                logger.info(f"Default user {pop_user['player_id']} found. Ensuring password hash is bcrypt compatible.")
                hashed_password = bcrypt.hashpw("passwordpop123".encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
                conn.execute(sqlalchemy.text('''
                    UPDATE players SET password_hash = :password_hash
                    WHERE player_id = :player_id
                '''), {"password_hash": hashed_password, "player_id": pop_user['player_id']})
# create_default_session_if_needed(pop_user['player_id'], conn) - Removed as requested
            
            if pop_user and pop_user['subscription_status'] != 'active':
                logger.info(f"Upgrading default user {pop_user['player_id']} to 'active' subscription status.")
                conn.execute(sqlalchemy.text('''
                    UPDATE players SET subscription_status = 'active'
                    WHERE player_id = :player_id
                '''), {"player_id": pop_user['player_id']})

def register_player(email, password, name):
    """Registers a new player with a hashed password."""
    if not email or not password or not name:
        raise ValueError("Email, password, and name cannot be empty.")

    pool = get_db_connection()
    password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    db_type = pool.dialect.name

    with pool.connect() as conn:
        with conn.begin() as trans:
            try:
                insert_sql = "INSERT INTO players (email, name, password_hash, timezone) VALUES (LOWER(:email), :name, :password_hash, :timezone)"
                if db_type == "postgresql":
                    insert_sql += " RETURNING player_id"
                
                result = conn.execute(sqlalchemy.text(insert_sql), {"email": email, "name": name, "password_hash": password_hash, "timezone": "UTC"})
                
                player_id = result.scalar() if db_type == "postgresql" else result.lastrowid

                # Initialize player_stats with default zero values for proper career stats display
                conn.execute(sqlalchemy.text("""
                    INSERT INTO player_stats (
                        player_id, total_makes, total_misses, total_putts, best_streak, 
                        fastest_21_makes, total_duration, last_updated
                    ) VALUES (
                        :player_id, 0, 0, 0, 0, 0, 0.0, :current_time
                    )
                """), {
                    "player_id": player_id, 
                    "current_time": datetime.utcnow()
                })

                # Send welcome email
                subject = "Welcome to Proof of Putt!"
                html_content = f"""<h1>Welcome, {name}!</h1>
                    <p>Thank you for registering for Proof of Putt. We're excited to have you.</p>
                    <p>Log in now and start tracking your putting sessions!</p>"""
                send_email(email, subject, html_content)

                logger.info(f"Registered new player '{name}' with ID {player_id}.")
                return player_id, name
            except IntegrityError as e:
                raise ValueError("A player with this email already exists.")

def login_with_email_password(email, password):
    """Authenticates a player with email and password."""
    pool = get_db_connection()
    with pool.connect() as conn:
        result = conn.execute(
            sqlalchemy.text("SELECT player_id, name, email, password_hash, timezone, subscription_status FROM players WHERE LOWER(email) = LOWER(:email)"),
            {"email": email.lower()}
        ).mappings().first()

        if result and bcrypt.checkpw(password.encode('utf-8'), result['password_hash'].encode('utf-8')):
            player_id = result['player_id']
            stats = get_player_stats(player_id)
            sessions = get_sessions_for_player(player_id, limit=25)
            return player_id, result['name'], result['email'], stats, sessions, result['timezone'], result['subscription_status']
        
        return None, None, None, None, None, None, None

def _aggregate_session_makes(s_makes_by_cat, career_stats):
    """Helper to aggregate makes from a single session into career stats."""
    s_makes_overview_counts = {cat: 0 for cat in ["TOP", "RIGHT", "LOW", "LEFT"]}
    for cat, count in s_makes_by_cat.items():
        # Detailed aggregation
        if cat not in career_stats["makes_detailed"]:
            career_stats["makes_detailed"][cat] = {"high": 0, "sum": 0}
        career_stats["makes_detailed"][cat]["high"] = max(career_stats["makes_detailed"][cat]["high"], count)
        career_stats["makes_detailed"][cat]["sum"] += count
        
        # Tally for session overview
        if "TOP" in cat: s_makes_overview_counts["TOP"] += count
        if "RIGHT" in cat: s_makes_overview_counts["RIGHT"] += count
        if "LOW" in cat: s_makes_overview_counts["LOW"] += count
        if "LEFT" in cat: s_makes_overview_counts["LEFT"] += count
    
    # Update career overview with this session's totals
    for cat, count in s_makes_overview_counts.items():
        career_stats["makes_overview"][cat]["sum"] += count
        career_stats["makes_overview"][cat]["high"] = max(career_stats["makes_overview"][cat]["high"], count)

def _aggregate_session_misses(putt_list, career_stats):
    """Helper to aggregate detailed misses from a single session's putt list."""
    s_misses_detailed = {}
    for putt in [p for p in putt_list if p.get('Putt Classification') == 'MISS']:
        detail = putt.get('Putt Detailed Classification', 'UNKNOWN').replace('MISS - ', '')
        s_misses_detailed[detail] = s_misses_detailed.get(detail, 0) + 1
    
    for detail, count in s_misses_detailed.items():
        if detail not in career_stats["misses_detailed"]:
            career_stats["misses_detailed"][detail] = {"low": float('inf'), "high": 0, "sum": 0}
        career_stats["misses_detailed"][detail]["low"] = min(career_stats["misses_detailed"][detail]["low"], count)
        career_stats["misses_detailed"][detail]["high"] = max(career_stats["misses_detailed"][detail]["high"], count)
        career_stats["misses_detailed"][detail]["sum"] += count

def safe_divide(numerator, denominator, default=0):
    """Safely divide two numbers, returning default if denominator is 0 or None."""
    if not denominator or denominator == 0:
        return default
    try:
        result = numerator / denominator
        return result if not (result == float('inf') or result != result) else default  # Check for inf/NaN
    except (TypeError, ZeroDivisionError):
        return default

def safe_value(value, default=0):
    """Return a safe value, replacing None, inf, or NaN with default."""
    if value is None or value == float('inf') or (isinstance(value, float) and value != value):
        return default
    return value

def get_player_stats(player_id):
    """
    Aggregates and calculates comprehensive career statistics for a player.
    This function replaces the previous simpler version with improved error handling.
    """
    pool = get_db_connection()
    with pool.connect() as conn:
        player_info = get_player_info(player_id)
        if not player_info:
            return None

        # Fetch base stats from the pre-aggregated table
        base_stats_result = conn.execute(
            sqlalchemy.text("SELECT * FROM player_stats WHERE player_id = :id"),
            {"id": player_id}
        ).mappings().first()
        base_stats = dict(base_stats_result) if base_stats_result else {}

        sessions = get_sessions_for_player(player_id)
        
        career_stats = {
            "player_id": player_id,
            "player_name": player_info.get('name', 'Unknown Player'),
            "is_subscribed": player_info.get('subscription_status') == 'active',
            "high_makes": 0,
            "sum_makes": base_stats.get('total_makes', 0),
            "high_best_streak": base_stats.get('best_streak', 0),
            "low_fastest_21": base_stats.get('fastest_21_makes', 0),  # Default to 0 instead of None
            "high_ppm": 0.0,
            "avg_ppm": 0.0,
            "high_mpm": 0.0,
            "avg_mpm": 0.0,
            "high_most_in_60": 0,
            "high_duration": 0.0,
            "sum_duration": 0.0,
            "high_accuracy": 0.0,
            "avg_accuracy": 0.0,
            "consecutive": {str(c): {"high": 0, "sum": 0} for c in [3, 7, 10, 15, 21, 50, 100]},
            "makes_overview": {cat: {"high": 0, "sum": 0} for cat in ["TOP", "RIGHT", "LOW", "LEFT"]},
            "makes_detailed": {},
            "misses_overview": {cat: {"low": 0, "high": 0, "sum": 0} for cat in ["RETURN", "CATCH", "TIMEOUT"]},  # Initialize low to 0 instead of inf
            "misses_detailed": {},
        }

        total_duration_seconds = 0
        for session in sessions:
            s_makes = session.get('total_makes', 0) or 0
            s_misses = session.get('total_misses', 0) or 0
            duration = session.get('session_duration', 0) or 0

            career_stats["high_makes"] = max(career_stats["high_makes"], s_makes)
            career_stats["high_ppm"] = max(career_stats["high_ppm"], session.get('putts_per_minute', 0) or 0)
            career_stats["high_mpm"] = max(career_stats["high_mpm"], session.get('makes_per_minute', 0) or 0)
            career_stats["high_most_in_60"] = max(career_stats["high_most_in_60"], session.get('most_makes_in_60_seconds', 0) or 0)
            career_stats["high_duration"] = max(career_stats["high_duration"], duration)
            total_duration_seconds += duration

            if (s_makes + s_misses) > 0:
                s_accuracy = (s_makes / (s_makes + s_misses)) * 100
                career_stats["high_accuracy"] = max(career_stats["high_accuracy"], s_accuracy)

            if session.get('putt_list'):
                try:
                    putt_list = json.loads(session['putt_list'])
                    _aggregate_session_misses(putt_list, career_stats)
                except (json.JSONDecodeError, TypeError): pass

        career_stats["sum_duration"] = safe_value(total_duration_seconds)
        total_putts = safe_value(base_stats.get('total_putts', 0))
        total_makes = safe_value(base_stats.get('total_makes', 0))
        
        # Safe calculations with proper defaults
        total_duration_minutes = safe_divide(total_duration_seconds, 60.0)
        career_stats["avg_ppm"] = safe_divide(total_putts, total_duration_minutes)
        career_stats["avg_mpm"] = safe_divide(total_makes, total_duration_minutes)
        career_stats["avg_accuracy"] = safe_divide(total_makes, total_putts) * 100 if total_putts > 0 else 0
        
        # Ensure fastest_21 is properly handled (0 if None or inf, otherwise keep value)
        fastest_21 = base_stats.get('fastest_21_makes')
        career_stats["low_fastest_21"] = safe_value(fastest_21, 0)

        # Final cleanup for JSON compatibility
        for detail in career_stats.get("misses_detailed", {}).values():
            if detail["low"] == float('inf'):
                detail["low"] = 0  # Use 0 instead of None for new players
        for category in career_stats.get("misses_overview", {}).values():
            if category["low"] == float('inf'):
                category["low"] = 0  # Use 0 instead of None for new players

        return career_stats

def recalculate_player_stats(player_id):
    """
    Recalculates and updates player stats in the database, handling N/A and division by zero issues.
    This should be called to clean up any existing problematic data.
    """
    pool = get_db_connection()
    with pool.connect() as conn:
        # Get all sessions for the player
        sessions_result = conn.execute(
            sqlalchemy.text("""
                SELECT total_putts, total_makes, total_misses, best_streak, 
                       fastest_21_makes, session_duration, putt_list
                FROM sessions 
                WHERE player_id = :player_id 
                ORDER BY start_time
            """),
            {"player_id": player_id}
        ).mappings().fetchall()
        
        if not sessions_result:
            # No sessions - set all to zero
            conn.execute(
                sqlalchemy.text("""
                    UPDATE player_stats 
                    SET total_makes = 0, total_misses = 0, total_putts = 0,
                        best_streak = 0, fastest_21_makes = 0, total_duration = 0.0,
                        last_updated = :current_time
                    WHERE player_id = :player_id
                """),
                {"player_id": player_id, "current_time": datetime.utcnow()}
            )
            conn.commit()
            return
            
        # Calculate aggregated stats
        total_makes = 0
        total_misses = 0  
        total_putts = 0
        best_streak = 0
        total_duration = 0.0
        make_timestamps = []  # For fastest 21 calculation
        
        for session in sessions_result:
            total_makes += safe_value(session.get('total_makes', 0))
            total_misses += safe_value(session.get('total_misses', 0))
            total_putts += safe_value(session.get('total_putts', 0))
            best_streak = max(best_streak, safe_value(session.get('best_streak', 0)))
            total_duration += safe_value(session.get('session_duration', 0))
            
            # Extract make timestamps for fastest 21 calculation
            if session.get('putt_list'):
                try:
                    putt_list = json.loads(session['putt_list'])
                    for putt in putt_list:
                        if putt.get('Putt Classification') == 'MAKE':
                            timestamp = safe_value(putt.get('current_frame_time', 0))
                            if timestamp > 0:
                                make_timestamps.append(timestamp)
                except (json.JSONDecodeError, TypeError, KeyError):
                    continue
        
        # Calculate fastest 21 makes
        fastest_21 = 0
        if len(make_timestamps) >= 21:
            make_timestamps.sort()
            fastest_21_times = []
            for i in range(len(make_timestamps) - 20):
                time_span = make_timestamps[i + 20] - make_timestamps[i]
                if time_span > 0:
                    fastest_21_times.append(time_span)
            fastest_21 = min(fastest_21_times) if fastest_21_times else 0
        
        # Update player stats with safe values
        conn.execute(
            sqlalchemy.text("""
                UPDATE player_stats 
                SET total_makes = :total_makes, 
                    total_misses = :total_misses, 
                    total_putts = :total_putts,
                    best_streak = :best_streak, 
                    fastest_21_makes = :fastest_21, 
                    total_duration = :total_duration,
                    last_updated = :current_time
                WHERE player_id = :player_id
            """),
            {
                "player_id": player_id,
                "total_makes": total_makes,
                "total_misses": total_misses, 
                "total_putts": total_putts,
                "best_streak": best_streak,
                "fastest_21": fastest_21,
                "total_duration": total_duration,
                "current_time": datetime.utcnow()
            }
        )
        conn.commit()
        logger.info(f"Recalculated stats for player {player_id}: {total_makes} makes, {total_putts} putts, fastest_21: {fastest_21}")
        
        return {
            "total_makes": total_makes,
            "total_putts": total_putts, 
            "fastest_21": fastest_21,
            "total_duration": total_duration
        }

def get_sessions_for_player(player_id, limit=25, offset=0):
    pool = get_db_connection()
    with pool.connect() as conn:
        player_info = conn.execute(
            sqlalchemy.text("SELECT subscription_status FROM players WHERE player_id = :player_id"),
            {"player_id": player_id}
        ).mappings().first()

        is_subscribed = player_info and player_info['subscription_status'] == 'active'

        result = conn.execute(
            sqlalchemy.text("""SELECT session_id, start_time, end_time, status, total_putts, total_makes, 
                                 total_misses, best_streak, fastest_21_makes, putts_per_minute, 
                                 makes_per_minute, most_makes_in_60_seconds, session_duration, 
                                 putt_list, makes_by_category, misses_by_category 
                          FROM sessions 
                          WHERE player_id = :player_id 
                          ORDER BY start_time DESC 
                          LIMIT :limit OFFSET :offset"""),
            {"player_id": player_id, "limit": limit, "offset": offset}
        ).mappings().fetchall()

        sessions_data = []
        for i, row in enumerate(result):
            session_dict = dict(row)
            # Convert datetime objects to ISO 8601 strings, handle None
            if session_dict.get('start_time'):
                session_dict['start_time'] = session_dict['start_time'].isoformat()
            if session_dict.get('end_time'):
                session_dict['end_time'] = session_dict['end_time'].isoformat()

            # Apply free user limitation
            if not is_subscribed and i > 0: # 0 is the most recent session
                session_dict['putt_list'] = None
                session_dict['makes_by_category'] = None
                session_dict['misses_by_category'] = None
                session_dict['fastest_21_makes'] = None
                session_dict['is_locked'] = True # Add a flag for the frontend

            sessions_data.append(session_dict)
        return sessions_data

def get_player_session_count(player_id):
    """Get the total count of sessions for a player."""
    pool = get_db_connection()
    with pool.connect() as conn:
        result = conn.execute(
            sqlalchemy.text("SELECT COUNT(*) as total FROM sessions WHERE player_id = :player_id"),
            {"player_id": player_id}
        ).fetchone()
        return result[0] if result else 0

def get_leagues_for_player(player_id):
    logger.info(f"Fetching leagues for player_id: {player_id}")
    pool = get_db_connection()
    with pool.connect() as conn:
        # Fetch leagues where the player is a member
        my_leagues_result = conn.execute(
            sqlalchemy.text("""
                SELECT l.league_id, l.name, l.description, l.privacy_type, l.status, l.start_time
                FROM leagues l
                JOIN league_members lm ON l.league_id = lm.league_id
                WHERE lm.player_id = :player_id
                ORDER BY l.start_time DESC
            """),
            {"player_id": player_id}
        ).mappings().fetchall()
        
        my_leagues = []
        for league_row in my_leagues_result:
            league = dict(league_row)
            
            # Convert start_time to ISO format
            if league.get('start_time'):
                league['start_time'] = league['start_time'].isoformat()

            # Fetch rounds for this specific league
            rounds_result = conn.execute(
                sqlalchemy.text("""
                    SELECT r.round_id, r.round_number, r.status, r.start_time, r.end_time,
                           (SELECT COUNT(*) FROM league_round_submissions lrs
                            WHERE lrs.round_id = r.round_id AND lrs.player_id = :player_id) > 0 AS has_submitted
                    FROM league_rounds r
                    WHERE r.league_id = :league_id
                    ORDER BY r.round_number ASC
                """),
                {"league_id": league['league_id'], "player_id": player_id}
            ).mappings().fetchall()
            
            league['rounds'] = []
            for round_row in rounds_result:
                round_dict = dict(round_row)
                if round_dict.get('start_time'):
                    round_dict['start_time'] = round_dict['start_time'].isoformat()
                if round_dict.get('end_time'):
                    round_dict['end_time'] = round_dict['end_time'].isoformat()
                league['rounds'].append(round_dict)

            # Fetch member count
            member_count_result = conn.execute(
                sqlalchemy.text("SELECT COUNT(*) FROM league_members WHERE league_id = :league_id"),
                {"league_id": league['league_id']}
            ).scalar()
            league['member_count'] = member_count_result or 0

            my_leagues.append(league)

        logger.info(f"Found and processed {len(my_leagues)} leagues for player {player_id}.")

        # Fetch public leagues that the player is NOT already a member of
        public_leagues_result = conn.execute(
            sqlalchemy.text("""
                SELECT l.league_id, l.name, l.description, l.privacy_type, l.status, COUNT(lm.player_id) AS member_count
                FROM leagues l
                LEFT JOIN league_members lm ON l.league_id = lm.league_id
                WHERE l.privacy_type = 'public'
                AND l.league_id NOT IN (SELECT league_id FROM league_members WHERE player_id = :player_id)
                GROUP BY l.league_id, l.name, l.description, l.privacy_type, l.status
                ORDER BY l.created_at DESC
            """),
            {"player_id": player_id}
        ).mappings().fetchall()
        public_leagues = [dict(row) for row in public_leagues_result]
        logger.info(f"Found {len(public_leagues)} public leagues not joined by player {player_id}.")

        # TODO: Fetch pending invites (requires a new table/column for invites)
        pending_invites = [] # Placeholder for now

        return {
            "my_leagues": my_leagues,
            "public_leagues": public_leagues,
            "pending_invites": pending_invites
        }

def get_duels_for_player(player_id):
    pool = get_db_connection()
    with pool.connect() as conn:
        # The main query to get all duels for a player, now joining sessions and players
        result = conn.execute(
            sqlalchemy.text("""
                SELECT 
                    d.duel_id, d.creator_id, d.invited_player_id, d.status, d.winner_id,
                    d.created_at, d.invitation_expires_at, d.session_duration_limit_minutes,
                    p_creator.name AS creator_name,
                    p_invited.name AS invited_name,
                    s_creator.total_makes AS creator_makes,
                    s_invited.total_makes AS invited_makes,
                    d.creator_submitted_session_id,
                    d.invited_player_submitted_session_id
                FROM duels d
                JOIN players p_creator ON d.creator_id = p_creator.player_id
                JOIN players p_invited ON d.invited_player_id = p_invited.player_id
                LEFT JOIN sessions s_creator ON d.creator_submitted_session_id = s_creator.session_id
                LEFT JOIN sessions s_invited ON d.invited_player_submitted_session_id = s_invited.session_id
                WHERE d.creator_id = :player_id OR d.invited_player_id = :player_id
                ORDER BY d.created_at DESC
            """),
            {"player_id": player_id}
        ).mappings().fetchall()

        duels_data = []
        for row in result:
            duel_dict = dict(row)
            # Convert all datetime objects to ISO 8601 strings
            for key, value in duel_dict.items():
                if isinstance(value, datetime):
                    duel_dict[key] = value.isoformat()
            duels_data.append(duel_dict)
            
        return duels_data

def search_players(search_term, current_player_id):
    pool = get_db_connection()
    db_type = pool.dialect.name
    like_operator = "ILIKE" if db_type == "postgresql" else "LIKE"

    with pool.connect() as conn:
        result = conn.execute(
            sqlalchemy.text(f"""
                SELECT player_id, name, email
                FROM players_view
                WHERE (name {like_operator} :term OR email {like_operator} :term)
                AND player_id != :current_player_id
                LIMIT 10
            """),
            {"term": f"%{search_term}%", "current_player_id": current_player_id}
        ).mappings().fetchall()
        return [dict(row) for row in result]

def create_in_app_notification(player_id, notification_type, message, details=None, link_path=None):
    """Creates a new in-app notification for a player."""
    pool = get_db_connection()
    with pool.connect() as conn:
        with conn.begin():
            conn.execute(
                sqlalchemy.text("""
                    INSERT INTO notifications (player_id, type, message, details, link_path)
                    VALUES (:player_id, :type, :message, :details, :link_path)
                """),
                {
                    "player_id": player_id,
                    "type": notification_type,
                    "message": message,
                    "details": json.dumps(details) if details else None,
                    "link_path": link_path
                }
            )
    logger.info(f"Created in-app notification for player {player_id} of type {notification_type}.")

def get_unread_notification_count(player_id):
    pool = get_db_connection()
    with pool.connect() as conn:
        count = conn.execute(
            sqlalchemy.text(""" 
                SELECT COUNT(*) FROM notifications
                WHERE player_id = :player_id AND read_status = FALSE
            """),
            {"player_id": player_id}
        ).scalar_one_or_none()
        return count or 0

def get_notifications_for_player(player_id, limit=20, offset=0):
    """Retrieves notifications for a specific player, sorted by most recent."""
    pool = get_db_connection()
    with pool.connect() as conn:
        result = conn.execute(
            sqlalchemy.text("""
                SELECT id, type, message, details, read_status, created_at, link_path
                FROM notifications
                WHERE player_id = :player_id
                ORDER BY created_at DESC
                LIMIT :limit OFFSET :offset
            """),
            {"player_id": player_id, "limit": limit, "offset": offset}
        ).mappings().fetchall()

        notifications = []
        for row in result:
            notification = dict(row)
            if notification.get('created_at'):
                notification['created_at'] = notification['created_at'].isoformat()
            notifications.append(notification)
        return notifications

def get_coach_conversations(player_id):
    pool = get_db_connection()
    with pool.connect() as conn:
        result = conn.execute(
            sqlalchemy.text("""
                SELECT conversation_id, title, last_updated
                FROM coach_conversations
                WHERE player_id = :player_id
                ORDER BY last_updated DESC
            """),
            {"player_id": player_id}
        ).mappings().fetchall()

        conversations_data = []
        for row in result:
            convo_dict = dict(row)
            if convo_dict.get('last_updated'):
                convo_dict['last_updated'] = convo_dict['last_updated'].isoformat()
            conversations_data.append(convo_dict)
        return conversations_data

def get_coach_conversation_details(conversation_id, player_id):
    pool = get_db_connection()
    with pool.connect() as conn:
        result = conn.execute(
            sqlalchemy.text("""
                SELECT *
                FROM coach_conversations
                WHERE conversation_id = :conversation_id AND player_id = :player_id
            """),
            {"conversation_id": conversation_id, "player_id": player_id}
        ).mappings().first()

        if not result:
            return None

        convo_dict = dict(result)
        if convo_dict.get('history_json'):
            convo_dict['history'] = json.loads(convo_dict['history_json'])
            del convo_dict['history_json']

        # Convert datetimes
        for key, value in convo_dict.items():
            if isinstance(value, datetime):
                convo_dict[key] = value.isoformat()

        return convo_dict

def get_player_info(player_id):
    pool = get_db_connection()
    with pool.connect() as conn:
        result = conn.execute(
            sqlalchemy.text("SELECT player_id, email, name, subscription_status, timezone FROM players WHERE player_id = :player_id"),
            {"player_id": player_id}
        ).mappings().first()
        if result:
            return dict(result)
        return None

def get_notification_preferences(player_id):
    """Retrieves notification preferences for a specific player."""
    pool = get_db_connection()
    with pool.connect() as conn:
        result = conn.execute(
            sqlalchemy.text("SELECT notification_preferences FROM players WHERE player_id = :player_id"),
            {"player_id": player_id}
        ).scalar_one_or_none()
    # The result could be a JSON string or None. The service layer will handle parsing.
    return result

def update_notification_preferences(player_id, preferences):
    """Updates notification preferences (as a JSON string) for a specific player."""
    pool = get_db_connection()
    with pool.connect() as conn:
        with conn.begin():
            conn.execute(
                sqlalchemy.text("""
                    UPDATE players
                    SET notification_preferences = :preferences
                    WHERE player_id = :player_id
                """),
                {"player_id": player_id, "preferences": json.dumps(preferences)}
            )
    logger.info(f"Updated notification preferences for player {player_id}.")

def update_player_profile(player_id, updates):
    """Updates player profile information for a specific player."""
    pool = get_db_connection()
    with pool.connect() as conn:
        with conn.begin():
            # Construct the SET clause dynamically based on the updates dictionary
            set_clauses = []
            params = {"player_id": player_id}
            for key, value in updates.items():
                if key in ["name", "email", "timezone", "x_url", "tiktok_url", "website_url"]:
                    set_clauses.append(f"{key} = :{key}")
                    params[key] = value
                # Add other fields as needed

            if not set_clauses:
                logger.warning(f"No valid fields to update for player {player_id}.")
                return False

            update_sql = sqlalchemy.text(f"UPDATE players SET {', '.join(set_clauses)} WHERE player_id = :player_id")
            conn.execute(update_sql, params)
    logger.info(f"Updated profile for player {player_id} with updates: {updates}.")
    return True

def get_last_conversation_time(player_id):
    # Placeholder: In a real application, query your coach_conversations table
    # to get the last conversation time for the player.
    # Return a datetime object or None if no conversation exists.
    return None

def create_conversation(player_id, title, history):
    # Placeholder: In a real application, insert a new conversation into
    # your coach_conversations table and return the new conversation_id.
    # For now, return a dummy ID.
    logger.info(f"Placeholder: Creating conversation for player {player_id} with title '{title}'")
    return 999 # Dummy conversation ID

def save_calibration_data(player_id, calibration_data):
    """Saves calibration data (as a JSON string) for a specific player."""
    pool = get_db_connection()
    with pool.connect() as conn:
        with conn.begin():
            conn.execute(
                sqlalchemy.text("""
                    UPDATE players
                    SET calibration_data = :calibration_data
                    WHERE player_id = :player_id
                """),
                {"player_id": player_id, "calibration_data": json.dumps(calibration_data)}
            )
    logger.info(f"Saved calibration data for player {player_id}.")

def get_calibration_data(player_id):
    """Retrieves calibration data for a specific player."""
    pool = get_db_connection()
    with pool.connect() as conn:
        result = conn.execute(
            sqlalchemy.text("SELECT calibration_data FROM players WHERE player_id = :player_id"),
            {"player_id": player_id}
        ).scalar_one_or_none()

    if result:
        logger.info(f"Retrieved calibration data for player {player_id}.")
        return json.loads(result)
    logger.warning(f"No calibration data found for player {player_id}.")
    return None

def save_session(session_data):
    """Saves a completed session and updates player career stats."""
    pool = get_db_connection()
    with pool.connect() as conn:
        with conn.begin() as trans:
            try:
                # Insert the session data
                conn.execute(
                    sqlalchemy.text("""
                        INSERT INTO sessions (
                            player_id, start_time, end_time, status, total_putts, total_makes,
                            total_misses, best_streak, fastest_21_makes, putts_per_minute,
                            makes_per_minute, most_makes_in_60_seconds, session_duration,
                            putt_list, makes_by_category, misses_by_category
                        ) VALUES (
                            :player_id, :start_time, :end_time, :status, :total_putts, :total_makes,
                            :total_misses, :best_streak, :fastest_21_makes, :putts_per_minute,
                            :makes_per_minute, :most_makes_in_60_seconds, :session_duration,
                            :putt_list, :makes_by_category, :misses_by_category
                        )
                    """),
                    session_data
                )
                
                player_id = session_data.get('player_id')
                if player_id:
                    recalculate_player_stats(player_id, conn)
                
                logger.info(f"Saved new session and updated stats for player {player_id}.")
            except Exception as e:
                logger.error(f"Error saving session for player {session_data.get('player_id')}: {e}", exc_info=True)
                trans.rollback()
                raise

def create_league(creator_id, name, description, privacy_type, settings, start_time_str):
    """Creates a new league, adds the creator as the first member, and generates rounds."""
    pool = get_db_connection()
    db_type = pool.dialect.name

    num_rounds = settings.get('num_rounds', 4)
    round_duration_hours = settings.get('round_duration_hours', 168)

    with pool.connect() as conn:
        with conn.begin() as trans:
            try:
                # Get player's timezone
                player_info = get_player_info(creator_id)
                player_timezone_str = player_info.get('timezone', 'UTC') if player_info else 'UTC'
                
                try:
                    player_timezone = pytz.timezone(player_timezone_str)
                except pytz.UnknownTimeZoneError:
                    logger.warning(f"Unknown timezone {player_timezone_str} for player {creator_id}. Defaulting to UTC.")
                    player_timezone = pytz.utc

                # Convert naive start_time_str to timezone-aware datetime in player's timezone
                naive_start_time = datetime.fromisoformat(start_time_str)
                localized_start_time = player_timezone.localize(naive_start_time)
                
                # Convert to UTC for storage
                start_time_utc = localized_start_time.astimezone(pytz.utc)

                insert_league_sql = """
                    INSERT INTO leagues (creator_id, name, description, privacy_type, settings, start_time)
                    VALUES (:creator_id, :name, :description, :privacy_type, :settings, :start_time)
                """
                if db_type == "postgresql":
                    insert_league_sql += " RETURNING league_id"

                result = conn.execute(
                    sqlalchemy.text(insert_league_sql),
                    {
                        "creator_id": creator_id,
                        "name": name,
                        "description": description,
                        "privacy_type": privacy_type,
                        "settings": json.dumps(settings),
                        "start_time": start_time_utc # Store UTC time
                    }
                )

                league_id = result.scalar() if db_type == "postgresql" else result.lastrowid
                if not league_id:
                    raise Exception("Failed to retrieve new league_id.")

                # Add the creator as the first member of the league
                conn.execute(
                    sqlalchemy.text("""
                        INSERT INTO league_members (league_id, player_id, status)
                        VALUES (:league_id, :player_id, 'active')
                    """),
                    {"league_id": league_id, "player_id": creator_id}
                )
                logger.info(f"Created new league '{name}' with ID {league_id} by player {creator_id}. Adding creator to league_members.")

                # Generate and insert rounds
                current_round_start_time_utc = start_time_utc
                for i in range(1, num_rounds + 1):
                    round_end_time_utc = current_round_start_time_utc + timedelta(hours=round_duration_hours)
                    conn.execute(
                        sqlalchemy.text("""
                            INSERT INTO league_rounds (league_id, round_number, status, start_time, end_time)
                            VALUES (:league_id, :round_number, :status, :start_time, :end_time)
                        """),
                        {
                            "league_id": league_id,
                            "round_number": i,
                            "status": 'scheduled',
                            "start_time": current_round_start_time_utc,
                            "end_time": round_end_time_utc
                        }
                    )
                    current_round_start_time_utc = round_end_time_utc # Next round starts when this one ends
                logger.info(f"Generated {num_rounds} rounds for league {league_id}. Settings: {settings}")
                
                return league_id
            except Exception as e:
                logger.error(f"Error creating league: {e}", exc_info=True)
                
                raise

def start_pending_league_rounds():
    """
    Updates the status of league rounds from 'scheduled' to 'active' if their start time has passed.
    """
    pool = get_db_connection()
    with pool.connect() as conn:
        with conn.begin():
            current_time_utc = datetime.utcnow().replace(tzinfo=pytz.utc) # Ensure current time is timezone-aware UTC
            logger.info(f"Scheduler: Checking for pending league rounds at {current_time_utc.isoformat()}")
            result = conn.execute(
                sqlalchemy.text("""
                    UPDATE league_rounds
                    SET status = 'active'
                    WHERE status = 'scheduled' AND start_time <= :current_time
                    RETURNING round_id, league_id, start_time
                """),
                {"current_time": current_time_utc}
            )
            updated_rounds = result.fetchall()
            if updated_rounds:
                for round_id, league_id, start_time_db in updated_rounds:
                    logger.info(f"League round {round_id} for league {league_id} (starts: {start_time_db.isoformat()}) changed to 'active'.")
            else:
                logger.info("No pending league rounds to activate.")

def expire_pending_duels():
    """Placeholder for expiring pending duels."""
    logger.info("Executing expire_pending_duels (placeholder).")

def expire_active_duels():
    """Placeholder for expiring active duels."""
    logger.info("Executing expire_active_duels (placeholder).")

def send_league_reminders():
    """Placeholder for sending league reminders."""
    logger.info("Executing send_league_reminders (placeholder).")

def process_final_league_results():
    """Placeholder for processing final league results."""
    logger.info("Executing process_final_league_results (placeholder).")

def send_fundraiser_reminders():
    """Placeholder for sending fundraiser reminders."""
    logger.info("Executing send_fundraiser_reminders (placeholder).")

def process_concluded_fundraisers():
    """Placeholder for processing concluded fundraisers."""
    logger.info("Executing process_concluded_fundraisers (placeholder).")

def get_league_details(league_id):
    """Retrieves comprehensive details for a single league, including its members, rounds, and submissions."""
    pool = get_db_connection()
    with pool.connect() as conn:
        # First, get the main league info
        league_info = conn.execute(
            sqlalchemy.text("SELECT * FROM leagues WHERE league_id = :league_id"),
            {"league_id": league_id}
        ).mappings().first()

        if not league_info:
            logger.warning(f"League {league_id} not found.")
            return None

        league_details = dict(league_info)
        # The 'settings' column is a JSON string, so parse it
        if league_details.get('settings'):
            league_details['settings'] = json.loads(league_details['settings'])
        else:
            league_details['settings'] = {} # Ensure settings is always a dict

        # Next, get the list of members
        members = conn.execute(
            sqlalchemy.text("""
                SELECT p.player_id, p.name
                FROM league_members lm
                JOIN players p ON lm.player_id = p.player_id
                WHERE lm.league_id = :league_id
                ORDER BY p.name
            """),
            {"league_id": league_id}
        ).mappings().fetchall()
        league_details['members'] = [dict(member) for member in members]
        logger.info(f"Fetched {len(members)} members for league {league_id}.")

        # Then, get all rounds for the league
        rounds_result = conn.execute(
            sqlalchemy.text("""
                SELECT round_id, league_id, round_number, status, start_time, end_time
                FROM league_rounds
                WHERE league_id = :league_id
                ORDER BY round_number ASC
            """),
            {"league_id": league_id}
        ).mappings().fetchall()

        rounds_data = []
        for r_row in rounds_result:
            round_dict = dict(r_row)
            # Convert datetimes
            if round_dict.get('start_time'):
                round_dict['start_time'] = round_dict['start_time'].isoformat()
            if round_dict.get('end_time'):
                round_dict['end_time'] = round_dict['end_time'].isoformat()

            # Get submissions for each round
            submissions_result = conn.execute(
                sqlalchemy.text("""
                    SELECT
                        lrs.submission_id, lrs.player_id, lrs.session_id, lrs.points_awarded,
                        s.total_makes AS score, p.name AS player_name
                    FROM league_round_submissions lrs
                    JOIN sessions s ON lrs.session_id = s.session_id
                    JOIN players p ON lrs.player_id = p.player_id
                    WHERE lrs.round_id = :round_id
                """),
                {"round_id": round_dict['round_id']}
            ).mappings().fetchall()
            round_dict['submissions'] = [dict(sub) for sub in submissions_result]
            rounds_data.append(round_dict)
        
        league_details['rounds'] = rounds_data
        logger.info(f"Fetched {len(rounds_data)} rounds and their submissions for league {league_id}.")

        return league_details

def join_league(league_id, player_id):
    """Allows a player to join a public league."""
    pool = get_db_connection()
    with pool.connect() as conn:
        with conn.begin() as trans:
            try:
                # First, check if the league is public
                league = conn.execute(
                    sqlalchemy.text("SELECT privacy_type FROM leagues WHERE league_id = :league_id"),
                    {"league_id": league_id}
                ).mappings().first()

                if not league:
                    raise ValueError("League not found.")
                
                if league['privacy_type'] != 'public':
                    raise ValueError("This league is private and requires an invitation to join.")

                # Attempt to add the player to the league
                conn.execute(
                    sqlalchemy.text("""
                        INSERT INTO league_members (league_id, player_id, status)
                        VALUES (:league_id, :player_id, 'active')
                    """),
                    {"league_id": league_id, "player_id": player_id}
                )
                logger.info(f"Player {player_id} successfully joined league {league_id}.")
                
                return {"success": True, "message": "Successfully joined league."}
            except IntegrityError:
                # This happens if the UNIQUE constraint on (league_id, player_id) fails
                
                logger.warning(f"Player {player_id} attempted to join league {league_id} which they are already a member of.")
                raise ValueError("You are already a member of this league.")
            except ValueError as ve:
                
                raise ve # Re-raise the specific value error for the API to catch
            except Exception as e:
                
                logger.error(f"Error in join_league for player {player_id} and league {league_id}: {e}", exc_info=True)
                raise Exception("An unexpected error occurred while trying to join the league.")

def create_duel(creator_id, invited_player_id, settings):
    """Creates a new duel invitation."""
    pool = get_db_connection()
    db_type = pool.dialect.name

    session_duration = settings.get('session_duration_limit_minutes', 15) # Default to 15 mins
    invitation_expiry_minutes = settings.get('invitation_expiry_minutes', 72 * 60) # Default to 72 hours

    invitation_expires_at = datetime.utcnow() + timedelta(minutes=invitation_expiry_minutes)

    with pool.connect() as conn:
        with conn.begin() as trans:
            try:
                insert_sql = """
                    INSERT INTO duels (creator_id, invited_player_id, status, session_duration_limit_minutes, invitation_expiry_minutes, invitation_expires_at)
                    VALUES (:creator_id, :invited_player_id, 'pending', :session_duration, :invitation_expiry_minutes, :invitation_expires_at)
                """
                if db_type == "postgresql":
                    insert_sql += " RETURNING duel_id"

                result = conn.execute(
                    sqlalchemy.text(insert_sql),
                    {
                        "creator_id": creator_id,
                        "invited_player_id": invited_player_id,
                        "session_duration": session_duration,
                        "invitation_expiry_minutes": invitation_expiry_minutes,
                        "invitation_expires_at": invitation_expires_at
                    }
                )

                duel_id = result.scalar() if db_type == "postgresql" else result.lastrowid
                if not duel_id:
                    raise Exception("Failed to retrieve new duel_id.")

                logger.info(f"Player {creator_id} created new duel {duel_id} inviting player {invited_player_id}.")
                
                return duel_id
            except Exception as e:
                logger.error(f"Error creating duel: {e}", exc_info=True)
                
                raise



def submit_session_to_duel(duel_id, player_id, session_id):
    """Submits a player's session to an active duel and determines a winner if applicable."""
    pool = get_db_connection()
    with pool.connect() as conn:
        with conn.begin() as trans:
            duel = conn.execute(
                sqlalchemy.text("SELECT creator_id, invited_player_id, status FROM duels WHERE duel_id = :duel_id"),
                {"duel_id": duel_id}
            ).mappings().first()

            if not duel:
                raise ValueError("Duel not found.")
            if duel['status'] != 'active':
                raise ValueError("This duel is not active.")

            update_column = None
            if player_id == duel['creator_id']:
                update_column = "creator_submitted_session_id"
            elif player_id == duel['invited_player_id']:
                update_column = "invited_player_submitted_session_id"
            else:
                raise ValueError("You are not a participant in this duel.")

            # Update the session ID for the correct player
            conn.execute(
                sqlalchemy.text(f"UPDATE duels SET {update_column} = :session_id WHERE duel_id = :duel_id"),
                {"session_id": session_id, "duel_id": duel_id}
            )
            logger.info(f"Player {player_id} submitted session {session_id} to duel {duel_id}.")

            # Check if both players have submitted
            updated_duel = conn.execute(
                sqlalchemy.text("SELECT creator_submitted_session_id, invited_player_submitted_session_id FROM duels WHERE duel_id = :duel_id"),
                {"duel_id": duel_id}
            ).mappings().first()

            if updated_duel['creator_submitted_session_id'] and updated_duel['invited_player_submitted_session_id']:
                _determine_duel_winner(duel_id, conn)
            
            
            return {"success": True, "message": "Session submitted successfully."}



def _determine_duel_winner(duel_id, conn):
    """
    Determines the winner of a duel after both players have submitted.
    This function expects to be called within an existing transaction.
    """
    # Get the duel and session IDs
    duel = conn.execute(
        sqlalchemy.text("SELECT creator_id, invited_player_id, creator_submitted_session_id, invited_player_submitted_session_id FROM duels WHERE duel_id = :duel_id"),
        {"duel_id": duel_id}
    ).mappings().first()

    if not duel or not duel['creator_submitted_session_id'] or not duel['invited_player_submitted_session_id']:
        return

    # Get scores for both sessions
    creator_session = conn.execute(
        sqlalchemy.text("SELECT total_makes FROM sessions WHERE session_id = :session_id"),
        {"session_id": duel['creator_submitted_session_id']}
    ).mappings().first()

    invited_session = conn.execute(
        sqlalchemy.text("SELECT total_makes FROM sessions WHERE session_id = :session_id"),
        {"session_id": duel['invited_player_submitted_session_id']}
    ).mappings().first()

    winner_id = None
    # Simple logic: most makes wins. Ties go to the creator for now.
    if creator_session['total_makes'] >= invited_session['total_makes']:
        winner_id = duel['creator_id']
    else:
        winner_id = duel['invited_player_id']
    
    # Update the duel with the winner and completed status
    conn.execute(
        sqlalchemy.text("UPDATE duels SET status = 'completed', winner_id = :winner_id WHERE duel_id = :duel_id"),
        {"winner_id": winner_id, "duel_id": duel_id}
    )
    logger.info(f"Duel {duel_id} completed. Winner is player {winner_id}.")
    # TODO: Create notifications for both players about the result.

def get_all_time_leaderboards(limit=10):
    """Retrieves a dictionary of all-time leaderboards for various metrics."""
    pool = get_db_connection()
    leaderboards = {}
    with pool.connect() as conn:
        # Top Makes in a Session
        leaderboards['top_makes'] = [
            dict(row) for row in conn.execute(
                sqlalchemy.text("""
                    SELECT s.total_makes, p.name, s.start_time
                    FROM sessions s JOIN players p ON s.player_id = p.player_id
                    WHERE s.total_makes > 0
                    ORDER BY s.total_makes DESC, s.start_time DESC
                    LIMIT :limit
                """),
                {"limit": limit}
            ).mappings().fetchall()
        ]

        # Top Streaks
        leaderboards['top_streaks'] = [
            dict(row) for row in conn.execute(
                sqlalchemy.text("""
                    SELECT s.best_streak, p.name, s.start_time
                    FROM sessions s JOIN players p ON s.player_id = p.player_id
                    WHERE s.best_streak > 0
                    ORDER BY s.best_streak DESC, s.start_time DESC
                    LIMIT :limit
                """),
                {"limit": limit}
            ).mappings().fetchall()
        ]

        # Top Makes per Minute
        leaderboards['top_makes_per_minute'] = [
            dict(row) for row in conn.execute(
                sqlalchemy.text("""
                    SELECT s.makes_per_minute, p.name, s.start_time
                    FROM sessions s JOIN players p ON s.player_id = p.player_id
                    WHERE s.makes_per_minute > 0
                    ORDER BY s.makes_per_minute DESC, s.start_time DESC
                    LIMIT :limit
                """),
                {"limit": limit}
            ).mappings().fetchall()
        ]

        # Fastest 21 Makes
        leaderboards['fastest_21'] = [
            dict(row) for row in conn.execute(
                sqlalchemy.text("""
                    SELECT s.fastest_21_makes, p.name, s.start_time
                    FROM sessions s JOIN players p ON s.player_id = p.player_id
                    WHERE s.fastest_21_makes > 0
                    ORDER BY s.fastest_21_makes ASC, s.start_time DESC
                    LIMIT :limit
                """),
                {"limit": limit}
            ).mappings().fetchall()
        ]

    return leaderboards

def get_player_vs_player_duels(player1_id, player2_id):
    """Retrieves the history of duels between two specific players."""
    pool = get_db_connection()
    with pool.connect() as conn:
        # Duels where player1 is creator and player2 is invited, OR vice-versa
        result = conn.execute(
            sqlalchemy.text("""
                SELECT
                    d.duel_id,
                    d.creator_id,
                    d.invited_player_id,
                    d.status,
                    d.winner_id,
                    d.created_at,
                    s_creator.total_makes AS creator_makes,
                    s_invited.total_makes AS invited_makes,
                    p_creator.name AS creator_name,
                    p_invited.name AS invited_name
                FROM duels d
                LEFT JOIN sessions s_creator ON d.creator_submitted_session_id = s_creator.session_id
                LEFT JOIN sessions s_invited ON d.invited_player_submitted_session_id = s_invited.session_id
                JOIN players p_creator ON d.creator_id = p_creator.player_id
                JOIN players p_invited ON d.invited_player_id = p_invited.player_id
                WHERE (d.creator_id = :player1_id AND d.invited_player_id = :player2_id)
                   OR (d.creator_id = :player2_id AND d.invited_player_id = :player1_id)
                ORDER BY d.created_at DESC
            """),
            {"player1_id": player1_id, "player2_id": player2_id}
        ).mappings().fetchall()

        duels_history = []
        for row in result:
            duel_dict = dict(row)
            # Convert datetimes
            if duel_dict.get('created_at'):
                duel_dict['created_at'] = duel_dict['created_at'].isoformat()
            duels_history.append(duel_dict)
        return duels_history

def get_player_vs_player_leaderboard(player1_id, player2_id):
    """Calculates the head-to-head win/loss record between two players."""
    pool = get_db_connection()
    with pool.connect() as conn:
        # Count wins for player1 against player2
        player1_wins = conn.execute(
            sqlalchemy.text("""
                SELECT COUNT(*) FROM duels
                WHERE winner_id = :player1_id
                AND (
                    (creator_id = :player1_id AND invited_player_id = :player2_id) OR
                    (creator_id = :player2_id AND invited_player_id = :player1_id)
                )
                AND status = 'completed'
            """),
            {"player1_id": player1_id, "player2_id": player2_id}
        ).scalar_one_or_none() or 0

        # Count wins for player2 against player1
        player2_wins = conn.execute(
            sqlalchemy.text("""
                SELECT COUNT(*) FROM duels
                WHERE winner_id = :player2_id
                AND (
                    (creator_id = :player1_id AND invited_player_id = :player2_id) OR
                    (creator_id = :player2_id AND invited_player_id = :player1_id)
                )
                AND status = 'completed'
            """),
            {"player2_id": player2_id, "player1_id": player1_id}
        ).scalar_one_or_none() or 0

        # Count total completed duels between them
        total_completed_duels = conn.execute(
            sqlalchemy.text("""
                SELECT COUNT(*) FROM duels
                WHERE (
                    (creator_id = :player1_id AND invited_player_id = :player2_id) OR
                    (creator_id = :player2_id AND invited_player_id = :player1_id)
                )
                AND status = 'completed'
            """),
            {"player1_id": player1_id, "player2_id": player2_id}
        ).scalar_one_or_none() or 0

        # Get player names
        player1_name = conn.execute(sqlalchemy.text("SELECT name FROM players WHERE player_id = :player_id"), {"player_id": player1_id}).scalar_one_or_none()
        player2_name = conn.execute(sqlalchemy.text("SELECT name FROM players WHERE player_id = :player_id"), {"player_id": player2_id}).scalar_one_or_none()

        return {
            "player1_id": player1_id,
            "player1_name": player1_name,
            "player1_wins": player1_wins,
            "player2_id": player2_id,
            "player2_name": player2_name,
            "player2_wins": player2_wins,
            "total_completed_duels": total_completed_duels
        }

def get_league_leaderboard(league_id, limit=10):
    """
    Retrieves leaderboards for a specific league, considering only sessions
    submitted to that league's rounds.
    """
    pool = get_db_connection()
    leaderboards = {}
    with pool.connect() as conn:
        base_query = """
            FROM sessions s
            JOIN league_round_submissions lrs ON s.session_id = lrs.session_id
            JOIN league_rounds lr ON lrs.round_id = lr.round_id
            JOIN players p ON s.player_id = p.player_id
            WHERE lr.league_id = :league_id
        """

        # Top Makes
        leaderboards['top_makes'] = [dict(row) for row in conn.execute(
            sqlalchemy.text(f"SELECT s.total_makes, p.name, s.start_time {base_query} AND s.total_makes > 0 ORDER BY s.total_makes DESC LIMIT :limit"),
            {"league_id": league_id, "limit": limit}
        ).mappings().fetchall()]

        # Top Streaks
        leaderboards['top_streaks'] = [dict(row) for row in conn.execute(
            sqlalchemy.text(f"SELECT s.best_streak, p.name, s.start_time {base_query} AND s.best_streak > 0 ORDER BY s.best_streak DESC LIMIT :limit"),
            {"league_id": league_id, "limit": limit}
        ).mappings().fetchall()]

        # Top Makes per Minute
        leaderboards['top_makes_per_minute'] = [dict(row) for row in conn.execute(
            sqlalchemy.text(f"SELECT s.makes_per_minute, p.name, s.start_time {base_query} AND s.makes_per_minute > 0 ORDER BY s.makes_per_minute DESC LIMIT :limit"),
            {"league_id": league_id, "limit": limit}
        ).mappings().fetchall()]

        # Fastest 21 Makes
        leaderboards['fastest_21'] = [dict(row) for row in conn.execute(
            sqlalchemy.text(f"SELECT s.fastest_21_makes, p.name, s.start_time {base_query} AND s.fastest_21_makes > 0 ORDER BY s.fastest_21_makes ASC LIMIT :limit"),
            {"league_id": league_id, "limit": limit}
        ).mappings().fetchall()]
def update_league_settings(league_id, editor_id, new_settings):
    """Updates league settings, only if the editor is the creator and the league is in 'registering' state."""
    pool = get_db_connection()
    with pool.connect() as conn:
        with conn.begin() as trans:
            # Step 1: Verify permissions and status
            league = conn.execute(
                sqlalchemy.text("SELECT creator_id, status FROM leagues WHERE league_id = :id"),
                {"id": league_id}
            ).mappings().first()

            if not league:
                raise ValueError("League not found.")
            if league['creator_id'] != editor_id:
                raise ValueError("Only the league creator can edit settings.")
            if league['status'] != 'registering':
                raise ValueError("League settings can only be edited before the league starts.")

            # Step 2: Update league settings and start time
            player_info = get_player_info(editor_id)
            player_timezone_str = player_info.get('timezone', 'UTC') if player_info else 'UTC'
            player_timezone = pytz.timezone(player_timezone_str)
            
            naive_start_time = datetime.fromisoformat(new_settings['start_time'])
            localized_start_time = player_timezone.localize(naive_start_time)
            new_start_time_utc = localized_start_time.astimezone(pytz.utc)

            update_sql = sqlalchemy.text("UPDATE leagues SET settings = :settings, start_time = :start_time WHERE league_id = :league_id")
            conn.execute(update_sql, {
                "settings": json.dumps(new_settings),
                "start_time": new_start_time_utc,
                "league_id": league_id
            })

            # Step 3: Delete old rounds and recreate them
            conn.execute(sqlalchemy.text("DELETE FROM league_rounds WHERE league_id = :league_id"), {"league_id": league_id})
            
            # Re-create rounds based on new settings
            num_rounds = new_settings.get('num_rounds', 4)
            round_duration_hours = new_settings.get('round_duration_hours', 168)
            # This part needs a helper function or inline logic to create rounds.
            # For simplicity, we'll assume a helper `_create_league_rounds` exists.
            # _create_league_rounds(league_id, new_start_time_utc, new_settings, conn)

            logger.info(f"League {league_id} settings updated by creator {editor_id}.")
            return True

def delete_league(league_id, deleter_id):
    """Deletes a league, only if the deleter is the creator and the league is in 'registering' state."""
    pool = get_db_connection()
    with pool.connect() as conn:
        with conn.begin() as trans:
            try:
                # Step 1: Verify permissions and status
                league = conn.execute(
                    sqlalchemy.text("SELECT creator_id, status, name FROM leagues WHERE league_id = :id"),
                    {"id": league_id}
                ).mappings().first()

                if not league:
                    raise ValueError("League not found.")
                if league['creator_id'] != deleter_id:
                    raise ValueError("Only the league creator can delete the league.")
                if league['status'] != 'registering':
                    raise ValueError("League can only be deleted before it starts.")

                # Step 2: Delete all related data in order (respecting foreign key constraints)
                
                # Delete league submissions first
                conn.execute(
                    sqlalchemy.text("DELETE FROM league_submissions WHERE round_id IN (SELECT round_id FROM league_rounds WHERE league_id = :league_id)"),
                    {"league_id": league_id}
                )
                
                # Delete league rounds
                conn.execute(
                    sqlalchemy.text("DELETE FROM league_rounds WHERE league_id = :league_id"),
                    {"league_id": league_id}
                )
                
                # Delete league memberships
                conn.execute(
                    sqlalchemy.text("DELETE FROM league_memberships WHERE league_id = :league_id"),
                    {"league_id": league_id}
                )
                
                # Finally delete the league itself
                conn.execute(
                    sqlalchemy.text("DELETE FROM leagues WHERE league_id = :league_id"),
                    {"league_id": league_id}
                )

                logger.info(f"League '{league['name']}' (ID: {league_id}) deleted by creator {deleter_id}.")
                return True

            except Exception as e:
                logger.error(f"Failed to delete league {league_id}: {e}")
                raise

    return leaderboards

# Password Recovery Functions

def create_password_reset_token(player_id):
    """Creates a password reset token for a player."""
    import secrets
    import string
    
    # Generate a secure random token
    alphabet = string.ascii_letters + string.digits
    token = ''.join(secrets.choice(alphabet) for i in range(32))
    
    # Token expires in 1 hour
    expires_at = datetime.utcnow() + timedelta(hours=1)
    
    pool = get_db_connection()
    with pool.connect() as conn:
        with conn.begin():
            # Invalidate any existing tokens for this player
            conn.execute(
                sqlalchemy.text("UPDATE password_reset_tokens SET used = TRUE WHERE player_id = :player_id AND used = FALSE"),
                {"player_id": player_id}
            )
            
            # Create new token
            conn.execute(
                sqlalchemy.text("""
                    INSERT INTO password_reset_tokens (player_id, token, expires_at, used, created_at)
                    VALUES (:player_id, :token, :expires_at, FALSE, :current_time)
                """),
                {
                    "player_id": player_id,
                    "token": token,
                    "expires_at": expires_at,
                    "current_time": datetime.utcnow()
                }
            )
    
    logger.info(f"Created password reset token for player {player_id}")
    return token

def validate_password_reset_token(token):
    """Validates a password reset token and returns the player_id if valid."""
    pool = get_db_connection()
    with pool.connect() as conn:
        result = conn.execute(
            sqlalchemy.text("""
                SELECT player_id, expires_at, used 
                FROM password_reset_tokens 
                WHERE token = :token
            """),
            {"token": token}
        ).mappings().first()
        
        if not result:
            return None
            
        if result['used']:
            logger.warning(f"Attempt to use already used password reset token")
            return None
            
        # Handle both datetime objects and string formats from database
        expires_at = result['expires_at']
        if isinstance(expires_at, str):
            expires_at = datetime.fromisoformat(expires_at.replace('Z', '+00:00'))
        
        if datetime.utcnow() > expires_at:
            logger.warning(f"Attempt to use expired password reset token")
            return None
            
        return result['player_id']

def use_password_reset_token(token, new_password):
    """Uses a password reset token to set a new password."""
    player_id = validate_password_reset_token(token)
    if not player_id:
        return False
    
    # Hash the new password
    password_hash = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    
    pool = get_db_connection()
    with pool.connect() as conn:
        with conn.begin():
            # Update the player's password
            conn.execute(
                sqlalchemy.text("UPDATE players SET password_hash = :password_hash WHERE player_id = :player_id"),
                {"password_hash": password_hash, "player_id": player_id}
            )
            
            # Mark token as used
            conn.execute(
                sqlalchemy.text("UPDATE password_reset_tokens SET used = TRUE WHERE token = :token"),
                {"token": token}
            )
    
    logger.info(f"Password reset completed for player {player_id}")
    return True

def get_player_by_email(email):
    """Gets a player by their email address."""
    pool = get_db_connection()
    with pool.connect() as conn:
        result = conn.execute(
            sqlalchemy.text("SELECT player_id, email, name FROM players WHERE email = :email"),
            {"email": email}
        ).mappings().first()
        
        return dict(result) if result else None

# Fundraising Functions

def create_fundraiser(creator_id, fundraiser_data):
    """Creates a new fundraiser."""
    pool = get_db_connection()
    with pool.connect() as conn:
        with conn.begin():
            result = conn.execute(
                sqlalchemy.text("""
                    INSERT INTO fundraisers (
                        creator_id, title, description, charity_name, charity_wallet_address,
                        target_amount, sat_per_putt, start_date, end_date, status, created_at
                    ) VALUES (
                        :creator_id, :title, :description, :charity_name, :charity_wallet_address,
                        :target_amount, :sat_per_putt, :start_date, :end_date, 'active', :current_time
                    ) RETURNING fundraiser_id
                """),
                {
                    "creator_id": creator_id,
                    "title": fundraiser_data.get('title'),
                    "description": fundraiser_data.get('description'),
                    "charity_name": fundraiser_data.get('charity_name'),
                    "charity_wallet_address": fundraiser_data.get('charity_wallet_address'),
                    "target_amount": fundraiser_data.get('target_amount', 0),
                    "sat_per_putt": fundraiser_data.get('sat_per_putt', 100),
                    "start_date": datetime.fromisoformat(fundraiser_data.get('start_date')) if fundraiser_data.get('start_date') else datetime.utcnow(),
                    "end_date": datetime.fromisoformat(fundraiser_data.get('end_date')) if fundraiser_data.get('end_date') else None,
                    "current_time": datetime.utcnow()
                }
            )
            fundraiser_id = result.scalar()
    
    logger.info(f"Created fundraiser {fundraiser_id} by player {creator_id}")
    return fundraiser_id

def get_fundraisers():
    """Gets all active fundraisers."""
    pool = get_db_connection()
    with pool.connect() as conn:
        results = conn.execute(
            sqlalchemy.text("""
                SELECT f.*, p.name as creator_name
                FROM fundraisers f
                JOIN players p ON f.creator_id = p.player_id
                WHERE f.status = 'active'
                ORDER BY f.created_at DESC
            """)
        ).mappings().all()
        
        fundraisers = []
        for result in results:
            fundraiser = dict(result)
            # Convert datetime objects to ISO strings
            for key, value in fundraiser.items():
                if isinstance(value, datetime):
                    fundraiser[key] = value.isoformat()
            fundraisers.append(fundraiser)
        
        return fundraisers

def get_fundraiser(fundraiser_id):
    """Gets a specific fundraiser by ID."""
    pool = get_db_connection()
    with pool.connect() as conn:
        result = conn.execute(
            sqlalchemy.text("""
                SELECT f.*, p.name as creator_name
                FROM fundraisers f
                JOIN players p ON f.creator_id = p.player_id
                WHERE f.fundraiser_id = :fundraiser_id
            """),
            {"fundraiser_id": fundraiser_id}
        ).mappings().first()
        
        if not result:
            return None
            
        fundraiser = dict(result)
        # Convert datetime objects to ISO strings
        for key, value in fundraiser.items():
            if isinstance(value, datetime):
                fundraiser[key] = value.isoformat()
        
        return fundraiser

def create_pledge(fundraiser_id, pledger_id, pledge_data):
    """Creates a pledge for a fundraiser."""
    pool = get_db_connection()
    with pool.connect() as conn:
        with conn.begin():
            result = conn.execute(
                sqlalchemy.text("""
                    INSERT INTO pledges (
                        fundraiser_id, pledger_id, amount_per_putt, max_amount, status, created_at
                    ) VALUES (
                        :fundraiser_id, :pledger_id, :amount_per_putt, :max_amount, 'active', :current_time
                    ) RETURNING pledge_id
                """),
                {
                    "fundraiser_id": fundraiser_id,
                    "pledger_id": pledger_id,
                    "amount_per_putt": pledge_data.get('amount_per_putt', 100),
                    "max_amount": pledge_data.get('max_amount'),
                    "current_time": datetime.utcnow()
                }
            )
            pledge_id = result.scalar()
    
    logger.info(f"Created pledge {pledge_id} for fundraiser {fundraiser_id} by player {pledger_id}")
    return pledge_id

def get_fundraiser_pledges(fundraiser_id):
    """Gets all pledges for a fundraiser."""
    pool = get_db_connection()
    with pool.connect() as conn:
        results = conn.execute(
            sqlalchemy.text("""
                SELECT p.*, pl.name as pledger_name
                FROM pledges p
                JOIN players pl ON p.pledger_id = pl.player_id
                WHERE p.fundraiser_id = :fundraiser_id AND p.status = 'active'
                ORDER BY p.created_at DESC
            """),
            {"fundraiser_id": fundraiser_id}
        ).mappings().all()
        
        pledges = []
        for result in results:
            pledge = dict(result)
            # Convert datetime objects to ISO strings
            for key, value in pledge.items():
                if isinstance(value, datetime):
                    pledge[key] = value.isoformat()
            pledges.append(pledge)
        
        return pledges