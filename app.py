from flask import Flask, render_template, request
from flask_socketio import SocketIO, emit, join_room, leave_room
from deep_translator import GoogleTranslator

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app, cors_allowed_origins="*")

# Store user data: { socket_id: { 'name': 'Rahul', 'lang': 'en', 'room': '123' } }
users = {}

@app.route('/')
def index():
    return render_template('index.html')

@socketio.on('connect')
def handle_connect():
    print(f"User Connected: {request.sid}")

@socketio.on('disconnect')
def handle_disconnect():
    user = users.get(request.sid)
    if user:
        room = user['room']
        name = user['name']
        leave_room(room)
        del users[request.sid]
        # Notify others in that room
        emit('system_message', {'message': f'{name} has left the chat.'}, to=room)

@socketio.on('join_chat')
def handle_join(data):
    username = data.get('name', 'Anonymous')
    room_code = data.get('room', 'default')
    lang = data.get('lang', 'en')
    
    # Save user info
    users[request.sid] = { 'name': username, 'lang': lang, 'room': room_code }
    
    # Connect user to the specific room
    join_room(room_code)
    
    # Broadcast ONLY to that room
    emit('system_message', {'message': f'{username} has joined room {room_code}.'}, to=room_code)

@socketio.on('send_message')
def handle_message(data):
    sender_id = request.sid
    sender_info = users.get(sender_id)
    
    if not sender_info:
        return 

    sender_name = sender_info['name']
    room_code = sender_info['room']
    original_text = data['message']

    # Find ONLY users in the same room (excluding sender)
    recipients = [sid for sid, info in users.items() if info['room'] == room_code and sid != sender_id]

    # Loop through recipients in the same room
    for recipient_id in recipients:
        recipient_data = users[recipient_id]
        target_lang = recipient_data['lang']
        
        # 1. Fallback: Use original text first
        translated_text = original_text 

        # 2. Try to translate
        try:
            translated_text = GoogleTranslator(source='auto', target=target_lang).translate(original_text)
        except Exception as e:
            # If translation fails, we print the error but CONTINUE to send the original text
            print(f"Error translating for {recipient_id}: {e}")

        # 3. Send message (This is now OUTSIDE the try block)
        emit('receive_message', {
            'original': original_text,
            'translation': translated_text,
            'sender': sender_name,
            'lang': target_lang
        }, room=recipient_id)

if __name__ == '__main__':
    print("✅ SERVER RUNNING: http://localhost:5001")
    socketio.run(app, host='0.0.0.0', port=5001)
