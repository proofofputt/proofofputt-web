# Refactored main application entry point.
import cv2
import logging
import numpy as np
from datetime import datetime, timezone
import json
import time
import os
import argparse
import sys # Gemini-added
import subprocess

# Gemin-added: Import the data manager and other necessary components
import data_manager
from video_processor import VideoProcessor
from putt_classifier import PuttClassifier
from session_reporter import SessionReporter # Assuming this class works as intended

# --- Gemini Refactor: Enhanced Logging from Prototype ---
# Get the absolute path of the directory where the script is located
script_dir = os.path.dirname(os.path.abspath(__file__))
log_dir = os.path.join(os.path.dirname(__file__), "logs")
os.makedirs(log_dir, exist_ok=True)

# Set up a separate debug logger
debug_logger = logging.getLogger("tracker_debug")
debug_logger.setLevel(logging.DEBUG)
debug_log_filename = os.path.join(log_dir, f"debug_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt")
file_handler = logging.FileHandler(debug_log_filename)
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
file_handler.setFormatter(formatter)
debug_logger.addHandler(file_handler)

# Set up logging for putt classification results (CSV format)
putt_log_filename = os.path.join(log_dir, f"putt_classification_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv")
putt_logger = logging.getLogger('putt_logger')
putt_logger.setLevel(logging.INFO)
putt_handler = logging.FileHandler(putt_log_filename)
putt_handler.setFormatter(logging.Formatter('%(message)s')) # Only message
putt_logger.addHandler(putt_handler)
putt_logger.info("current_frame_time,classification,detailed_classification,ball_x,ball_y,transition_history") # CSV header

# Suppress matplotlib font manager debug messages
logging.getLogger('matplotlib.font_manager').setLevel(logging.WARNING)

DISPLAY_VIDEO = True # Keep video display on

# --- Gemini: Added OBS Text File Update Function ---
def update_obs_text_files(stats, is_subscribed):
    """Writes session stats to text files for OBS, if user is subscribed."""
    if not is_subscribed:
        return

    total_makes, total_misses, consecutive_makes, max_consecutive_makes = stats
    obs_dir = os.path.join(os.path.dirname(__file__), "obs_text_files")
    
    # Ensure OBS directory exists
    try:
        os.makedirs(obs_dir, exist_ok=True)
    except OSError as e:
        debug_logger.error(f"Could not create OBS directory {obs_dir}: {e}")
        return
    
    files_to_update = {
        "MadePutts.txt": int(total_makes) if total_makes is not None else 0,
        "MissedPutts.txt": int(total_misses) if total_misses is not None else 0,
        "TotalPutts.txt": int((total_makes or 0) + (total_misses or 0)),
        "CurrentStreak.txt": int(consecutive_makes) if consecutive_makes is not None else 0,
        "MaxStreak.txt": int(max_consecutive_makes) if max_consecutive_makes is not None else 0
    }

    for filename, value in files_to_update.items():
        try:
            with open(os.path.join(obs_dir, filename), "w") as f:
                # Ensure we write pure numbers without any units or formatting
                f.write(str(value))
            debug_logger.debug(f"Updated OBS file {filename} with value: {value}")
        except (IOError, TypeError, ValueError) as e:
            debug_logger.error(f"Could not write to OBS file {filename}: {e}")
            # Write a default value to prevent file corruption
            try:
                with open(os.path.join(obs_dir, filename), "w") as f:
                    f.write("0")
            except IOError:
                pass  # If we can't even write 0, there's a deeper issue

# --- Gemini Refactor: Added Helper Functions from Prototype ---

