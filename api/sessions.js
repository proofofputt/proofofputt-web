export default function handler(req, res) {
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type, Authorization');
  
  if (req.method === 'OPTIONS') {
    return res.status(200).end();
  }

  if (req.method === 'POST') {
    const { player_id, session_type, putts_data } = req.body;
    
    return res.status(200).json({
      success: true,
      session: {
        id: Date.now(),
        player_id,
        session_type: session_type || "practice",
        created_at: new Date().toISOString(),
        status: "active"
      },
      message: "Session started successfully"
    });
  }

  if (req.method === 'PUT') {
    const { session_id, putts_data, end_session } = req.body;
    
    if (end_session) {
      return res.status(200).json({
        success: true,
        session: {
          id: session_id,
          status: "completed",
          ended_at: new Date().toISOString(),
          final_stats: {
            total_putts: 45,
            makes: 33,
            make_percentage: 73.3,
            best_streak: 8
          }
        },
        message: "Session completed successfully"
      });
    }

    return res.status(200).json({
      success: true,
      message: "Session updated successfully"
    });
  }

  return res.status(405).json({ error: 'Method not allowed' });
}