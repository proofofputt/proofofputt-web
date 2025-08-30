export default function handler(req, res) {
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type, Authorization');
  
  if (req.method === 'OPTIONS') {
    return res.status(200).end();
  }

  if (req.method === 'GET') {
    return res.status(200).json({
      duels: [
        { 
          id: 1, 
          challenger_name: "Pop", 
          opponent_name: "Tiger", 
          status: "active",
          created_at: "2025-08-29T10:00:00Z",
          stakes: "Loser buys coffee"
        },
        { 
          id: 2, 
          challenger_name: "Jordan", 
          opponent_name: "Pop", 
          status: "pending",
          created_at: "2025-08-28T15:30:00Z",
          stakes: "50 putts challenge"
        }
      ]
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