export default function handler(req, res) {
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type, Authorization');
  
  if (req.method === 'OPTIONS') {
    return res.status(200).end();
  }

  const { leagueId } = req.query;

  if (req.method === 'POST') {
    return res.status(200).json({
      success: true,
      message: "Successfully joined league",
      league_id: parseInt(leagueId),
      member_since: new Date().toISOString()
    });
  }

  if (req.method === 'DELETE') {
    return res.status(200).json({
      success: true,
      message: "Successfully left league"
    });
  }

  return res.status(405).json({ error: 'Method not allowed' });
}