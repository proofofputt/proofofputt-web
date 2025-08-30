export default function handler(req, res) {
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type, Authorization');
  
  if (req.method === 'OPTIONS') {
    return res.status(200).end();
  }

  if (req.method === 'GET') {
    // Mock desktop app connection status
    // In production, this would check if desktop app has pinged recently
    const isConnected = Math.random() > 0.3; // 70% chance connected for demo
    
    return res.status(200).json({
      connected: isConnected,
      last_ping: isConnected ? new Date().toISOString() : null,
      status: isConnected ? 'active' : 'disconnected',
      desktop_version: isConnected ? '1.0.0' : null,
      capabilities: isConnected ? ['camera_capture', 'cv_processing', 'calibration'] : []
    });
  }

  return res.status(405).json({ error: 'Method not allowed' });
}