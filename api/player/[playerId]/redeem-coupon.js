export default function handler(req, res) {
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'POST, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type');

  if (req.method === 'OPTIONS') {
    return res.status(200).end();
  }

  if (req.method === 'POST') {
    const { coupon_code } = req.body;
    
    if (coupon_code === 'early') {
      return res.status(200).json({
        success: true,
        message: 'Early access code redeemed successfully!',
        tier_updated: 'premium'
      });
    } else {
      return res.status(400).json({
        error: 'Invalid coupon code'
      });
    }
  }

  return res.status(405).json({ error: 'Method not allowed' });
}