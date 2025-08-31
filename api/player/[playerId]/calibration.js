export default function handler(req, res) {
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Credentials', 'true');
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

    // For demo purposes, we'll use a simple in-memory store
    // In production, this would read from a database or file system
    const calibrationKey = `calibration_${playerId}`;
    const storedCalibration = global[calibrationKey];
    
    if (storedCalibration) {
      return res.status(200).json(storedCalibration);
    } else {
      return res.status(200).json({
        is_calibrated: false,
        calibration_date: null,
        camera_index: null,
        roi_coordinates: null,
        calibration_quality: null,
        notes: 'No calibration found. Please connect desktop app and calibrate camera.',
        desktop_connected: false
      });
    }
  }

  if (req.method === 'POST') {
    if (!playerId) {
      return res.status(400).json({ error: 'Player ID is required' });
    }

    // Handle calibration creation/update
    const calibrationData = req.body;
    
    // Store calibration data (in production, this would be saved to database)
    const calibrationKey = `calibration_${playerId}`;
    const updatedCalibration = {
      is_calibrated: calibrationData.is_calibrated || false,
      calibration_date: calibrationData.calibration_date || new Date().toISOString(),
      camera_index: calibrationData.camera_index || 0,
      roi_coordinates: calibrationData.roi_coordinates || null,
      calibration_quality: calibrationData.calibration_quality || 'unknown',
      notes: calibrationData.notes || 'Calibration updated',
      desktop_connected: calibrationData.desktop_connected || false,
      last_updated: new Date().toISOString()
    };
    
    // Store in global memory (demo only)
    global[calibrationKey] = updatedCalibration;
    
    return res.status(200).json({
      message: 'Calibration saved successfully',
      ...updatedCalibration
    });
  }

  return res.status(405).json({ error: 'Method not allowed' });
}