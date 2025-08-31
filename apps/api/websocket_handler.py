"""
WebSocket handler for real-time updates in Proof of Putt.
Supports real-time session updates, duels, and notifications.
"""

from flask_socketio import SocketIO, emit, join_room, leave_room
import json
import logging

logger = logging.getLogger(__name__)

class WebSocketHandler:
    def __init__(self, app):
        """Initialize WebSocket handler with Flask app."""
        self.socketio = SocketIO(
            app,
            cors_allowed_origins="*",
            logger=True,
            engineio_logger=True
        )
        self.setup_handlers()
    
    def setup_handlers(self):
        """Set up all WebSocket event handlers."""
        
        @self.socketio.on('connect')
        def handle_connect():
            """Handle client connection."""
            logger.info(f'Client connected: {request.sid}')
            emit('connected', {'status': 'Connected to Proof of Putt WebSocket'})
        
        @self.socketio.on('disconnect')
        def handle_disconnect():
            """Handle client disconnection."""
            logger.info(f'Client disconnected: {request.sid}')
        
        @self.socketio.on('join_session')
        def handle_join_session(data):
            """Join a session room for real-time updates."""
            try:
                session_id = data.get('session_id')
                player_id = data.get('player_id')
                
                if not session_id or not player_id:
                    emit('error', {'message': 'Missing session_id or player_id'})
                    return
                
                room = f'session_{session_id}'
                join_room(room)
                
                logger.info(f'Player {player_id} joined session {session_id}')
                emit('session_joined', {
                    'session_id': session_id,
                    'room': room,
                    'status': 'joined'
                })
                
                # Notify others in the room
                emit('player_joined', {
                    'player_id': player_id,
                    'session_id': session_id
                }, room=room, include_self=False)
                
            except Exception as e:
                logger.error(f'Error joining session: {e}')
                emit('error', {'message': 'Failed to join session'})
        
        @self.socketio.on('leave_session')
        def handle_leave_session(data):
            """Leave a session room."""
            try:
                session_id = data.get('session_id')
                player_id = data.get('player_id')
                
                if session_id:
                    room = f'session_{session_id}'
                    leave_room(room)
                    
                    logger.info(f'Player {player_id} left session {session_id}')
                    emit('session_left', {'session_id': session_id})
                    
                    # Notify others in the room
                    emit('player_left', {
                        'player_id': player_id,
                        'session_id': session_id
                    }, room=room)
                    
            except Exception as e:
                logger.error(f'Error leaving session: {e}')
        
        @self.socketio.on('session_update')
        def handle_session_update(data):
            """Handle session progress updates."""
            try:
                session_id = data.get('session_id')
                update_data = data.get('data', {})
                
                if not session_id:
                    emit('error', {'message': 'Missing session_id'})
                    return
                
                room = f'session_{session_id}'
                
                # Broadcast the update to all clients in the session
                emit('session_progress', {
                    'session_id': session_id,
                    'timestamp': update_data.get('timestamp'),
                    'stats': {
                        'total_putts': update_data.get('total_putts', 0),
                        'total_makes': update_data.get('total_makes', 0),
                        'consecutive_makes': update_data.get('consecutive_makes', 0),
                        'session_duration': update_data.get('session_duration', 0)
                    },
                    'last_putt': update_data.get('last_putt')
                }, room=room)
                
            except Exception as e:
                logger.error(f'Error handling session update: {e}')
                emit('error', {'message': 'Failed to process session update'})
    
    def broadcast_session_update(self, session_id, stats_data):
        """
        Broadcast session updates to all connected clients.
        Can be called from other parts of the application.
        """
        try:
            room = f'session_{session_id}'
            self.socketio.emit('session_progress', {
                'session_id': session_id,
                'stats': stats_data,
                'timestamp': stats_data.get('timestamp')
            }, room=room)
            
        except Exception as e:
            logger.error(f'Error broadcasting session update: {e}')
    
    def broadcast_duel_update(self, duel_id, duel_data):
        """
        Broadcast duel updates to participants.
        """
        try:
            room = f'duel_{duel_id}'
            self.socketio.emit('duel_update', {
                'duel_id': duel_id,
                'data': duel_data
            }, room=room)
            
        except Exception as e:
            logger.error(f'Error broadcasting duel update: {e}')
    
    def send_notification(self, player_id, notification):
        """
        Send notification to specific player.
        """
        try:
            room = f'player_{player_id}'
            self.socketio.emit('notification', notification, room=room)
            
        except Exception as e:
            logger.error(f'Error sending notification: {e}')

def create_websocket_handler(app):
    """Factory function to create and return WebSocket handler."""
    return WebSocketHandler(app)