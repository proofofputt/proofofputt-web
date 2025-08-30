export default function handler(req, res) {
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type, Authorization');
  
  if (req.method === 'OPTIONS') {
    return res.status(200).end();
  }

  if (req.method === 'POST') {
    const { player_id, duel_id, league_round_id } = req.body;

    if (!player_id) {
      return res.status(400).json({ error: 'Player ID is required' });
    }

    // Mock response - in real implementation this would start session tracking
    return res.status(200).json({
      message: 'Session started successfully',
      session_id: Date.now(), // Generate a mock session ID
      player_id: parseInt(player_id),
      status: 'active',
      start_time: new Date().toISOString(),
      duel_id: duel_id || null,
      league_round_id: league_round_id || null
    });
  }

  return res.status(405).json({ error: 'Method not allowed' });
}