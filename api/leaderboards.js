export default function handler(req, res) {
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type, Authorization');
  
  if (req.method === 'OPTIONS') {
    return res.status(200).end();
  }

  const { type = 'global', timeframe = 'weekly' } = req.query;

  if (req.method === 'GET') {
    return res.status(200).json({
      top_makes: [
        { name: "Jordan", value: 1040, rank: 1 },
        { name: "Pop", value: 923, rank: 2 },
        { name: "Tiger", value: 698, rank: 3 },
        { name: "Rory", value: 588, rank: 4 }
      ],
      top_streaks: [
        { name: "Jordan", value: 12, rank: 1 },
        { name: "Pop", value: 8, rank: 2 },
        { name: "Tiger", value: 5, rank: 3 },
        { name: "Rory", value: 3, rank: 4 }
      ],
      top_makes_per_minute: [
        { name: "Pop", value: 2.8, rank: 1 },
        { name: "Tiger", value: 2.4, rank: 2 },
        { name: "Jordan", value: 2.1, rank: 3 },
        { name: "Rory", value: 1.9, rank: 4 }
      ],
      fastest_21: [
        { name: "Pop", value: "7:32", rank: 1 },
        { name: "Tiger", value: "8:45", rank: 2 },
        { name: "Jordan", value: "9:21", rank: 3 },
        { name: "Rory", value: "10:15", rank: 4 }
      ],
      type,
      timeframe,
      updated_at: new Date().toISOString()
    });
  }

  return res.status(405).json({ error: 'Method not allowed' });
}