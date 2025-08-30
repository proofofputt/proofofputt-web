export default function handler(req, res) {
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type, Authorization');
  
  if (req.method === 'OPTIONS') {
    return res.status(200).end();
  }

  const { player1Id, player2Id } = req.query;

  if (req.method === 'GET') {
    return res.status(200).json({
      duels: [
        {
          id: 1,
          date: "2025-08-29T10:00:00Z",
          winner_id: parseInt(player1Id),
          player1_score: 18,
          player2_score: 15,
          status: "completed"
        },
        {
          id: 2,
          date: "2025-08-25T14:30:00Z", 
          winner_id: parseInt(player2Id),
          player1_score: 12,
          player2_score: 16,
          status: "completed"
        }
      ],
      head_to_head: {
        player1_wins: 1,
        player2_wins: 1,
        total_duels: 2
      },
      player1_id: parseInt(player1Id),
      player2_id: parseInt(player2Id)
    });
  }

  return res.status(405).json({ error: 'Method not allowed' });
}