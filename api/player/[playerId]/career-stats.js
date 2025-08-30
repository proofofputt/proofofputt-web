export default function handler(req, res) {
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'GET');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type');

  if (req.method === 'GET') {
    return res.status(200).json({
      total_sessions: 847,
      total_putts: 12483,
      made_putts: 9286,
      make_percentage: 74.4,
      average_session_length: 45.2,
      best_streak: 23,
      current_streak: 8,
      sessions_this_week: 12,
      putts_this_week: 394,
      improvement_trend: "positive"
    });
  }

  return res.status(405).json({ error: 'Method not allowed' });
}