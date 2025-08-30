export default function handler(req, res) {
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type, Authorization');
  
  if (req.method === 'OPTIONS') {
    return res.status(200).end();
  }

  if (req.method === 'POST') {
    const { name, email, password, early_access_code } = req.body;
    
    // Basic validation
    if (!name || !email || !password) {
      return res.status(400).json({
        success: false,
        error: "Name, email and password are required"
      });
    }

    return res.status(200).json({
      success: true,
      player: {
        id: Date.now(),
        name,
        email,
        membership_tier: early_access_code === 'early' ? 'premium' : 'basic',
        created_at: new Date().toISOString()
      },
      token: 'mock-jwt-token-' + Date.now(),
      message: "Registration successful"
    });
  }

  return res.status(405).json({ error: 'Method not allowed' });
}