import os # Cache-busting comment
from flask import Flask, request, jsonify
from flask_cors import CORS
import json
import subprocess
import sys
from dotenv import load_dotenv
import logging
from datetime import datetime, timedelta, timezone
import threading
from google.api_core import exceptions as google_exceptions
import tenacity
from functools import wraps
import google.generativeai as genai

# Configure logging to show INFO messages
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('api') # Use a specific logger for api.py

# Load environment variables from a .env file at the project root.
load_dotenv()

import data_manager
import notification_service # Import the new notification service
from utils import get_camera_index_from_config

# Configure the Gemini API client
try:
    genai.configure(api_key=os.environ.get("GEMINI_API_KEY"))
except Exception as e:
    logger.warning(f"Could not configure Gemini API. AI Coach will be disabled. Error: {e}")

app = Flask(__name__)
# Set up CORS, allowing for multiple origins from an environment variable
allowed_origins = [origin.strip() for origin in os.environ.get("ALLOWED_ORIGINS", "http://localhost:5173,https://www.proofofputt.com").split(',')]
CORS(app, resources={r"/*": {"origins": allowed_origins, "allow_headers": "Content-Type", "supports_credentials": True}})

# Initialize database and create default user once when the app starts
with app.app_context():
    data_manager.initialize_database()

@app.route('/')
def home():
    return "Proof of Putt API is running."

@app.route('/test')
def test_route():
    return "Test route is working!"

@app.route('/test-user')
def test_user():
    """Test endpoint to check if default user exists"""
    try:
        pool = data_manager.get_db_connection()
        with pool.connect() as conn:
            result = conn.execute(
                data_manager.sqlalchemy.text("SELECT player_id, email, name FROM players WHERE email = :email"),
                {"email": "pop@proofofputt.com"}
            ).mappings().first()
            if result:
                return f"Default user found: ID={result['player_id']}, Email={result['email']}, Name={result['name']}"
            else:
                return "Default user not found"
    except Exception as e:
        return f"Error checking user: {e}"

@app.route('/health')
def health_check():
    return jsonify({"status": "healthy", "timestamp": datetime.now(timezone.utc).isoformat()})

@app.route('/sessions/submit', methods=['POST'])
def submit_desktop_session():
    """Endpoint for desktop application to submit session data"""
    try:
        payload = request.get_json()
        
        if not payload:
            return jsonify({"error": "No data provided"}), 400
            
        session_data = payload.get('session_data')
        verification = payload.get('verification')
        source = payload.get('source', 'unknown')
        version = payload.get('version', 'unknown')
        
        if not session_data or not verification:
            return jsonify({"error": "Missing session_data or verification"}), 400
            
        logger.info(f"Received desktop session from {source} v{version}")
        logger.info(f"Session ID: {session_data['metadata']['session_id']}")
        logger.info(f"Player ID: {session_data['metadata']['player_id']}")
        logger.info(f"Putt entries: {len(session_data['putt_log_entries'])}")
        
        # Verify data integrity
        expected_count = verification['classification_count']
        actual_count = session_data['session_summary']['total_putts']
        
        if expected_count != actual_count:
            logger.warning(f"Data integrity mismatch: expected {expected_count}, got {actual_count}")
            
        # Process session data using existing SessionReporter
        putt_log_entries = []
        for entry in session_data['putt_log_entries']:
            # Filter to only classification entries (MAKE/MISS)
            if entry['classification'] in ['MAKE', 'MISS']:
                putt_log_entries.append(entry)
        
        if putt_log_entries:
            from session_reporter import SessionReporter
            
            # Process with SessionReporter (same as backend processing)
            reporter = SessionReporter(putt_log_entries)
            reporter.process_data()
            
            # Store in database using existing data_manager functions
            player_id = session_data['metadata']['player_id']
            
            # Create statistics dictionary from reporter attributes
            session_stats = {
                'total_putts': reporter.total_putts,
                'total_makes': reporter.total_makes,
                'total_misses': reporter.total_misses,
                'best_streak': reporter.max_consecutive_makes,
                'fastest_21_makes': reporter.fastest_21_makes if reporter.fastest_21_makes != float('inf') else None,
                'putts_per_minute': reporter.putts_per_minute,
                'makes_per_minute': reporter.makes_per_minute,
                'most_makes_in_60_seconds': reporter.most_makes_in_60_seconds,
                'session_duration': reporter.session_duration,
                'makes_by_category': reporter.makes_by_category,
                'misses_by_category': reporter.misses_by_category,
                'source': 'desktop',
                'session_id': session_data['metadata']['session_id'],
                'submitted_at': datetime.now(timezone.utc).isoformat()
            }
            
            # Format session data for save_session function
            session_save_data = {
                'player_id': player_id,
                'start_time': session_data['metadata']['start_time'],
                'end_time': session_data['metadata'].get('end_time'),
                'status': 'completed',
                'total_putts': session_stats.get('total_putts', 0),
                'total_makes': session_stats.get('total_makes', 0),
                'total_misses': session_stats.get('total_misses', 0),
                'best_streak': session_stats.get('best_streak', 0),
                'fastest_21_makes': session_stats.get('fastest_21_makes'),
                'putts_per_minute': session_stats.get('putts_per_minute', 0),
                'makes_per_minute': session_stats.get('makes_per_minute', 0),
                'most_makes_in_60_seconds': session_stats.get('most_makes_in_60_seconds', 0),
                'session_duration': session_stats.get('session_duration', 0),
                'putt_list': json.dumps(putt_log_entries),
                'makes_by_category': json.dumps(session_stats.get('makes_by_category', {})),
                'misses_by_category': json.dumps(session_stats.get('misses_by_category', {}))
            }
            
            # Store session using existing save_session function
            data_manager.save_session(session_save_data)
            success = True
            
            if success:
                logger.info(f"Desktop session {session_data['metadata']['session_id']} processed successfully")
                return jsonify({
                    "success": True,
                    "session_id": session_data['metadata']['session_id'],
                    "putts_processed": len(putt_log_entries),
                    "statistics": session_stats
                })
            else:
                return jsonify({"error": "Failed to store session results"}), 500
        else:
            logger.info("No classified putts in session, storing metadata only")
            return jsonify({
                "success": True,
                "session_id": session_data['metadata']['session_id'],
                "putts_processed": 0,
                "message": "Session received but no putts classified"
            })
            
    except Exception as e:
        logger.error(f"Error processing desktop session: {e}", exc_info=True)
        return jsonify({"error": "Internal server error"}), 500

