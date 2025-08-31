export default function handler(req, res) {
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type, Authorization');
  
  if (req.method === 'OPTIONS') {
    return res.status(200).end();
  }

  if (req.method === 'GET') {
    // TODO: Implement database query for active duels
    return res.status(200).json({
      duels: []
    });
  }
  
  if (req.method === 'POST') {
    const { opponent_id, stakes, rules } = req.body;
    return res.status(200).json({ 
      success: true, 
      duel: { 
        id: Date.now(),
        challenger_id: 1,
        opponent_id,
        stakes,
        rules,
        status: "pending",
        created_at: new Date().toISOString()
      }
    });
  }

  return res.status(405).json({ error: 'Method not allowed' });
}