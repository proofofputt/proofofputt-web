export default function handler(req, res) {
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Credentials', 'true');
  res.setHeader('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type, Authorization');
  
  if (req.method === 'OPTIONS') {
    return res.status(200).end();
  }

  if (req.method === 'GET') {
    // For MVP demo - always return connected when desktop app is likely running
    // In production, this would check if desktop app has pinged recently
    const isConnected = true; // Always connected for demo
    
    return res.status(200).json({
      connected: isConnected,
      last_ping: new Date().toISOString(),
      status: 'active',
      desktop_version: '1.0.0',
      capabilities: ['camera_capture', 'cv_processing', 'calibration']
    });
  }

  return res.status(405).json({ error: 'Method not allowed' });
}