@app.route('/sessions/<session_id>/verify', methods=['GET'])
def verify_session(session_id):
    """Verify that a session was processed correctly"""
    try:
        # Check if session exists in database
        session_info = data_manager.get_session_by_id(session_id)
        
        if session_info:
            return jsonify({
                "verified": True,
                "session_id": session_id,
                "processed_at": session_info.get('processed_at'),
                "putt_count": session_info.get('total_putts', 0)
            })
        else:
            return jsonify({
                "verified": False,
                "session_id": session_id,
                "error": "Session not found"
            }), 404
            
    except Exception as e:
        logger.error(f"Error verifying session {session_id}: {e}", exc_info=True)
        return jsonify({"error": "Verification failed"}), 500

@tenacity.retry(
    wait=tenacity.wait_exponential(multiplier=1, min=2, max=10),
    stop=tenacity.stop_after_attempt(3),
    retry=tenacity.retry_if_exception_type(google_exceptions.ResourceExhausted)
)
def _generate_content_with_retry(model, prompt):
    """Wrapper to retry Gemini API calls on rate limiting errors."""
    return model.generate_content(prompt)

@app.errorhandler(ValueError)
def handle_value_error(e):
    return jsonify({"error": str(e)}), 400

@app.errorhandler(Exception)
def handle_generic_exception(e):
    app.logger.error(f"An unexpected server error occurred: {e}", exc_info=True)
    return jsonify({"error": "An unexpected server error occurred."}), 500

@app.route('/favicon.ico')
def favicon():
    return '', 204

