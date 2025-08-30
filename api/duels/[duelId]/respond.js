export default function handler(req, res) {
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type, Authorization');
  
  if (req.method === 'OPTIONS') {
    return res.status(200).end();
  }

  const { duelId } = req.query;
  const { response, message } = req.body; // "accept" or "decline"

  if (req.method === 'POST') {
    return res.status(200).json({ 
      success: true, 
      message: `Duel ${response}ed successfully`,
      duel_id: parseInt(duelId),
      status: response === 'accept' ? 'active' : 'declined'
    });
  }

  return res.status(405).json({ error: 'Method not allowed' });
}