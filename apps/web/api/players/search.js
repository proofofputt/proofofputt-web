export default function handler(req, res) {
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type, Authorization');
  
  if (req.method === 'OPTIONS') {
    return res.status(200).end();
  }

  const { query: searchQuery } = req.query;

  if (req.method === 'GET') {
    const allPlayers = [
      { id: 1, name: "Pop", make_percentage: 74.4, total_sessions: 45, rank: 1 },
      { id: 2, name: "Tiger", make_percentage: 71.2, total_sessions: 38, rank: 2 },
      { id: 3, name: "Jordan", make_percentage: 68.9, total_sessions: 52, rank: 3 },
      { id: 4, name: "Rory", make_percentage: 66.1, total_sessions: 29, rank: 4 },
      { id: 5, name: "Scottie", make_percentage: 65.3, total_sessions: 41, rank: 5 }
    ];

    let filteredPlayers = allPlayers;
    if (searchQuery) {
      filteredPlayers = allPlayers.filter(player => 
        player.name.toLowerCase().includes(searchQuery.toLowerCase())
      );
    }

    return res.status(200).json({
      players: filteredPlayers,
      total: filteredPlayers.length
    });
  }

  return res.status(405).json({ error: 'Method not allowed' });
}