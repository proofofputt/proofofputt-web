"""
Example of how to integrate WebSocket support with the existing API.
This demonstrates real-time session updates and notifications.
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import sys

# Add the current directory to sys.path for imports
sys.path.append(os.path.dirname(__file__))

try:
    from websocket_handler import create_websocket_handler
    import data_manager
    WEBSOCKET_AVAILABLE = True
except ImportError as e:
    print(f"WebSocket dependencies not available: {e}")
    WEBSOCKET_AVAILABLE = False

app = Flask(__name__)
CORS(app)

# Initialize WebSocket if available
websocket_handler = None
if WEBSOCKET_AVAILABLE:
    try:
        websocket_handler = create_websocket_handler(app)
        print("WebSocket support enabled")
    except Exception as e:
        print(f"Failed to initialize WebSocket: {e}")
        WEBSOCKET_AVAILABLE = False

@app.route('/session/<int:session_id>/realtime', methods=['POST'])
def update_session_realtime(session_id):
    """
    API endpoint to receive session updates and broadcast them via WebSocket.
    This would be called by the desktop app during active sessions.
    """
    if not WEBSOCKET_AVAILABLE:
        return jsonify({"error": "WebSocket not available"}), 503
    
    try:
        data = request.json
        if not data:
            return jsonify({"error": "No data provided"}), 400
        
        # Validate session exists
        # In production, you'd check session ownership/permissions
        
        # Broadcast the update to all connected clients
        stats_data = {
            'total_putts': data.get('total_putts', 0),
            'total_makes': data.get('total_makes', 0),
            'total_misses': data.get('total_misses', 0),
            'consecutive_makes': data.get('consecutive_makes', 0),
            'session_duration': data.get('session_duration', 0),
            'last_putt_classification': data.get('last_putt_classification'),
            'timestamp': data.get('timestamp')
        }
        
        websocket_handler.broadcast_session_update(session_id, stats_data)
        
        return jsonify({
            "success": True,
            "message": "Session update broadcasted",
            "session_id": session_id
        })
        
    except Exception as e:
        print(f"Error in realtime session update: {e}")
        return jsonify({"error": "Failed to broadcast update"}), 500

@app.route('/player/<int:player_id>/notify', methods=['POST'])
def notify_player(player_id):
    """
    API endpoint to send notifications to specific players via WebSocket.
    """
    if not WEBSOCKET_AVAILABLE:
        return jsonify({"error": "WebSocket not available"}), 503
    
    try:
        data = request.json
        if not data or 'message' not in data:
            return jsonify({"error": "No message provided"}), 400
        
        notification = {
            'type': data.get('type', 'info'),
            'title': data.get('title', 'Notification'),
            'message': data['message'],
            'timestamp': data.get('timestamp'),
            'action_url': data.get('action_url')
        }
        
        websocket_handler.send_notification(player_id, notification)
        
        return jsonify({
            "success": True,
            "message": "Notification sent",
            "player_id": player_id
        })
        
    except Exception as e:
        print(f"Error sending notification: {e}")
        return jsonify({"error": "Failed to send notification"}), 500

@app.route('/websocket/status', methods=['GET'])
def websocket_status():
    """Check WebSocket availability and status."""
    return jsonify({
        "websocket_enabled": WEBSOCKET_AVAILABLE,
        "status": "ready" if WEBSOCKET_AVAILABLE else "disabled",
        "features": [
            "real-time session updates",
            "player notifications",
            "duel updates"
        ] if WEBSOCKET_AVAILABLE else []
    })

if __name__ == '__main__':
    # For development only
    if WEBSOCKET_AVAILABLE and websocket_handler:
        websocket_handler.socketio.run(app, debug=True, host='0.0.0.0', port=5001)
    else:
        app.run(debug=True, host='0.0.0.0', port=5001)