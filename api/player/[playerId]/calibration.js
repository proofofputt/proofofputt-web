export default function handler(req, res) {
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type, Authorization');
  
  if (req.method === 'OPTIONS') {
    return res.status(200).end();
  }

  const { playerId } = req.query;

  if (req.method === 'GET') {
    if (!playerId) {
      return res.status(400).json({ error: 'Player ID is required' });
    }

    // Mock calibration status based on player ID
    // In production, this would check desktop app's calibration files
    const hasCalibration = parseInt(playerId) === 1; // Player 1 has calibration for demo
    
    if (hasCalibration) {
      return res.status(200).json({
        is_calibrated: true,
        calibration_date: '2025-08-30T12:00:00Z',
        camera_index: 0,
        roi_coordinates: {
          x: 100,
          y: 100, 
          width: 300,
          height: 200
        },
        calibration_quality: 'good',
        notes: 'Optimal lighting conditions'
      });
    } else {
      return res.status(200).json({
        is_calibrated: false,
        calibration_date: null,
        camera_index: null,
        roi_coordinates: null,
        calibration_quality: null,
        notes: 'No calibration found. Please calibrate camera first.'
      });
    }
  }

  if (req.method === 'POST') {
    // Handle calibration creation/update
    const calibrationData = req.body;
    
    return res.status(200).json({
      message: 'Calibration saved successfully',
      is_calibrated: true,
      calibration_date: new Date().toISOString(),
      ...calibrationData
    });
  }

  return res.status(405).json({ error: 'Method not allowed' });
}