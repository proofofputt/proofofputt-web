export default function handler(req, res) {
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type, Authorization');
  
  if (req.method === 'OPTIONS') {
    return res.status(200).end();
  }

  const { playerId } = req.query;

  if (req.method === 'GET') {
    return res.status(200).json({
      notifications: [
        { 
          id: 1, 
          type: "duel_challenge", 
          title: "New Duel Challenge", 
          message: "Tiger challenged you to a putting duel!",
          read: false,
          created_at: "2025-08-30T09:00:00Z"
        },
        { 
          id: 2, 
          type: "league_invite", 
          title: "League Invitation", 
          message: "You've been invited to join Masters Champions league",
          read: false,
          created_at: "2025-08-30T08:30:00Z"
        },
        { 
          id: 3, 
          type: "achievement", 
          title: "New Achievement!", 
          message: "You've achieved a 10-putt streak!",
          read: true,
          created_at: "2025-08-29T20:15:00Z"
        }
      ],
      unread_count: 2
    });
  }

  if (req.method === 'POST') {
    const { notification_id } = req.body;
    return res.status(200).json({
      success: true,
      message: "Notification marked as read"
    });
  }

  return res.status(405).json({ error: 'Method not allowed' });
}