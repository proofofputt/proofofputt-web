export default function handler(req, res) {
  // Enable CORS
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'GET, POST, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type');

  if (req.method === 'OPTIONS') {
    return res.status(200).end();
  }

  if (req.method === 'POST') {
    const { email, password } = req.body;
    
    // Mock authentication for testing
    if (email === 'pop@proofofputt.com' && password === 'passwordpop123') {
      return res.status(200).json({
        success: true,
        player_id: 1,
        name: 'Pop',
        email: email,
        token: 'mock-jwt-token'
      });
    } else {
      return res.status(401).json({
        error: 'Invalid credentials'
      });
    }
  }

  return res.status(405).json({ error: 'Method not allowed' });
}