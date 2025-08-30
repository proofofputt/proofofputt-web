export default function handler(req, res) {
  try {
    // Set CORS headers for all requests
    res.setHeader('Access-Control-Allow-Origin', '*');
    res.setHeader('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS');
    res.setHeader('Access-Control-Allow-Headers', 'Content-Type, Authorization');
    
    if (req.method === 'OPTIONS') {
      return res.status(200).end();
    }

    const { playerId } = req.query;

    if (req.method === 'GET') {
      const playerIdNum = playerId ? parseInt(playerId) : 1;
      
      return res.status(200).json({
        unread_count: 2,
        player_id: playerIdNum
      });
    }

    return res.status(405).json({ error: 'Method not allowed' });
  } catch (error) {
    console.error('Notifications unread_count error:', error);
    return res.status(500).json({ error: 'Internal server error', message: error.message });
  }
}