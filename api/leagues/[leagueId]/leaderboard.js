export default function handler(req, res) {
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type, Authorization');
  
  if (req.method === 'OPTIONS') {
    return res.status(200).end();
  }

  const { leagueId } = req.query;

  if (req.method === 'GET') {
    // TODO: Implement database query for league leaderboard
    return res.status(200).json({
      leaderboard: [],
      league_id: parseInt(leagueId),
      updated_at: new Date().toISOString()
    });
  }

  return res.status(405).json({ error: 'Method not allowed' });
}