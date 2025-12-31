# 1. ADD THESE TWO LINES AT THE VERY TOP
import eventlet
eventlet.monkey_patch()

from flask import Flask, render_template, request
from flask_socketio import SocketIO, emit, join_room, leave_room
from deep_translator import GoogleTranslator
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'

# 2. ALLOW ALL ORIGINS FOR RENDER
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='eventlet')

users = {}

@app.route('/')
def index():
    return render_template('index.html')

@socketio.on('connect')
def handle_connect():
    print(f"✅ NEW CONNECTION: {request.sid}")

@socketio.on('disconnect')
def handle_disconnect():
    user = users.get(request.sid)
    if user:
        room = user['room']
        name = user['name']
        leave_room(room)
        del users[request.sid]
        print(f"❌ DISCONNECTED: {name}")
        emit('system_message', {'message': f'{name} has left the chat.'}, to=room)

@socketio.on('join_chat')
def handle_join(data):
    username = data.get('name', 'Anonymous')
    room_code = data.get('room', 'default')
    lang = data.get('lang', 'en')
    
    users[request.sid] = { 'name': username, 'lang': lang, 'room': room_code }
    join_room(room_code)
    
    # Broadcast to room so you know they are there
    emit('system_message', {'message': f'{username} has joined room {room_code}.'}, to=room_code)
    print(f"📢 {username} joined Room {room_code}")

@socketio.on('send_message')
def handle_message(data):
    sender_id = request.sid
    sender_info = users.get(sender_id)
    
    if not sender_info:
        # If server forgot user, force them to refresh
        print(f"⚠️ ERROR: User {sender_id} not found in memory.")
        return 

    sender_name = sender_info['name']
    room_code = sender_info['room']
    original_text = data['message']

    recipients = [sid for sid, info in users.items() if info['room'] == room_code and sid != sender_id]

    # DEBUG LOG
    print(f"📨 Message from {sender_name} to {len(recipients)} people in Room {room_code}")

    for recipient_id in recipients:
        recipient_data = users[recipient_id]
        target_lang = recipient_data['lang']
        
        # Default fallback
        translated_text = original_text 

        try:
            translated_text = GoogleTranslator(source='auto', target=target_lang).translate(original_text)
        except Exception as e:
            print(f"⚠️ Translation Error: {e}")

        # Send Message OUTSIDE the try block
        emit('receive_message', {
            'original': original_text,
            'translation': translated_text,
            'sender': sender_name,
            'lang': target_lang
        }, room=recipient_id)

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=int(os.environ.get("PORT", 5001)))
