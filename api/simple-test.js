export default function handler(req, res) {
  return res.status(200).json({ message: "Simple test works", timestamp: Date.now() });
}