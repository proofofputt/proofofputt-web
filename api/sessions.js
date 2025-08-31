
import { getDb } from './db.js';
import withCors from './middleware/cors.js';

async function sessionsHandler(req, res) {
  const { player_id } = req.query;

  if (!player_id) {
    return res.status(400).json({ error: 'player_id is required' });
  }

  if (req.method === 'GET') {
    const db = getDb();
    try {
      const query = 'SELECT * FROM sessions WHERE player_id = $1 ORDER BY start_time DESC';
      const result = await db.query(query, [player_id]);
      const sessions = result.rows;

      return res.status(200).json(sessions);
    } catch (error) {
      console.error('Error fetching session data:', error);
      return res.status(500).json({ error: 'Internal server error' });
    }
  }

  return res.status(405).json({ error: 'Method not allowed' });
}

export default withCors(sessionsHandler);
