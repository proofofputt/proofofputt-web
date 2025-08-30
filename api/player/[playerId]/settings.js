export default function handler(req, res) {
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type, Authorization');
  
  if (req.method === 'OPTIONS') {
    return res.status(200).end();
  }

  const { playerId } = req.query;

  if (req.method === 'GET') {
    return res.status(200).json({
      settings: {
        notifications: {
          duel_challenges: true,
          league_updates: true,
          achievements: true,
          weekly_summary: false
        },
        privacy: {
          profile_visibility: "public",
          stats_visibility: "friends",
          allow_challenges: true
        },
        game_preferences: {
          default_session_length: 30,
          auto_calibrate: true,
          sound_effects: true,
          difficulty_level: "intermediate"
        }
      },
      player_id: parseInt(playerId)
    });
  }

  if (req.method === 'PUT') {
    const { settings } = req.body;
    
    return res.status(200).json({
      success: true,
      message: "Settings updated successfully",
      settings
    });
  }

  return res.status(405).json({ error: 'Method not allowed' });
}