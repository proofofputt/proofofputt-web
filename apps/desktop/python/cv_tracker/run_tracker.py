def update_local_career_stats(player_id, session_stats):
    """Reads a local career stats file, aggregates the new session, and writes it back."""
    data_dir = os.path.join(script_dir, '..', 'data')
    os.makedirs(data_dir, exist_ok=True)
    stats_file = os.path.join(data_dir, f'career_stats_{player_id}.json')

    career_stats = {}
    # Load existing career stats if they exist
    if os.path.exists(stats_file):
        try:
            with open(stats_file, 'r') as f:
                career_stats = json.load(f)
            debug_logger.info(f"Loaded local career stats from {stats_file}")
        except (IOError, json.JSONDecodeError) as e:
            debug_logger.error(f"Could not read or parse local career stats file: {e}")
            # Start with a fresh slate if file is corrupt
            career_stats = {}

    # Initialize stats if this is the first time
    if not career_stats:
        career_stats = {
            'total_putts': 0,
            'total_makes': 0,
            'total_misses': 0,
            'best_streak': 0,
            'total_duration_seconds': 0
        }

    # Aggregate new session data
    career_stats['total_putts'] += session_stats.get('total_putts', 0)
    career_stats['total_makes'] += session_stats.get('total_makes', 0)
    career_stats['total_misses'] += session_stats.get('total_misses', 0)
    career_stats['total_duration_seconds'] += session_stats.get('session_duration', 0)
    career_stats['best_streak'] = max(career_stats.get('best_streak', 0), session_stats.get('best_streak', 0))

    # Save the updated stats back to the local file
    try:
        with open(stats_file, 'w') as f:
            json.dump(career_stats, f, indent=4)
        debug_logger.info(f"Updated and saved local career stats to {stats_file}")
    except IOError as e:
        debug_logger.error(f"Could not save updated local career stats: {e}")