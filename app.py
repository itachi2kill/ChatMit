@socketio.on('send_message')
def handle_message(data):
    sender_id = request.sid
    sender_info = users.get(sender_id)
    
    if not sender_info:
        return 

    sender_name = sender_info['name']
    room_code = sender_info['room']
    original_text = data['message']

    # Find ONLY users in the same room
    recipients = [sid for sid, info in users.items() if info['room'] == room_code and sid != sender_id]

    # Loop through recipients in the same room
    for recipient_id in recipients:
        recipient_data = users[recipient_id]
        target_lang = recipient_data['lang']
        
        # Default to original text in case translation fails
        translated_text = original_text 

        try:
            # Try to translate
            translated_text = GoogleTranslator(source='auto', target=target_lang).translate(original_text)
        except Exception as e:
            # If it fails, just print error but DON'T stop the message
            print(f"Error translating for {recipient_id}: {e}")

        # --- MOVED THIS OUTSIDE THE TRY BLOCK ---
        # Now the message sends even if translation failed
        emit('receive_message', {
            'original': original_text,
            'translation': translated_text,
            'sender': sender_name,
            'lang': target_lang
        }, room=recipient_id)
