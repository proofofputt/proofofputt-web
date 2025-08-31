export default function handler(req, res) {
  // Set CORS headers for all requests
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type, Authorization');
  
  if (req.method === 'OPTIONS') {
    return res.status(200).end();
  }

  const { method } = req;
  
  if (method === 'GET') {
    const { player_id } = req.query;
    
    // Mock data structure that matches what LeaguesPage expects
    return res.status(200).json({
      my_leagues: [
        {
          league_id: 1,
          name: "Masters Champions",
          description: "Elite putting league for advanced players",
          member_count: 24,
          privacy_type: "private",
          status: "active",
          can_join: false
        }
      ],
      public_leagues: [
        {
          league_id: 2,
          name: "Weekend Warriors",
          description: "Casual league for weekend practice sessions",
          member_count: 12,
          privacy_type: "public",
          status: "active",
          can_join: true
        }
      ],
      pending_invites: []
    });
  }
  
  if (method === 'POST') {
    const { name, description, privacy_type } = req.body;
    const newLeagueId = Date.now();
    
    // Simulate creating a new league and return it
    return res.status(200).json({ 
      success: true, 
      league: { 
        league_id: newLeagueId,
        name: name || "New League",
        description: description || "A newly created league",
        member_count: 1,
        privacy_type: privacy_type || "private",
        status: "active",
        can_join: false
      }
    });
  }

  return res.status(405).json({ error: 'Method not allowed' });
}