def subscription_required(f):
    """A decorator to protect routes that require a subscription."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        player_id = None
        # Extract player_id from route, body, or query args
        if 'player_id' in kwargs:
            player_id = kwargs['player_id']
        elif request.is_json:
            data = request.get_json()
            player_id = data.get('player_id') or data.get('creator_id')
        elif request.method == 'GET':
            player_id = request.args.get('player_id', type=int)

        if not player_id:
            return jsonify({"error": "Player identification is required for this feature."}), 400

        player_info = data_manager.get_player_info(player_id)
        if not player_info or player_info.get('subscription_status') != 'active':
            return jsonify({"error": "This feature requires a full subscription."}), 403
        return f(*args, **kwargs)
    return decorated_function

def _create_daily_ai_chat_if_needed(player_id):
    """
    Checks if a daily AI chat should be created for a subscribed player and creates it.
    This is intended to be run asynchronously (e.g., in a thread) to not block API responses.
    """
    with app.app_context():
        # Check subscription status
        player_info = data_manager.get_player_info(player_id)
        if not player_info or player_info.get('subscription_status') != 'active':
            return

        # Check daily limit - has a conversation been created in the last 24 hours?
        last_convo_time = data_manager.get_last_conversation_time(player_id)
        if last_convo_time and (datetime.now(timezone.utc) - last_convo_time.replace(tzinfo=timezone.utc) < timedelta(days=1)):
            return

        # Check for data to analyze - don't create a chat if there's nothing to talk about.
        stats = data_manager.get_player_stats(player_id)
        sessions = data_manager.get_sessions_for_player(player_id)
        if not stats or not sessions:
            app.logger.info(f"Skipping daily AI chat for player {player_id}: no stats or sessions.")
            return

        # All checks passed, create the conversation
        try:
            model = genai.GenerativeModel('gemini-1.5-flash-latest')
            recent_sessions = sessions[:2]
            player_name = player_info.get('name', f'Player {player_id}')
            
            initial_prompt = f'''As a PhD-level putting coach, provide a comprehensive initial analysis for {player_name}.
Please ensure the response is well-formatted for readability, using line breaks and bullet points as specified.

1.  **Career Skills Evaluation:** Based on these career stats, highlight one key accomplishment and provide one specific, actionable recommendation for improvement. Career Stats: {json.dumps(stats, indent=2)}
2.  **Recent Performance Summary:** Compare their two most recent sessions. Focus on changes in makes, misses, and makes per minute to identify short-term trends. Recent Sessions: {json.dumps(recent_sessions, indent=2)}
3.  **Putting Trends Analysis:** Analyze the 'classification' data within the sessions to identify any patterns (e.g., 'MISS - RETURN: Entry RAMP_ROI - Exit RAMP_ROI'). Provide an insight based on this data.

Keep the entire response concise and encouraging.'''
            initial_response = _generate_content_with_retry(model, initial_prompt)
            title_prompt = f"Create a very short, descriptive title (5 words or less) for a conversation that starts with this analysis: {initial_response.text}"
            title_response = _generate_content_with_retry(model, title_prompt)
            title = title_response.text.strip().replace('"', '') if title_response and title_response.text else "AI Coach Analysis"
            initial_history = [{'role': 'model', 'parts': [initial_response.text]}]
            new_conversation_id = data_manager.create_conversation(player_id, title, initial_history)

            notification_service.create_in_app_notification(player_id, 'AI_COACH_INSIGHT', 'Your AI Coach has a new insight for you!', {'conversation_id': new_conversation_id, 'title': title}, f'/coach/{new_conversation_id}')
            app.logger.info(f"Created daily AI chat {new_conversation_id} for player {player_id}.")
        except Exception as e:
            app.logger.error(f"Failed to auto-create daily AI chat for player {player_id}: {e}", exc_info=True)

# --- Auth & Player Routes ---

@app.route('/login', methods=['POST', 'OPTIONS'])
def login():
    if request.method == 'OPTIONS':
        return '', 200 # Handle CORS preflight

    data = request.get_json()
    email = data.get('email', '').strip()
    password = data['password']
    app.logger.info(f"Login attempt for email: {email}")
    if not email or not password:
        return jsonify({"error": "Invalid credentials"}), 401
    try:
        player_id, player_name, player_email, stats, sessions, timezone, subscription_status = data_manager.login_with_email_password(email, password)
        app.logger.info(f"Login result for {email}: player_id={player_id}")
        if player_id is not None:
            # Asynchronously trigger the daily AI chat creation check
            thread = threading.Thread(target=_create_daily_ai_chat_if_needed, args=(player_id,))
            thread.start()

            return jsonify({
                "player_id": player_id, 
                "name": player_name,
                "email": player_email,
                "stats": stats,
                "sessions": sessions,
                "timezone": timezone,
                "subscription_status": subscription_status,
                "is_new_user": False
            }), 200
        else:
            return jsonify({"error": "Invalid credentials"}), 401
    except Exception as e:
        app.logger.error(f"Login failed: {e}", exc_info=True)
        return jsonify({"error": "An internal error occurred during login."}), 500

@app.route('/register', methods=['POST', 'OPTIONS'])
def register():
    if request.method == 'OPTIONS':
        return '', 200 # Handle CORS preflight

    data = request.get_json()
    email = data.get('email', '').strip()
    password = data['password']
    name = data['name'].strip()
    if not email or not password or not name:
        return jsonify({"error": "Email, password, and name cannot be empty"}), 400
    try:
        player_id, player_name = data_manager.register_player(email, password, name)
        # After registering, log them in to get the full data object
        player_id, player_name, player_email, stats, sessions, timezone, subscription_status = data_manager.login_with_email_password(email, password)
        if player_id is not None:
            
            return jsonify({
                "player_id": player_id,
                "name": player_name,
                "email": player_email,
                "stats": stats,
                "sessions": sessions,
                "timezone": timezone,
                "subscription_status": subscription_status,
                "is_new_user": True
            }), 201
        else:
            return jsonify({"error": "Registration successful, but failed to log in automatically."}), 500
    except ValueError as e:
        return jsonify({"error": "A player with this email already exists."}), 409
    except Exception as e:
        app.logger.error(f"Registration failed: {e}", exc_info=True)
        return jsonify({"error": "An internal error occurred during registration."}), 500

@app.route('/player/<int:player_id>/data', methods=['GET'])
def get_player_data(player_id):
    """Endpoint to refresh all player data."""
    try:
        player_info = data_manager.get_player_info(player_id)
        if not player_info:
            return jsonify({"error": "Player not found"}), 404
        
        stats = data_manager.get_player_stats(player_id)
        sessions = data_manager.get_sessions_for_player(player_id, limit=25)
        
        # This structure should match the login response for consistency
        return jsonify({
            **player_info,
            "stats": stats,
            "sessions": sessions
        }), 200
    except Exception as e:
        app.logger.error(f"Error refreshing data for player {player_id}: {e}", exc_info=True)
        return jsonify({"error": "An internal error occurred."}), 500

# --- Player Profile Routes ---
@app.route('/player/<int:player_id>', methods=['PUT'])
@subscription_required
def update_player_profile(player_id):
    data = request.get_json()
    if not data:
        return jsonify({"error": "No update data provided."}), 400
    
    try:
        # Ensure the player_id in the URL matches the player_id in the request body if present
        # This is a security measure to prevent one player from updating another's profile
        if 'player_id' in data and data['player_id'] != player_id:
            return jsonify({"error": "Player ID mismatch."}), 403

        success = data_manager.update_player_profile(player_id, data)
        if success:
            return jsonify({"message": "Player profile updated successfully."}), 200
        else:
            return jsonify({"error": "Failed to update player profile."}), 500
    except Exception as e:
        app.logger.error(f"Error updating profile for player {player_id}: {e}", exc_info=True)
        return jsonify({"error": "An internal error occurred while updating the profile."}), 500

@app.route('/player/<int:player_id>/career-stats', methods=['GET'])
@subscription_required
def get_career_stats(player_id):
    app.logger.info(f"Attempting to get career stats for player_id: {player_id}")
    try:
        stats = data_manager.get_player_stats(player_id)
        if stats: # Check if stats is not None
            app.logger.info(f"Found stats for player {player_id}: {stats}")
            return jsonify(stats), 200
        app.logger.warning(f"No career stats found for player {player_id}. Returning 404.")
        return jsonify({"message": "No career stats found for this player."}), 404
    except Exception as e:
        app.logger.error(f"Error getting career stats for player {player_id}: {e}", exc_info=True)
        return jsonify({"error": "An internal error occurred."}), 500

@app.route('/player/<int:player_id>/sessions', methods=['GET'])
@subscription_required
def get_player_sessions(player_id):
    try:
        # Get pagination parameters from query string
        page = int(request.args.get('page', 1))
        limit = int(request.args.get('limit', 25))
        offset = (page - 1) * limit
        
        sessions = data_manager.get_sessions_for_player(player_id, limit=limit, offset=offset)
        
        # Get total count for pagination
        total_sessions = data_manager.get_player_session_count(player_id) if hasattr(data_manager, 'get_player_session_count') else len(sessions)
        total_pages = max(1, (total_sessions + limit - 1) // limit)  # Ceiling division
        
        return jsonify({
            "sessions": sessions,
            "current_page": page,
            "total_pages": total_pages,
            "total_sessions": total_sessions,
            "limit": limit
        }), 200
    except Exception as e:
        app.logger.error(f"Error getting sessions for player {player_id}: {e}", exc_info=True)
        return jsonify({"error": "An internal error occurred."}), 500

# --- Duels Routes ---
@app.route('/duels', methods=['POST'])
@subscription_required
def create_duel():
    data = request.get_json()
    creator_id = data.get('creator_id')
    invited_player_id = data.get('invited_player_id')
    settings = data.get('settings', {})

    if not all([creator_id, invited_player_id]):
        return jsonify({"error": "Creator ID and Invited Player ID are required."}), 400
    
    if creator_id == invited_player_id:
        return jsonify({"error": "You cannot duel yourself."}), 400

    try:
        duel_id = data_manager.create_duel(
            creator_id=creator_id,
            invited_player_id=invited_player_id,
            settings=settings
        )
        # TODO: Create a notification for the invited player
        return jsonify({"message": "Duel invitation sent successfully.", "duel_id": duel_id}), 201
    except Exception as e:
        app.logger.error(f"Error creating duel between {creator_id} and {invited_player_id}: {e}", exc_info=True)
        return jsonify({"error": "An internal error occurred while creating the duel."}), 500

@app.route('/duels/list/<int:player_id>', methods=['GET'])
@subscription_required
def list_duels(player_id):
    try:
        duels = data_manager.get_duels_for_player(player_id)
        return jsonify(duels), 200
    except Exception as e:
        app.logger.error(f"Error getting duels for player {player_id}: {e}", exc_info=True)
        return jsonify({"error": "An internal error occurred."}), 500

@app.route('/players/search', methods=['GET'])
@subscription_required
def search_players():
    search_term = request.args.get('search_term', '').strip()
    player_id = request.args.get('player_id', type=int)

    if not search_term or not player_id:
        return jsonify({"error": "Search term and player ID are required."}), 400

    try:
        players = data_manager.search_players(search_term, player_id)
        return jsonify(players), 200
    except Exception as e:
        app.logger.error(f"Error searching for players: {e}", exc_info=True)
        return jsonify({"error": "An internal error occurred during player search."}), 500

@app.route('/duels/<int:duel_id>/respond', methods=['POST'])
@subscription_required
def respond_to_duel(duel_id):
    data = request.get_json()
    player_id = data.get('player_id')
    response = data.get('response') # 'accepted' or 'declined'

    if not all([player_id, response]):
        return jsonify({"error": "Player ID and response are required."}), 400

    try:
        result = data_manager.respond_to_duel(duel_id, player_id, response)
        # TODO: Create a notification for the creator player
        return jsonify(result), 200
    except ValueError as ve:
        return jsonify({"error": str(ve)}), 400
    except Exception as e:
        app.logger.error(f"Error responding to duel {duel_id} for player {player_id}: {e}", exc_info=True)
        return jsonify({"error": "An internal error occurred."}), 500

@app.route('/duels/<int:duel_id>/submit', methods=['POST'])
@subscription_required
def submit_session_to_duel(duel_id):
    data = request.get_json()
    player_id = data.get('player_id')
    session_id = data.get('session_id')

    if not all([player_id, session_id]):
        return jsonify({"error": "Player ID and session ID are required."}), 400

    try:
        result = data_manager.submit_session_to_duel(duel_id, player_id, session_id)
        # TODO: Create a notification for the other player
        return jsonify(result), 200
    except ValueError as ve:
        return jsonify({"error": str(ve)}), 400
    except Exception as e:
        app.logger.error(f"Error submitting session to duel {duel_id} for player {player_id}: {e}", exc_info=True)
        return jsonify({"error": "An internal error occurred."}), 500

# --- Leaderboard Routes ---
@app.route('/leaderboards', methods=['GET'])
def get_leaderboards():
    try:
        leaderboard_data = data_manager.get_all_time_leaderboards()
        return jsonify(leaderboard_data), 200
    except Exception as e:
        app.logger.error(f"Error generating leaderboards: {e}", exc_info=True)
        return jsonify({"error": "An internal error occurred while generating the leaderboards."}), 500

# --- Player vs Player Routes ---
@app.route('/players/<int:player1_id>/vs/<int:player2_id>/duels', methods=['GET'])
@subscription_required
def get_player_vs_player_duels_api(player1_id, player2_id):
    try:
        duels_history = data_manager.get_player_vs_player_duels(player1_id, player2_id)
        return jsonify(duels_history), 200
    except Exception as e:
        app.logger.error(f"Error getting duels between {player1_id} and {player2_id}: {e}", exc_info=True)
        return jsonify({"error": "An internal error occurred."}), 500

@app.route('/players/<int:player1_id>/vs/<int:player2_id>/leaderboard', methods=['GET'])
@subscription_required
def get_player_vs_player_leaderboard_api(player1_id, player2_id):
    try:
        leaderboard_data = data_manager.get_player_vs_player_leaderboard(player1_id, player2_id)
        return jsonify(leaderboard_data), 200
    except Exception as e:
        app.logger.error(f"Error getting head-to-head leaderboard for {player1_id} vs {player2_id}: {e}", exc_info=True)
        return jsonify({"error": "An internal error occurred."}), 500

# --- Leagues Routes ---
@app.route('/leagues', methods=['GET'])
@subscription_required
def get_leagues():
    player_id = request.args.get('player_id', type=int)
    if not player_id:
        return jsonify({"error": "Player ID is required."}), 400
    try:
        leagues_data = data_manager.get_leagues_for_player(player_id)
        return jsonify(leagues_data), 200
    except Exception as e:
        app.logger.error(f"Error getting leagues for player {player_id}: {e}", exc_info=True)
        return jsonify({"error": "An internal error occurred."}), 500

@app.route('/leagues', methods=['POST'])
@subscription_required
def create_league():
    data = request.get_json()
    creator_id = data.get('creator_id')
    name = data.get('name')
    description = data.get('description', '')
    privacy_type = data.get('privacy_type', 'private')
    settings = data.get('settings', {}) # Default to empty dict
    start_time_str = data.get('start_time')

    if not all([creator_id, name, privacy_type, start_time_str]):
        return jsonify({"error": "Creator ID, name, privacy type, and start time are required."}), 400

    try:
        start_time = datetime.fromisoformat(start_time_str)
        league_id = data_manager.create_league(
            creator_id=creator_id,
            name=name,
            description=description,
            privacy_type=privacy_type,
            settings=settings,
            start_time_str=start_time_str
        )
        return jsonify({"message": "League created successfully.", "league_id": league_id}), 201
    except Exception as e:
        app.logger.error(f"Error creating league for player {creator_id}: {e}", exc_info=True)
        return jsonify({"error": "An internal error occurred while creating the league."}), 500

@app.route('/leagues/<int:league_id>', methods=['GET'])
@subscription_required
def get_league_details(league_id):
    try:
        details = data_manager.get_league_details(league_id)
        if details:
            return jsonify(details), 200
        else:
            return jsonify({"error": "League not found."}), 404
    except Exception as e:
        app.logger.error(f"Error getting details for league {league_id}: {e}", exc_info=True)
        return jsonify({"error": "An internal error occurred."}), 500

@app.route('/leagues/<int:league_id>/leaderboard', methods=['GET'])
@subscription_required
def get_league_leaderboard(league_id):
    try:
        leaderboard_data = data_manager.get_league_leaderboard(league_id)
        return jsonify(leaderboard_data), 200
    except Exception as e:
        app.logger.error(f"Error generating leaderboard for league {league_id}: {e}", exc_info=True)
        return jsonify({"error": "An internal error occurred."}), 500

@app.route('/leagues/<int:league_id>/settings', methods=['PUT'])
@subscription_required
def update_league_settings(league_id):
    data = request.get_json()
    editor_id = data.get('editor_id')
    new_settings = data.get('settings')

    if not editor_id or not new_settings:
        return jsonify({"error": "Editor ID and new settings are required."}), 400
    
    try:
        success = data_manager.update_league_settings(league_id, editor_id, new_settings)
        if success:
            return jsonify({"message": "League settings updated successfully."}), 200
    except ValueError as ve:
        return jsonify({"error": str(ve)}), 403 # Permission denied or bad state
    except Exception as e:
        app.logger.error(f"Error updating settings for league {league_id}: {e}", exc_info=True)
        return jsonify({"error": "An internal error occurred."}), 500

@app.route('/leagues/<int:league_id>', methods=['DELETE'])
@subscription_required
def delete_league(league_id):
    data = request.get_json()
    deleter_id = data.get('deleter_id')

    if not deleter_id:
        return jsonify({"error": "Deleter ID is required."}), 400
    
    try:
        success = data_manager.delete_league(league_id, deleter_id)
        if success:
            return jsonify({"message": "League deleted successfully."}), 200
    except ValueError as ve:
        return jsonify({"error": str(ve)}), 403  # Permission denied or bad state
    except Exception as e:
        app.logger.error(f"Error deleting league {league_id}: {e}", exc_info=True)
        return jsonify({"error": "An internal error occurred."}), 500

# --- Notifications Routes ---
@app.route('/notifications/<int:player_id>/unread_count', methods=['GET'])
@subscription_required
def get_unread_notification_count(player_id):
    try:
        count = data_manager.get_unread_notification_count(player_id)
        return jsonify({"unread_count": count}), 200
    except Exception as e:
        app.logger.error(f"Error getting unread notification count for player {player_id}: {e}", exc_info=True)
        return jsonify({"error": "An internal error occurred."}), 500

@app.route('/notifications/<int:player_id>', methods=['GET'])
@subscription_required
def get_notifications(player_id):
    """Fetches a paginated list of notifications for a player."""
    try:
        limit = request.args.get('limit', 20, type=int)
        offset = request.args.get('offset', 0, type=int)
        
        notifications = data_manager.get_notifications_for_player(player_id, limit, offset)
        return jsonify({"notifications": notifications}), 200
    except Exception as e:
        app.logger.error(f"Error getting notifications for player {player_id}: {e}", exc_info=True)
        return jsonify({"error": "An internal error occurred."}), 500

# --- Session Management Routes ---
@app.route('/start-session', methods=['POST'])
@subscription_required
def start_session():
    data = request.get_json()
    player_id = data.get('player_id')
    if not player_id:
        return jsonify({"error": "Player ID is required."}), 400

    # Check if the player has calibration data before starting a session.
    calibration_data = data_manager.get_calibration_data(player_id)
    if not calibration_data:
        app.logger.warning(f"Player {player_id} attempted to start a session without calibration data.")
        return jsonify({"error": "No calibration data found. Please calibrate your camera first from the Dashboard."}), 400

    try:
        script_path = os.path.join(os.path.dirname(__file__), 'run_tracker.py')
        process = subprocess.Popen([sys.executable, script_path, '--player_id', str(player_id)])
        app.logger.info(f"Started session process for player {player_id} with PID {process.pid}.")
        return jsonify({"message": "Session started successfully.", "pid": process.pid}), 200
    except Exception as e:
        app.logger.error(f"Failed to start session for player {player_id}: {e}", exc_info=True)
        return jsonify({"error": "Failed to start session process."}), 500

@app.route('/start-calibration', methods=['POST'])
@subscription_required
def start_calibration():
    data = request.get_json()
    player_id = data.get('player_id')
    camera_index = data.get('camera_index') # Optional camera index from frontend

    try:
        script_path = os.path.join(os.path.dirname(__file__), 'calibration.py')
        command = [sys.executable, script_path, '--player_id', str(player_id)]
        if camera_index is not None:
            command.extend(['--camera_index', str(camera_index)])
        else:
            command.extend(['--camera_index', '0']) # Default to camera index 0 if not provided
        
        app.logger.info(f"Executing calibration command: {' '.join(command)}")
        process = subprocess.Popen(command)
        app.logger.info(f"Started calibration process for player {player_id} with PID {process.pid}.")
        return jsonify({"message": "Calibration process started successfully.", "pid": process.pid}), 200
    except Exception as e:
        app.logger.error(f"Failed to start calibration for player {player_id}: {e}", exc_info=True)
        return jsonify({"error": "Failed to start calibration process."}), 500

# --- AI Coach Routes ---
@app.route('/coach/conversations', methods=['GET'])
@subscription_required
def get_coach_conversations():
    player_id = request.args.get('player_id', type=int)
    if not player_id:
        return jsonify({"error": "Player ID is required."}), 400
    try:
        conversations = data_manager.get_coach_conversations(player_id)
        return jsonify(conversations), 200
    except Exception as e:
        app.logger.error(f"Error getting coach conversations for player {player_id}: {e}", exc_info=True)
        return jsonify({"error": "An internal error occurred."}), 500

@app.route('/coach/conversation/<int:conversation_id>', methods=['GET'])
@subscription_required
def get_coach_conversation(conversation_id):
    # The decorator ensures the user is subscribed, but we also need the player_id
    # to securely fetch the conversation.
    player_id = request.args.get('player_id', type=int)
    if not player_id:
        return jsonify({"error": "Player ID is required."}), 400

    try:
        conversation = data_manager.get_coach_conversation_details(conversation_id, player_id)
        if conversation:
            return jsonify(conversation), 200
        else:
            return jsonify({"error": "Conversation not found or access denied."}), 404
    except Exception as e:
        app.logger.error(f"Error getting coach conversation {conversation_id} for player {player_id}: {e}", exc_info=True)
        return jsonify({"error": "An internal error occurred."}), 500

@app.route('/coach/conversation/<int:conversation_id>/message', methods=['POST'])
@subscription_required
def send_coach_message(conversation_id):
    # Placeholder for sending a message to coach
    return jsonify({"message": f"Message sent to coach for conversation {conversation_id}"}), 200

# --- Password Recovery Routes ---

@app.route('/forgot-password', methods=['POST', 'OPTIONS'])
def forgot_password():
    """Send password reset email to user."""
    if request.method == 'OPTIONS':
        return '', 200
    
    try:
        data = request.get_json()
        if not data or not data.get('email'):
            return jsonify({"error": "Email is required."}), 400
        
        email = data.get('email').strip().lower()
        
        # Check if player exists
        player = data_manager.get_player_by_email(email)
        if not player:
            # Don't reveal if email exists or not for security
            return jsonify({"message": "If this email is registered, you will receive a password reset link."}), 200
        
        # Create password reset token
        token = data_manager.create_password_reset_token(player['player_id'])
        
        # TODO: Send email with reset link
        # For now, we'll just log it (in production, integrate with SendGrid or similar)
        reset_link = f"https://www.proofofputt.com/reset-password?token={token}"
        app.logger.info(f"Password reset link for {email}: {reset_link}")
        
        return jsonify({"message": "If this email is registered, you will receive a password reset link."}), 200
        
    except Exception as e:
        app.logger.error(f"Error in forgot password: {e}", exc_info=True)
        return jsonify({"error": "An internal error occurred."}), 500

@app.route('/reset-password', methods=['POST', 'OPTIONS'])
def reset_password():
    """Reset password using token."""
    if request.method == 'OPTIONS':
        return '', 200
    
    try:
        data = request.get_json()
        if not data or not data.get('token') or not data.get('new_password'):
            return jsonify({"error": "Token and new password are required."}), 400
        
        token = data.get('token')
        new_password = data.get('new_password')
        
        # Validate password strength
        if len(new_password) < 6:
            return jsonify({"error": "Password must be at least 6 characters long."}), 400
        
        # Use the token to reset password
        success = data_manager.use_password_reset_token(token, new_password)
        
        if success:
            return jsonify({"message": "Password reset successfully."}), 200
        else:
            return jsonify({"error": "Invalid or expired reset token."}), 400
        
    except Exception as e:
        app.logger.error(f"Error in reset password: {e}", exc_info=True)
        return jsonify({"error": "An internal error occurred."}), 500

# --- Fundraising Routes ---

@app.route('/fundraisers', methods=['GET', 'OPTIONS'])
def get_fundraisers():
    """Get all active fundraisers."""
    if request.method == 'OPTIONS':
        return '', 200
    
    try:
        fundraisers = data_manager.get_fundraisers()
        return jsonify(fundraisers), 200
    except Exception as e:
        app.logger.error(f"Error getting fundraisers: {e}", exc_info=True)
        return jsonify({"error": "An internal error occurred."}), 500

@app.route('/fundraisers', methods=['POST'])
@subscription_required
def create_fundraiser():
    """Create a new fundraiser."""
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "Request body is required."}), 400
        
        # Validate required fields
        required_fields = ['title', 'charity_name']
        for field in required_fields:
            if not data.get(field):
                return jsonify({"error": f"{field} is required."}), 400
        
        # Get creator_id from request (you might need to modify this based on your auth system)
        creator_id = data.get('creator_id')  # In production, get from authenticated user
        if not creator_id:
            return jsonify({"error": "Creator ID is required."}), 400
        
        fundraiser_id = data_manager.create_fundraiser(creator_id, data)
        return jsonify({"message": "Fundraiser created successfully.", "fundraiser_id": fundraiser_id}), 201
        
    except Exception as e:
        app.logger.error(f"Error creating fundraiser: {e}", exc_info=True)
        return jsonify({"error": "An internal error occurred."}), 500

@app.route('/fundraisers/<int:fundraiser_id>', methods=['GET', 'OPTIONS'])
def get_fundraiser(fundraiser_id):
    """Get a specific fundraiser by ID."""
    if request.method == 'OPTIONS':
        return '', 200
    
    try:
        fundraiser = data_manager.get_fundraiser(fundraiser_id)
        if not fundraiser:
            return jsonify({"error": "Fundraiser not found."}), 404
        
        # Also get pledges for this fundraiser
        pledges = data_manager.get_fundraiser_pledges(fundraiser_id)
        fundraiser['pledges'] = pledges
        
        return jsonify(fundraiser), 200
    except Exception as e:
        app.logger.error(f"Error getting fundraiser {fundraiser_id}: {e}", exc_info=True)
        return jsonify({"error": "An internal error occurred."}), 500

@app.route('/fundraisers/<int:fundraiser_id>/pledge', methods=['POST', 'OPTIONS'])
@subscription_required
def create_pledge(fundraiser_id):
    """Create a pledge for a fundraiser."""
    if request.method == 'OPTIONS':
        return '', 200
    
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "Request body is required."}), 400
        
        # Get pledger_id from request (you might need to modify this based on your auth system)
        pledger_id = data.get('pledger_id')  # In production, get from authenticated user
        if not pledger_id:
            return jsonify({"error": "Pledger ID is required."}), 400
        
        # Validate that fundraiser exists
        fundraiser = data_manager.get_fundraiser(fundraiser_id)
        if not fundraiser:
            return jsonify({"error": "Fundraiser not found."}), 404
        
        pledge_id = data_manager.create_pledge(fundraiser_id, pledger_id, data)
        return jsonify({"message": "Pledge created successfully.", "pledge_id": pledge_id}), 201
        
    except Exception as e:
        app.logger.error(f"Error creating pledge for fundraiser {fundraiser_id}: {e}", exc_info=True)
        return jsonify({"error": "An internal error occurred."}), 500

if __name__ == "__main__":
    # Note: debug=True is great for development but should be False in production.
    # The host='0.0.0.0' makes the server accessible from other devices on the network.
    app.run(host='0.0.0.0', port=5001, debug=True)

# ... (rest of the file is the same) ...
