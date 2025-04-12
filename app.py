from flask import Flask, render_template, request, redirect, url_for, jsonify
from config import Config
from extensions import db
from models import ChatRoom, Message, Bot, User
from ollama_client import get_chat_response, get_available_models
import os
from flask_migrate import Migrate

app = Flask(__name__)
app.config.from_object(Config)
db.init_app(app)
migrate = Migrate(app, db)

@app.route('/')
def index():
    rooms = ChatRoom.query.all()
    return render_template('index.html', rooms=rooms)

@app.route('/room/<int:room_id>', methods=['GET', 'POST'])
def room(room_id):
    room = ChatRoom.query.get_or_404(room_id)
    bots = Bot.query.filter_by(room_id=room.id).all()

    # Retrieve user profile information.
    user = User.query.first()
    if not user:
        user = User(username="Guest", bio="", age=None, location="", profile_pic=None)
        db.session.add(user)
        db.session.commit()
    user_profile_info = (f"Name: {user.username}; "
                         f"Age: {user.age if user.age else 'N/A'}; "
                         f"Location: {user.location if user.location else 'N/A'}; "
                         f"Bio: {user.bio or 'No bio provided.'}")
    
    if request.method == 'POST':
        user_msg = request.form['message']
        db.session.add(Message(content=user_msg, sender="User", room=room))
        db.session.commit()

        message_history = []
        # Add the user profile context.
        message_history.append({
            "role": "system",
            "content": f"User Profile: {user_profile_info}"
        })
        # Add the bot persona as a system message if a bot is defined.
        if bots:
            bot = bots[0]
            message_history.append({
                "role": "system",
                "content": f"You are {bot.name}. {bot.persona} Bio: {bot.bio or 'No bio provided.'}"
            })
        else:
            message_history.append({
                "role": "system",
                "content": "You are a helpful assistant."
            })
        # Append previous conversation messages.
        conv_messages = Message.query.filter_by(room_id=room.id).order_by(Message.timestamp.asc()).all()
        for msg in conv_messages:
            role = "user" if msg.sender == "User" else "assistant"
            message_history.append({"role": role, "content": msg.content})
        
        chosen_model = bots[0].model if bots else "llama3.2"
        reply = get_chat_response(message_history, model=chosen_model)
        bot_sender = bots[0].name if bots else "Assistant"
        new_message = Message(content=reply, sender=bot_sender, room=room)
        db.session.add(new_message)
        db.session.commit()

        if request.headers.get("X-Requested-With") == "XMLHttpRequest":
            return jsonify({"bot_message": reply, "sender": bot_sender})
        return redirect(url_for('room', room_id=room.id))
    
    conv_messages = Message.query.filter_by(room_id=room.id).order_by(Message.timestamp.asc()).all()
    # Poll for available models to populate the edit modal
    available_models = get_available_models()
    return render_template('chatroom.html', room=room, messages=conv_messages, bots=bots, user=user, models=available_models)

@app.route('/room/<int:room_id>/reset', methods=['POST'])
def reset_chat(room_id):
    room = ChatRoom.query.get_or_404(room_id)
    # Delete all messages for the room.
    Message.query.filter_by(room_id=room.id).delete()
    db.session.commit()
    return redirect(url_for('room', room_id=room.id))

@app.route('/edit_bot/<int:bot_id>', methods=['POST'])
def edit_bot(bot_id):
    bot = Bot.query.get_or_404(bot_id)
    new_model = request.form.get('model')
    if new_model:
        bot.model = new_model
        db.session.commit()
    return redirect(url_for('room', room_id=bot.room_id))

@app.route('/add_room', methods=['POST'])
def add_room():
    title = request.form['title']
    description = request.form['description']
    db.session.add(ChatRoom(title=title, description=description))
    db.session.commit()
    return redirect(url_for('index'))

@app.route('/add_bot/<int:room_id>', methods=['GET', 'POST'])
def add_bot(room_id):
    if request.method == 'POST':
        name = request.form['name']
        persona = request.form['persona']
        bio = request.form.get('bio', '')
        model = request.form['model']
        profile_pic = request.files.get('profile_pic')
        filename = None
        if profile_pic:
            from werkzeug.utils import secure_filename
            filename = secure_filename(profile_pic.filename)
            upload_path = os.path.join(app.root_path, 'static', 'uploads', filename)
            profile_pic.save(upload_path)
        new_bot = Bot(name=name, persona=persona, bio=bio, profile_pic=filename, model=model, room_id=room_id)
        db.session.add(new_bot)
        db.session.commit()
        return redirect(url_for('room', room_id=room_id))
    
    # GET: poll for available models
    try:
        models = get_available_models()
        # models is a list of objects; we'll extract the name from each.
        # For example, each model object might have a "name" key.
    except Exception as e:
        models = []
        print("Error retrieving models:", e)
    
    return render_template('add_bot.html', room_id=room_id, models=models)

@app.route('/profile', methods=['GET', 'POST'])
def profile():
    # Retrieve the first user or create one if not existing.
    user = User.query.first()
    if not user:
        user = User(username="Guest", bio="", age=None, location="", profile_pic=None)
        db.session.add(user)
        db.session.commit()
    if request.method == 'POST':
        user.username = request.form['username']
        user.bio = request.form['bio']
        # Update numeric age; if not provided, keep it as None.
        age = request.form.get('age')
        user.age = int(age) if age and age.isdigit() else None
        user.location = request.form['location']
        profile_pic = request.files.get('profile_pic')
        if profile_pic:
            from werkzeug.utils import secure_filename
            filename = secure_filename(profile_pic.filename)
            upload_path = os.path.join(app.root_path, 'static', 'uploads', filename)
            profile_pic.save(upload_path)
            user.profile_pic = filename
        db.session.commit()
        return redirect(url_for('profile'))
    return render_template('profile.html', user=user)

@app.route('/generate_bot_bio', methods=['POST'])
def generate_bot_bio():
    input_text = request.form.get('input_text')
    if not input_text:
        return jsonify({"error": "No input provided."}), 400

    # Build a message history with a system prompt instructing a JSON output.
    message_history = [
        {
            "role": "system",
            "content": (
                "You are an expert character designer. Generate a complete chatbot character description based on the following input. "
                "Your output must be a valid JSON object with two keys: 'name' and 'bio'. Use 'name' for a creative bot name and 'bio' for a detailed character biography, "
                "including personality, backstory, appearance, and behavior. Do not include any additional text. "
                "Example output: { \"name\": \"Jasmine\", \"bio\": \"A wise and mysterious girl who provides deep insights...\" }.\n\n"
                "User input:"
            )
        },
        {
            "role": "user",
            "content": input_text
        }
    ]
    
    try:
        generated_output = get_chat_response(message_history, model="llama3.2")
        import json
        data = json.loads(generated_output)
        return jsonify(data)
    except Exception as e:
        # If parsing fails, return the raw output to help with debugging.
        return jsonify({"error": str(e), "raw_output": generated_output}), 500

if __name__ == '__main__':
    app.run(debug=True, host="0.0.0.0")
