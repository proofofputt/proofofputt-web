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
      duels: [
        { 
          id: 1, 
          challenger_name: "Pop", 
          opponent_name: "Tiger", 
          status: "active",
          my_role: parseInt(playerId) === 1 ? "challenger" : "opponent",
          score_challenger: 15,
          score_opponent: 12,
          created_at: "2025-08-29T10:00:00Z"
        },
        { 
          id: 2, 
          challenger_name: "Jordan", 
          opponent_name: "Pop", 
          status: "completed",
          my_role: parseInt(playerId) === 1 ? "opponent" : "challenger", 
          score_challenger: 20,
          score_opponent: 18,
          winner: "Jordan",
          created_at: "2025-08-28T15:30:00Z"
        }
      ]
    });
  }

  return res.status(405).json({ error: 'Method not allowed' });
}