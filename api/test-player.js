export default function handler(req, res) {
  return res.status(200).json({ 
    test: true, 
    player_id: 1,
    message: "Test endpoint working" 
  });
}