export default function handler(req, res) {
  // Set CORS headers for all requests
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type, Authorization');
  
  if (req.method === 'OPTIONS') {
    return res.status(200).end();
  }

  if (req.method === 'POST') {
    const { email, password } = req.body;
    
    if (email === 'pop@proofofputt.com' && password === 'passwordpop123') {
      return res.status(200).json({
        player_id: 1,
        name: 'Pop',
        email: email,
        subscription_status: 'active',
        timezone: 'America/New_York',
        stats: {
          total_makes: 57,
          total_misses: 26,
          best_streak: 8,
          make_percentage: 68.7,
          total_putts: 83,
          avg_distance: 6.2,
          sessions_played: 2
        },
        sessions: [
          {
            session_id: 1,
            start_time: '2025-08-30T14:00:00Z',
            end_time: '2025-08-30T14:15:00Z',
            total_putts: 45,
            total_makes: 32,
            total_misses: 13,
            make_percentage: 71.1,
            best_streak: 8,
            session_duration: 900,
            status: 'completed'
          },
          {
            session_id: 2,
            start_time: '2025-08-29T16:30:00Z',
            end_time: '2025-08-29T16:45:00Z',
            total_putts: 38,
            total_makes: 25,
            total_misses: 13,
            make_percentage: 65.8,
            best_streak: 5,
            session_duration: 750,
            status: 'completed'
          }
        ],
        calibration_data: {
          is_calibrated: true,
          last_calibration: '2025-08-30T12:00:00Z',
          camera_index: 0,
          roi_coordinates: { x: 100, y: 100, width: 300, height: 200 }
        },
        is_new_user: false
      });
    } else {
      return res.status(401).json({
        error: 'Invalid credentials'
      });
    }
  }

  return res.status(405).json({ error: 'Method not allowed' });
}