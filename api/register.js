export default function handler(req, res) {
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'POST, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type');

  if (req.method === 'OPTIONS') {
    return res.status(200).end();
  }

  if (req.method === 'POST') {
    const { email, password, name } = req.body;
    
    // Mock registration - in production, validate & store in database
    return res.status(200).json({
      success: true,
      player_id: Date.now(),
      name: name,
      email: email,
      token: 'mock-jwt-token-' + Date.now()
    });
  }

  return res.status(405).json({ error: 'Method not allowed' });
}