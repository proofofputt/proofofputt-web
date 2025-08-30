export default function handler(req, res) {
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'GET');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type');

  if (req.method === 'GET') {
    return res.status(200).json({
      weekly_leaders: [
        { player_id: 1, name: "Pop", sessions: 12, make_percentage: 74.4 },
        { player_id: 2, name: "Tiger", sessions: 10, make_percentage: 71.2 },
        { player_id: 3, name: "Jordan", sessions: 8, make_percentage: 68.9 }
      ],
      monthly_leaders: [
        { player_id: 1, name: "Pop", sessions: 47, make_percentage: 74.4 },
        { player_id: 4, name: "Rory", sessions: 43, make_percentage: 72.1 },
        { player_id: 2, name: "Tiger", sessions: 39, make_percentage: 71.2 }
      ]
    });
  }

  return res.status(405).json({ error: 'Method not allowed' });
}