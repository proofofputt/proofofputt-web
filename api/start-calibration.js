export default function handler(req, res) {
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type, Authorization');
  
  if (req.method === 'OPTIONS') {
    return res.status(200).end();
  }

  if (req.method === 'POST') {
    const { player_id, camera_index } = req.body;

    if (!player_id) {
      return res.status(400).json({ error: 'Player ID is required' });
    }

    // Mock response - in real implementation this would start calibration process
    return res.status(200).json({
      message: 'Calibration started successfully',
      player_id: parseInt(player_id),
      camera_index: camera_index || 0,
      calibration_id: `calib_${Date.now()}`,
      status: 'calibrating',
      started_at: new Date().toISOString()
    });
  }

  return res.status(405).json({ error: 'Method not allowed' });
}