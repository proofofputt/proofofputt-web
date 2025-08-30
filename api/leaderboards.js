export default function handler(req, res) {
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type, Authorization');
  
  if (req.method === 'OPTIONS') {
    return res.status(200).end();
  }

  const { type = 'global', timeframe = 'weekly' } = req.query;

  if (req.method === 'GET') {
    return res.status(200).json({
      leaderboard: [
        { 
          player_id: 1, 
          name: "Pop", 
          make_percentage: 74.4, 
          total_putts: 1240,
          total_makes: 923,
          sessions: 12,
          rank: 1,
          points: 2850,
          streak: 8
        },
        { 
          player_id: 2, 
          name: "Tiger", 
          make_percentage: 71.2, 
          total_putts: 980,
          total_makes: 698,
          sessions: 10,
          rank: 2,
          points: 2650,
          streak: 5
        },
        { 
          player_id: 3, 
          name: "Jordan", 
          make_percentage: 68.9, 
          total_putts: 1510,
          total_makes: 1040,
          sessions: 15,
          rank: 3,
          points: 2580,
          streak: 12
        },
        { 
          player_id: 4, 
          name: "Rory", 
          make_percentage: 66.1, 
          total_putts: 890,
          total_makes: 588,
          sessions: 8,
          rank: 4,
          points: 2240,
          streak: 3
        }
      ],
      type,
      timeframe,
      updated_at: new Date().toISOString()
    });
  }

  return res.status(405).json({ error: 'Method not allowed' });
}