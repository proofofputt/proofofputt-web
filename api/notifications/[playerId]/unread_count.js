export default function handler(req, res) {
  // Set CORS headers
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'GET, POST, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type');
  
  if (req.method === 'OPTIONS') {
    return res.status(200).end();
  }

  if (req.method === 'GET') {
    const { playerId } = req.query;
    return res.status(200).json({
      unread_count: 2,
      player_id: parseInt(playerId) || 1
    });
  }

  return res.status(405).json({ error: 'Method not allowed' });
}