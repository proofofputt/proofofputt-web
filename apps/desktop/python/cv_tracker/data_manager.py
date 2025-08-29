import os
import json
import logging

logger = logging.getLogger('tracker_debug')

def get_calibration_data(player_id):
    """Retrieves calibration data for a specific player from a local JSON file."""
    # In the desktop app, data will be stored locally, not in a DB.
    # We'll assume a standard location for calibration files.
    script_dir = os.path.dirname(os.path.abspath(__file__))
    data_dir = os.path.join(script_dir, '..', 'data') # Assume a data directory
    os.makedirs(data_dir, exist_ok=True)
    calibration_file = os.path.join(data_dir, f'calibration_player_{player_id}.json')

    if os.path.exists(calibration_file):
        try:
            with open(calibration_file, 'r') as f:
                data = json.load(f)
                logger.info(f"Retrieved local calibration data for player {player_id}.")
                return data
        except (json.JSONDecodeError, IOError) as e:
            logger.error(f"Error reading calibration file {calibration_file}: {e}")
            return None
    else:
        logger.warning(f"No local calibration data found for player {player_id} at {calibration_file}")
        return None

def save_calibration_data(player_id, calibration_data):
    """Saves calibration data (as a JSON string) for a specific player to a local file."""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    data_dir = os.path.join(script_dir, '..', 'data')
    os.makedirs(data_dir, exist_ok=True)
    calibration_file = os.path.join(data_dir, f'calibration_player_{player_id}.json')

    try:
        with open(calibration_file, 'w') as f:
            json.dump(calibration_data, f, indent=4)
        logger.info(f"Saved local calibration data for player {player_id} to {calibration_file}.")
    except IOError as e:
        logger.error(f"Error writing to calibration file {calibration_file}: {e}")

# The run_tracker will output session data to a CSV/JSON file.
# The desktop app's Rust/JS layer will be responsible for reading that file
# and sending its contents to the backend API.
# Therefore, save_session is not needed here.

def save_session(session_data):
    logger.info("Session saving is handled by the main desktop application, not the CV module.")
    pass
