from flask import Flask, jsonify, request, session, make_response
from flask_migrate import Migrate
from flask_bcrypt import Bcrypt
from flask_socketio import SocketIO, emit  # Import Flask-SocketIO
from models import db, User, Skill
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
import jwt

# Initialize app and extensions
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///app.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'super_secret_key'

# Initialize SocketIO
socketio = SocketIO(app, cors_allowed_origins="*")  # Allow all origins for WebSocket connections

# More comprehensive CORS configuration
CORS(app, resources={r"/*": {
    "origins": [
        "https://upskillr-nis2.onrender.com", 
        "https://upskillr-1-9xow.onrender.com"  # Ensure both front-end URLs are allowed
    ],
    "methods": ["OPTIONS", "GET", "POST", "PUT", "DELETE"],
    "allow_headers": ["Content-Type", "Authorization"],
    "supports_credentials": True  # Enable support for credentials (cookies)
}})

# Initialize db, bcrypt, and migrate
db.init_app(app)
migrate = Migrate(app, db)
bcrypt = Bcrypt(app)

# Create app function (needed for seeding)
def create_app():
    return app

# Profile endpoint
@app.route('/api/profile', methods=['GET', 'OPTIONS'])
def profile():
    if request.method == 'OPTIONS':
        # Pre-flight response for CORS
        response = make_response()
        response.headers.add('Access-Control-Allow-Origin', 'https://upskillr-1-9xow.onrender.com')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type, Authorization')
        response.headers.add('Access-Control-Allow-Methods', 'GET, OPTIONS')
        response.headers.add('Access-Control-Allow-Credentials', 'true')  # Ensure credentials are allowed
        response.status_code = 200
        return response

    auth_header = request.headers.get('Authorization')
    if not auth_header:
        return jsonify({'error': 'Missing token'}), 401

    token = auth_header.split(" ")[1]
    try:
        decoded = jwt.decode(token, app.config['SECRET_KEY'], algorithms=['HS256'])
        user_id = decoded.get('user_id')
        
        user = User.query.get(user_id)
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        return jsonify({
            'name': user.username,
            'email': user.email,
            'joinedDate': user.created_at.strftime('%Y-%m-%d')
        }), 200
    except Exception as e:
        return jsonify({'error': 'Invalid or expired token', 'details': str(e)}), 401

# CRUD for Skills
@app.route('/skills', methods=['GET', 'POST'])
def skills():
    if request.method == 'GET':
        skills = Skill.query.all()
        return jsonify([{'id': s.id, 'name': s.name, 'user_id': s.user_id} for s in skills]), 200
    
    if request.method == 'POST':
        data = request.get_json()
        name, user_id = data.get('name'), data.get('user_id')
        if not name or not user_id:
            return jsonify({'error': 'Missing required fields'}), 400
        
        skill = Skill(name=name, user_id=user_id)
        db.session.add(skill)
        db.session.commit()
        return jsonify({'message': 'Skill added successfully'}), 201

# Logout
@app.route('/logout', methods=['POST'])
def logout():
    session.clear()
    return jsonify({'message': 'Logged out successfully'}), 200

# Socket.IO event to handle a message from the client
@socketio.on('message')
def handle_message(data):
    print("Received message:", data)
    emit('response', {'message': 'Message received!'})

# Socket.IO event to handle a custom event
@socketio.on('custom_event')
def handle_custom_event(data):
    print("Received custom event data:", data)
    emit('custom_response', {'message': 'Custom event received!'})

if __name__ == '__main__':
    # Ensure the app context is pushed for CLI operations
    with app.app_context():
        socketio.run(app, debug=True, host='0.0.0.0', port=10000)  # Use socketio.run instead of app.run
