
import { getDb } from './db.js';

export default async function handler(req, res) {
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type, Authorization');

  if (req.method === 'OPTIONS') {
    return res.status(200).end();
  }

  const { type = 'global', timeframe = 'weekly' } = req.query;

  if (req.method === 'GET') {
    const db = getDb();
    try {
      const topMakesQuery = `
        SELECT p.name, ps.total_makes as value, RANK() OVER (ORDER BY ps.total_makes DESC) as rank
        FROM player_stats ps
        JOIN players p ON ps.player_id = p.player_id
        ORDER BY ps.total_makes DESC
        LIMIT 10;
      `;
      const topMakesResult = await db.query(topMakesQuery);
      const topMakes = topMakesResult.rows;

      return res.status(200).json({
        top_makes: topMakes,
        top_streaks: [], // TODO: Implement this leaderboard
        top_makes_per_minute: [], // TODO: Implement this leaderboard
        fastest_21: [], // TODO: Implement this leaderboard
        type,
        timeframe,
        updated_at: new Date().toISOString()
      });
    } catch (error) {
      console.error('Error fetching leaderboard data:', error);
      return res.status(500).json({ error: 'Internal server error' });
    }
  }

  return res.status(405).json({ error: 'Method not allowed' });
}
