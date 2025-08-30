export default function handler(req, res) {
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'GET');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type');

  if (req.method === 'GET') {
    const { player_id } = req.query;
    return res.status(200).json({
      sessions: [
        {
          id: 1,
          date: "2024-08-29",
          putts: 45,
          made: 33,
          make_percentage: 73.3,
          duration: 38,
          best_streak: 7
        },
        {
          id: 2, 
          date: "2024-08-28",
          putts: 52,
          made: 39,
          make_percentage: 75.0,
          duration: 42,
          best_streak: 9
        }
      ]
    });
  }

  return res.status(405).json({ error: 'Method not allowed' });
}