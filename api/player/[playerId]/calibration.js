
import { getDb } from '../db.js';

export default async function handler(req, res) {
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Credentials', 'true');
  res.setHeader('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type, Authorization');

  if (req.method === 'OPTIONS') {
    return res.status(200).end();
  }

  const { playerId } = req.query;
  const playerIdNum = parseInt(playerId);

  if (isNaN(playerIdNum)) {
    return res.status(400).json({ error: 'Invalid Player ID' });
  }

  const db = getDb();

  if (req.method === 'GET') {
    try {
      const query = 'SELECT * FROM calibrations WHERE player_id = $1';
      const result = await db.query(query, [playerIdNum]);

      if (result.rows.length > 0) {
        return res.status(200).json(result.rows[0]);
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
    } catch (error) {
      console.error('Error fetching calibration data:', error);
      return res.status(500).json({ error: 'Internal server error' });
    }
  }

  if (req.method === 'POST' || req.method === 'PUT') {
    try {
      const {
        is_calibrated,
        calibration_date,
        camera_index,
        roi_coordinates,
        calibration_quality,
        notes,
        desktop_connected
      } = req.body;

      if (is_calibrated && !roi_coordinates) {
        return res.status(400).json({ error: 'ROI coordinates required when is_calibrated is true' });
      }

      const query = `
        INSERT INTO calibrations (player_id, is_calibrated, calibration_date, camera_index, roi_coordinates, calibration_quality, notes, desktop_connected, last_updated)
        VALUES ($1, $2, $3, $4, $5, $6, $7, $8, NOW())
        ON CONFLICT (player_id)
        DO UPDATE SET
          is_calibrated = EXCLUDED.is_calibrated,
          calibration_date = EXCLUDED.calibration_date,
          camera_index = EXCLUDED.camera_index,
          roi_coordinates = EXCLUDED.roi_coordinates,
          calibration_quality = EXCLUDED.calibration_quality,
          notes = EXCLUDED.notes,
          desktop_connected = EXCLUDED.desktop_connected,
          last_updated = NOW()
        RETURNING *;
      `;

      const values = [
        playerIdNum,
        is_calibrated || false,
        calibration_date || new Date().toISOString(),
        camera_index || 0,
        roi_coordinates || null,
        calibration_quality || 'unknown',
        notes || 'Calibration updated',
        desktop_connected || false
      ];

      const result = await db.query(query, values);

      return res.status(200).json({
        success: true,
        message: 'Calibration saved successfully',
        ...result.rows[0]
      });
    } catch (error) {
      console.error('Calibration update error:', error);
      return res.status(500).json({
        error: 'Failed to update calibration data',
        details: error.message
      });
    }
  }

  return res.status(405).json({ error: 'Method not allowed' });
}
