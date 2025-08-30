export default function handler(req, res) {
  return res.status(200).json({ unread_count: 2, player_id: 1 });
}