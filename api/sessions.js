export default function handler(req, res) {
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type, Authorization');
  
  if (req.method === 'OPTIONS') {
    return res.status(200).end();
  }

  const { player_id } = req.query;

  if (req.method === 'GET') {
    return res.status(200).json([
      {
        session_id: 1,
        player_id: parseInt(player_id) || 1,
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
        player_id: parseInt(player_id) || 1,
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
    ]);
  }

  return res.status(405).json({ error: 'Method not allowed' });
}