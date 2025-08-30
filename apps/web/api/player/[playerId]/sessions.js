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
      sessions: [
        {
          id: 1,
          date: "2025-08-30T09:00:00Z",
          duration: 1800, // 30 minutes in seconds
          total_putts: 45,
          makes: 33,
          make_percentage: 73.3,
          best_streak: 8,
          avg_distance: 6.2,
          session_type: "practice"
        },
        {
          id: 2,
          date: "2025-08-29T14:30:00Z", 
          duration: 2400, // 40 minutes
          total_putts: 62,
          makes: 44,
          make_percentage: 71.0,
          best_streak: 12,
          avg_distance: 5.8,
          session_type: "league"
        },
        {
          id: 3,
          date: "2025-08-28T11:15:00Z",
          duration: 1200, // 20 minutes
          total_putts: 28,
          makes: 21,
          make_percentage: 75.0,
          best_streak: 6,
          avg_distance: 4.9,
          session_type: "duel"
        }
      ],
      player_id: parseInt(playerId),
      total_sessions: 3
    });
  }

  return res.status(405).json({ error: 'Method not allowed' });
}