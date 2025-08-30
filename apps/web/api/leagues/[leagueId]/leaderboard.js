export default function handler(req, res) {
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type, Authorization');
  
  if (req.method === 'OPTIONS') {
    return res.status(200).end();
  }

  const { leagueId } = req.query;

  if (req.method === 'GET') {
    return res.status(200).json({
      leaderboard: [
        { 
          player_id: 1, 
          name: "Pop", 
          sessions: 12, 
          make_percentage: 74.4, 
          total_putts: 1240,
          total_makes: 923,
          rank: 1,
          points: 2850
        },
        { 
          player_id: 2, 
          name: "Tiger", 
          sessions: 10, 
          make_percentage: 71.2, 
          total_putts: 980,
          total_makes: 698,
          rank: 2,
          points: 2650
        },
        { 
          player_id: 3, 
          name: "Jordan", 
          sessions: 15, 
          make_percentage: 68.9, 
          total_putts: 1510,
          total_makes: 1040,
          rank: 3,
          points: 2580
        }
      ],
      league_id: parseInt(leagueId),
      updated_at: new Date().toISOString()
    });
  }

  return res.status(405).json({ error: 'Method not allowed' });
}