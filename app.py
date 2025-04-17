from flask import Flask, render_template, request, redirect, url_for, jsonify
from config import Config
from extensions import db
from models import ChatRoom, Message, Bot, User
from ollama_client import get_chat_response, get_available_models
import os
from flask_migrate import Migrate
import json
import re

app = Flask(__name__)
app.config.from_object(Config)
db.init_app(app)
migrate = Migrate(app, db)

# A helper to retrieve the default model from the environment.
def get_default_model():
    return os.environ.get("DEFAULT_MODEL", "llama3.2")

@app.route('/')
def index():
    rooms = ChatRoom.query.all()
    return render_template('index.html', rooms=rooms)

@app.route('/room/<int:room_id>', methods=['GET', 'POST'])
def room(room_id):
    room = ChatRoom.query.get_or_404(room_id)
    bots = Bot.query.filter_by(room_id=room.id).all()

    # Retrieve user profile information (create a default user if none exists).
    user = User.query.first()
    if not user:
        user = User(username="Guest", bio="", age=None, location="", profile_pic=None)
        db.session.add(user)
        db.session.commit()
    user_profile_info = (
        f"Name: {user.username}; "
        f"Age: {user.age if user.age else 'N/A'}; "
        f"Location: {user.location if user.location else 'N/A'}; "
        f"Bio: {user.bio or 'No bio provided.'}"
    )

    if request.method == 'POST':
        user_msg = request.form['message']
        db.session.add(Message(content=user_msg, sender="User", room=room))
        db.session.commit()

        message_history = []
        # Add system context with user profile and room scenario.
        message_history.append({
            "role": "system",
            "content": f"User Profile: {user_profile_info}"
        })
        message_history.append({
            "role": "system",
            "content": f"Chatroom Scenario: {room.description}"
        })
        if bots:
            bot = bots[0]
            message_history.append({
                "role": "system",
                "content": (
                    f"You are {bot.name}. {bot.persona} Bio: {bot.bio or 'No bio provided.'} "
                    f"From this point forward, ALWAYS respond solely as {bot.name} and never mimic a user."
                )
            })
        else:
            message_history.append({
                "role": "system",
                "content": (
                    "You are a helpful assistant. From this point forward, ALWAYS respond as the assistant and never as the user."
                )
            })
        # Append all previous conversation messages in chronological order.
        conv_messages = Message.query.filter_by(room_id=room.id).order_by(Message.timestamp.asc()).all()
        for msg in conv_messages:
            role = "user" if msg.sender == "User" else "assistant"
            message_history.append({"role": role, "content": msg.content})
        
        # Use the selected bot's model if available; otherwise fall back to the default model.
        default_model = get_default_model()  # <-- New: using the .env default model value.
        chosen_model = bots[0].model if bots else default_model
        
        # Optionally, pass in stored conversation context from the room.
        context = room.conversation_context if room.conversation_context else None
        reply, new_context = get_chat_response(message_history, model=chosen_model, context=context)
        bot_sender = bots[0].name if bots else "Assistant"
        new_message = Message(content=reply, sender=bot_sender, room=room)
        db.session.add(new_message)
        
        # Update the conversation context stored with this room.
        if new_context is not None:
            try:
                room.conversation_context = json.dumps(new_context)
            except Exception:
                room.conversation_context = str(new_context)
        db.session.commit()

        if request.headers.get("X-Requested-With") == "XMLHttpRequest":
            return jsonify({"bot_message": reply, "sender": bot_sender})
        return redirect(url_for('room', room_id=room.id))

    conv_messages = Message.query.filter_by(room_id=room.id).order_by(Message.timestamp.asc()).all()
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
    # Check if a bot already exists for this room
    if Bot.query.filter_by(room_id=room_id).first():
        # Optionally, display a message or simply redirect
        return redirect(url_for('room', room_id=room_id))

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
    
    try:
        models = get_available_models()
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
                "You are a master storyteller and expert character designer. Based on the following input, generate a completely detailed chatbot character description. "
                "Your output must be a valid JSON object with two keys: 'name' and 'bio'. "
                "The 'name' key should contain a creative and memorable name for the bot. "
                "The 'bio' key must contain an extensive and highly detailed character biography, at least 1000 words long. "
                "This biography should include a comprehensive personality profile, an in-depth backstory, detailed physical description, and behavior patterns. "
                "Additionally, incorporate rich background details including the character's hometown, current age, and family history. "
                "Describe their childhood, formative influences, education, and significant life experiences, including any challenges they have overcome and major turning points. "
                "Elaborate on their relationships, personal interests, hobbies, ambitions, and dreams to paint a vivid picture of the character. "
                "Do not include any text outside the JSON object. "
                "Example output: { \"name\": \"Aurora\", \"bio\": \"Aurora, a spirited 29-year-old from the quaint town of Willowbrook, was raised in a loving, tradition-steeped family. Her childhood was filled with adventures in the nearby woods, inspiring a deep curiosity about the natural world. Throughout her formative years, Aurora faced personal challenges that transformed her into a resilient, empathetic soul. Educated in both the arts and sciences, she quickly emerged as a beacon of hope and creativity within her community. Her relationships, marked by both joy and hardship, have further enriched her character, driving her passion for storytelling and artistic expression. Aurora’s journey from a curious child to a wise and inspirational figure is a testament to her enduring strength, compassion, and relentless pursuit of knowledge...\" }.\n\n"
                "User input:"
            )
        },
        {
            "role": "user",
            "content": input_text
        }
    ]
    
    try:
        # New: Use the default model from .env for creation endpoints.
        default_model = get_default_model()
        generated_output = get_chat_response(message_history, model=default_model)
        match = re.search(r'\{.*\}', generated_output, re.DOTALL)
        if not match:
            raise ValueError("Could not find JSON object in the response.")
        
        raw_json = match.group(0)
        
        # Attempt to load and fix control characters.
        data = json.loads(raw_json)
        return jsonify(data)
    except Exception as e:
        # If parsing fails, return the raw output to help with debugging.
        return jsonify({"error": str(e), "raw_output": generated_output}), 500

