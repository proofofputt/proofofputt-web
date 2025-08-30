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
      league: {
        id: parseInt(leagueId),
        name: "Masters Champions",
        description: "Elite putting competition for advanced players",
        member_count: 24,
        is_member: true,
        created_at: "2025-08-15T10:00:00Z",
        rules: "Best of 100 putts, weekly competitions",
        entry_fee: 0,
        prize_pool: 500
      }
    });
  }

  if (req.method === 'PUT') {
    const { name, description, rules } = req.body;
    return res.status(200).json({
      success: true,
      message: "League updated successfully",
      league: {
        id: parseInt(leagueId),
        name,
        description, 
        rules
      }
    });
  }

  if (req.method === 'DELETE') {
    return res.status(200).json({
      success: true,
      message: "League deleted successfully"
    });
  }

  return res.status(405).json({ error: 'Method not allowed' });
}