def update_display_window(display_frame, calibrated_rois, stats, ball_data, current_video_time):
    """Draws all visual elements onto the display frame."""
    height, width, _ = display_frame.shape
    total_makes, total_misses, consecutive_makes, max_consecutive_makes = stats
    (overall_detected_ball_center, detailed_classification_results_display, 
     ball_in_hole, classification) = ball_data

    # --- Define Colors ---
    DARK_GREEN = (0, 80, 0)
    HIGHLIGHT_YELLOW = (0, 255, 255)
    LIGHT_GREEN = (0, 255, 0)
    RED = (0, 0, 255)
    WHITE = (255, 255, 255)

    # --- Draw ROIs and Ball ---
    for name, roi_points_data in calibrated_rois.items():
        if name == "camera_index": continue
        roi_points = np.array(roi_points_data, dtype=np.int32)
        if len(roi_points) == 0: continue
        roi_flag_key = f"ball_in_{name.lower().replace('_roi', '')}"
        is_ball_in_roi = detailed_classification_results_display.get(roi_flag_key, False)
        if name == "HOLE_ROI" and ball_in_hole:
            is_ball_in_roi = True
        color = HIGHLIGHT_YELLOW if is_ball_in_roi else DARK_GREEN
        cv2.polylines(display_frame, [roi_points], isClosed=True, color=color, thickness=2)

    if overall_detected_ball_center:
        cv2.circle(display_frame, (int(overall_detected_ball_center[0]), int(overall_detected_ball_center[1])), 10, HIGHLIGHT_YELLOW, -1)

    # --- Main Stats (Top Right) ---
    stats_font_scale = 2.0
    stats_font_thickness = 3
    stats_y_offset = 80

    stats_to_draw = [
        (f"Makes: {total_makes}", LIGHT_GREEN),
        (f"Misses: {total_misses}", RED),
        (f"Streak: {consecutive_makes}", HIGHLIGHT_YELLOW),
        (f"Best: {max_consecutive_makes}", HIGHLIGHT_YELLOW)
    ]
    for text, color in stats_to_draw:
        (w, h), _ = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, stats_font_scale, stats_font_thickness)
        cv2.putText(display_frame, text, (width - w - 20, stats_y_offset), cv2.FONT_HERSHEY_SIMPLEX, stats_font_scale, color, stats_font_thickness)
        stats_y_offset += h + 40

    if current_video_time > 0:
        minutes = int(current_video_time // 60)
        seconds = int(current_video_time % 60)
        time_text = f"Time: {minutes:02d}:{seconds:02d}"
        (w, h), _ = cv2.getTextSize(time_text, cv2.FONT_HERSHEY_SIMPLEX, stats_font_scale, stats_font_thickness)
        cv2.putText(display_frame, time_text, (width - w - 20, stats_y_offset), cv2.FONT_HERSHEY_SIMPLEX, stats_font_scale, HIGHLIGHT_YELLOW, stats_font_thickness)

    # --- Quit Instructions (Bottom Left) ---
    cv2.putText(display_frame, "Press 'q' to end session", (20, height - 20), cv2.FONT_HERSHEY_SIMPLEX, 0.8, WHITE, 2)

    # --- ROI Status Table (Bottom Right) ---
    roi_table_font_scale = 1.2
    roi_y_offset = height - 20
    sorted_roi_items = sorted(detailed_classification_results_display.items())
    for k, v in reversed(sorted_roi_items):
        roi_name_clean = k.replace("ball_in_", "").upper()
        text = f"{roi_name_clean}: {v}"
        color = HIGHLIGHT_YELLOW if v else LIGHT_GREEN
        (w, h), _ = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, roi_table_font_scale, 1)
        cv2.putText(display_frame, text, (width - w - 20, roi_y_offset), cv2.FONT_HERSHEY_SIMPLEX, roi_table_font_scale, color, 1)
        roi_y_offset -= h + 10

    # --- Last Putt Result (Top Left) ---
    if classification:
        color = (0, 255, 0) if "MAKE" in classification else (0, 0, 255)
        cv2.putText(display_frame, f"Last Putt: {classification}", (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 1.0, color, 2)

    cv2.imshow("Putt Tracker", display_frame)

def confirm_calibration_interactively(cap, calibrated_rois, player_id):
    """
    Displays the loaded ROIs on the live camera feed and prompts the user for confirmation.
    If ROIs are incorrect, offers to launch calibration script.
    Returns True if calibration is confirmed, False if user quits or recalibrates.
    """
    debug_logger.info("Starting interactive calibration confirmation.")
    cv2.namedWindow("Confirm Calibration", cv2.WINDOW_NORMAL)
    while True:
        ret, frame = cap.read()
        if not ret:
            debug_logger.error("Could not read frame during calibration confirmation.")
            cv2.destroyAllWindows()
            return False

        display_frame = frame.copy()
        for name, roi_points in calibrated_rois.items():
            if name != "camera_index" and len(roi_points) > 0:
                cv2.polylines(display_frame, [np.array(roi_points, dtype=np.int32)], isClosed=True, color=(0, 255, 255), thickness=2)

        cv2.putText(display_frame, "ROIs OK? Press 'y' to start, 'r' to recalibrate, 'q' to quit.", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)
        cv2.imshow("Confirm Calibration", display_frame)

        key = cv2.waitKey(1) & 0xFF
        if key == ord('y'):
            debug_logger.info("Calibration confirmed by user.")
            cv2.destroyAllWindows()
            return True
        elif key == ord('r'):
            debug_logger.info("User requested recalibration. Launching calibration script.")
            cv2.destroyAllWindows()
            subprocess.Popen([sys.executable, os.path.join(script_dir, 'calibration.py'), '--player_id', str(player_id), '--camera_index', str(int(cap.get(cv2.CAP_PROP_POS_FRAMES)))])
            return False
        elif key == ord('q'):
            debug_logger.info("User quit calibration confirmation. Exiting session.")
            cv2.destroyAllWindows()
            return False

def main():
    parser = argparse.ArgumentParser(description="Run the Putt Tracker application.")
    parser.add_argument("--player_id", type=int, required=True, help="The ID of the player for this session.")
    parser.add_argument("--camera_index", type=int, help="Override the camera index from calibration data.")
    parser.add_argument("--time_limit_seconds", type=int, help="Optional session duration limit in seconds.")
    args = parser.parse_args()
    
    # --- 1. Load Calibration & Initialize ---
    debug_logger.info(f"Session started for Player ID: {args.player_id}")

    player_info = data_manager.get_player_info(args.player_id)
    if not player_info:
        debug_logger.error(f"Could not retrieve player info for player {args.player_id}. Exiting.")
        return
    is_subscribed = player_info.get('subscription_status') == 'active'
    if is_subscribed:
        debug_logger.info("Player is subscribed. OBS text file updates will be enabled.")
    else:
        debug_logger.info("Player is not subscribed. OBS text file updates will be disabled.")

    calibrated_rois = data_manager.get_calibration_data(args.player_id)
    if not calibrated_rois:
        debug_logger.error(f"Calibration data not found for player {args.player_id}. Please run calibration first.")
        return

    # Determine camera index
    camera_index = calibrated_rois.get("camera_index", 0)
    if args.camera_index is not None:
        camera_index = args.camera_index
        debug_logger.info(f"Using camera index override from command line: {camera_index}")

    # Initialize video capture and processors
    cap = cv2.VideoCapture(camera_index)
    if not cap.isOpened():
        debug_logger.error(f"Error: Could not open camera with index {camera_index}.")
        return

    model_path = os.path.join(os.path.dirname(__file__), "models", "best.pt")
    video_processor = VideoProcessor(model_path=model_path)
    rois_np = {name: np.array(data, dtype=np.int32) for name, data in calibrated_rois.items() if name != 'camera_index'}
    putt_classifier = PuttClassifier(yolo_model=video_processor.model, rois=rois_np, logger=debug_logger)

    # --- 2. Interactive Calibration Confirmation ---
    if not confirm_calibration_interactively(cap, calibrated_rois, args.player_id):
        debug_logger.info("Calibration not confirmed. Exiting session.")
        cap.release()
        return

    # --- 3. Main Tracking Loop ---
    if DISPLAY_VIDEO:
        cv2.namedWindow("Putt Tracker", cv2.WINDOW_NORMAL)

    session_start_time_utc = datetime.now(timezone.utc)
    session_start_time_local = time.time()

    scoring_active = False
    total_makes = 0
    total_misses = 0
    consecutive_makes = 0
    max_consecutive_makes = 0

    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                debug_logger.info("End of video stream.")
                break

            current_session_time = time.time() - session_start_time_local
            detected_balls = video_processor.process_frame(frame)
            
            (current_state, classification, detailed_classification_str, overall_detected_ball_center, 
             ball_in_putting_mat, ball_in_ramp, ball_in_return_track, ball_in_left_of_mat, 
             ball_in_catch, ball_in_hole, ball_in_hole_top, ball_in_hole_right, 
             ball_in_hole_low, ball_in_hole_left, ball_in_ramp_left, ball_in_ramp_center, 
             ball_in_ramp_right, transition_history) = putt_classifier.update_and_classify(frame, detected_balls, current_session_time)

            if classification:
                debug_logger.info(f"Putt classified: {classification} - {detailed_classification_str}")
                putt_logger.info(f'{current_session_time:.2f},{classification},{detailed_classification_str},{overall_detected_ball_center[0] if overall_detected_ball_center else ""},{overall_detected_ball_center[1] if overall_detected_ball_center else ""},{json.dumps(transition_history)}')
                
                if not scoring_active:
                    scoring_active = True
                    debug_logger.info("Scoring activated: First putt detected.")

                if classification.startswith("MAKE"):
                    total_makes += 1
                    consecutive_makes += 1
                    if consecutive_makes > max_consecutive_makes:
                        max_consecutive_makes = consecutive_makes
                elif "MISS" in classification.upper():
                    total_misses += 1
                    consecutive_makes = 0
                
                # Update OBS files after stats change
                current_stats = (total_makes, total_misses, consecutive_makes, max_consecutive_makes)
                update_obs_text_files(current_stats, is_subscribed)

            if DISPLAY_VIDEO:
                display_frame = frame.copy()
                detailed_classification_results_display = {"ball_in_putting_mat": ball_in_putting_mat, "ball_in_ramp": ball_in_ramp, "ball_in_hole": ball_in_hole, "ball_in_left_of_mat": ball_in_left_of_mat, "ball_in_catch": ball_in_catch, "ball_in_return_track": ball_in_return_track, "ball_in_ramp_left": ball_in_ramp_left, "ball_in_ramp_center": ball_in_ramp_center, "ball_in_ramp_right": ball_in_ramp_right, "ball_in_hole_top": ball_in_hole_top, "ball_in_hole_right": ball_in_hole_right, "ball_in_hole_low": ball_in_hole_low, "ball_in_hole_left": ball_in_hole_left}
                stats = (total_makes, total_misses, consecutive_makes, max_consecutive_makes)
                ball_data = (overall_detected_ball_center, detailed_classification_results_display, ball_in_hole, classification)
                update_display_window(display_frame, calibrated_rois, stats, ball_data, current_session_time)

            if cv2.waitKey(1) & 0xFF == ord('q'):
                debug_logger.info("'q' pressed by user. Ending session.")
                break
            
            if args.time_limit_seconds and current_session_time > args.time_limit_seconds:
                debug_logger.info(f"Session time limit of {args.time_limit_seconds}s reached.")
                break

    finally:
        # --- 4. Save Session to Database ---
        session_end_time_utc = datetime.now(timezone.utc)
        wall_clock_duration_seconds = (session_end_time_utc - session_start_time_utc).total_seconds()
        debug_logger.info(f"Session ended. Wall-clock duration: {wall_clock_duration_seconds:.2f} seconds.")

        reporter = SessionReporter.from_csv(putt_log_filename)
        reporter.process_data()
        debug_logger.info(f"Session report generated from log file: {putt_log_filename}")

        # Recalculate rate-based stats using the accurate wall-clock duration
        if wall_clock_duration_seconds > 0:
            final_duration_minutes = wall_clock_duration_seconds / 60.0
            putts_per_minute = reporter.total_putts / final_duration_minutes
            makes_per_minute = reporter.total_makes / final_duration_minutes
        else:
            putts_per_minute = 0.0
            makes_per_minute = 0.0

        session_data = {
            "player_id": args.player_id,
            "start_time": session_start_time_utc.isoformat(),
            "end_time": session_end_time_utc.isoformat(),
            "status": "completed",
            "total_putts": reporter.total_putts,
            "total_makes": reporter.total_makes,
            "total_misses": reporter.total_misses,
            "best_streak": reporter.max_consecutive_makes,
            "fastest_21_makes": reporter.fastest_21_makes if reporter.fastest_21_makes != float('inf') else 0.0,
            "putts_per_minute": putts_per_minute,
            "makes_per_minute": makes_per_minute,
            "most_makes_in_60_seconds": reporter.most_makes_in_60_seconds,
            "session_duration": wall_clock_duration_seconds,
            "putt_list": json.dumps(reporter.putt_data),
            "makes_by_category": json.dumps(reporter.makes_by_category),
            "misses_by_category": json.dumps(reporter.misses_by_category)
        }

        data_manager.save_session(session_data)
        debug_logger.info(f"Session saved to database for player {args.player_id}.")

        cap.release()
        if DISPLAY_VIDEO:
            cv2.destroyAllWindows()

if __name__ == "__main__":
    main()