@app.route('/delete_room/<int:room_id>', methods=['POST'])
def delete_room(room_id):
    # Retrieve the room or return 404 if not found.
    room = ChatRoom.query.get_or_404(room_id)

    # Optionally, delete all associated messages and bots.
    Message.query.filter_by(room_id=room.id).delete()
    Bot.query.filter_by(room_id=room.id).delete()

    # Delete the room.
    db.session.delete(room)
    db.session.commit()
    return redirect(url_for('index'))

@app.route('/delete_bot/<int:bot_id>', methods=['POST'])
def delete_bot(bot_id):
    # Retrieve the bot or return 404 if not found.
    bot = Bot.query.get_or_404(bot_id)
    room_id = bot.room_id  # Save this to redirect back to the room.
    
    # Delete the bot.
    db.session.delete(bot)
    db.session.commit()
    return redirect(url_for('room', room_id=room_id))

@app.route('/generate_room_scenario', methods=['POST'])
def generate_room_scenario():
    title = request.form.get('title', '')
    description = request.form.get('description', '')
    # Combine the fields into one input text.
    input_text = f"Chatroom Title: {title}\nChatroom Description: {description}"
    
    # Build a message history with a system prompt instructing the model
    # to generate ONLY a JSON object with one key: 'scenario'.
    message_history = [
        {
            "role": "system",
            "content": (
                "You are a creative narrative designer. Based on the following chatroom input, generate an immersive, detailed scenario background "
                "that describes an imaginative setting for a chatbot to live in. "
                "Return ONLY a valid JSON object with a single key 'scenario'. Do not include any text before or after the JSON output."
            )
        },
        {
            "role": "user",
            "content": input_text
        }
    ]
    
    try:
        default_model = get_default_model()  # <-- New: use default for room scenario generation.
        generated_output = get_chat_response(message_history, model=default_model).strip()
        
        # If the output doesn't start with '{', try to extract the JSON substring.
        if not generated_output.startswith("{"):
            start = generated_output.find("{")
            end = generated_output.rfind("}")
            if start != -1 and end != -1:
                generated_output = generated_output[start:end+1]
        
        # Fix problematic escape sequences.
        generated_output = generated_output.replace("\\'", "'")
        
        # Ensure balanced braces.
        num_open = generated_output.count("{")
        num_close = generated_output.count("}")
        if num_close < num_open:
            generated_output += "}" * (num_open - num_close)
        
        data = json.loads(generated_output)
        return data["scenario"]
    except Exception as e:
        return jsonify({"error": str(e), "raw_output": generated_output}), 500

@app.route('/get_bot_feeling/<int:room_id>', methods=['GET'])
def get_bot_feeling(room_id):
    room = ChatRoom.query.get_or_404(room_id)
    conv_messages = Message.query.filter_by(room_id=room.id).order_by(Message.timestamp.asc()).all()

    if not conv_messages:
        return jsonify({"feeling": "Neutral"})

    message_history = [
        {
            "role": "system",
            "content": (
                "You are asked to evaluate your current emotional state strictly based on the recent conversation. "
                "Output exactly one word from the following options: happy, sad, neutral, excited, angry. "
                "Do not include any additional text."
            )
        }
    ]

    # Use the last 3 messages from the conversation.
    recent_messages = conv_messages[-3:]
    for msg in recent_messages:
        role = "user" if msg.sender == "User" else "assistant"
        content = msg.content
        if role == "assistant" and len(content) > 200:
            content = content[:200]
        message_history.append({"role": role, "content": content})

    message_history.append({
        "role": "user",
        "content": "Based on the above, what is your current feeling? Answer with one word only."
    })

    print("Message history for bot feeling:", message_history)
    
    try:
        # Retrieve the bot for the room, if available.
        bot = Bot.query.filter_by(room_id=room.id).first()
        chosen_model = bot.model if bot else get_default_model()  # <-- Use selected bot's model if available.
        reply, _ = get_chat_response(message_history, model=chosen_model)
    except Exception as e:
        print("Error during get_chat_response:", e)
        return jsonify({"feeling": "Neutral"})

    feeling = reply.strip()
    print("Raw bot feeling output:", repr(feeling))
    if not feeling:
        feeling = "Neutral"

    return jsonify({"feeling": feeling})

if __name__ == '__main__':
    app.run(debug=True, host="0.0.0.0")
