
import { getDb } from '../db.js';

export default async function handler(req, res) {
  // Set CORS headers for all requests
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type, Authorization');

  if (req.method === 'OPTIONS') {
    return res.status(200).end();
  }

  const { playerId } = req.query;

  if (req.method === 'GET') {
    // Add validation for playerId
    if (!playerId) {
      return res.status(400).json({ error: 'Player ID is required' });
    }

    const playerIdNum = parseInt(playerId);
    if (isNaN(playerIdNum)) {
      return res.status(400).json({ error: 'Invalid Player ID' });
    }

    const db = getDb();
    try {
      const playerQuery = 'SELECT * FROM players WHERE id = $1';
      const playerResult = await db.query(playerQuery, [playerIdNum]);

      if (playerResult.rows.length === 0) {
        return res.status(404).json({ error: 'Player not found' });
      }

      const player = playerResult.rows[0];

      const statsQuery = 'SELECT * FROM player_stats WHERE player_id = $1';
      const statsResult = await db.query(statsQuery, [playerIdNum]);
      const stats = statsResult.rows[0] || {
        total_makes: 0,
        total_misses: 0,
        best_streak: 0,
        make_percentage: 0,
        total_putts: 0,
        avg_distance: 0,
        sessions_played: 0
      };

      const sessionsQuery = 'SELECT * FROM sessions WHERE player_id = $1 ORDER BY start_time DESC';
      const sessionsResult = await db.query(sessionsQuery, [playerIdNum]);
      const sessions = sessionsResult.rows;

      const calibrationQuery = 'SELECT * FROM calibrations WHERE player_id = $1';
      const calibrationResult = await db.query(calibrationQuery, [playerIdNum]);
      const calibration_data = calibrationResult.rows[0] || {
        is_calibrated: false,
        last_calibration: null,
        camera_index: null,
        roi_coordinates: null
      };

      return res.status(200).json({
        player_id: player.id,
        name: player.name,
        email: player.email,
        membership_tier: player.membership_tier,
        early_access_code: player.early_access_code,
        subscription_status: player.subscription_status,
        timezone: player.timezone,
        stats,
        sessions,
        calibration_data,
      });
    } catch (error) {
      console.error('Error fetching player data:', error);
      return res.status(500).json({ error: 'Internal server error' });
    }
  }

  return res.status(405).json({ error: 'Method not allowed' });
}
