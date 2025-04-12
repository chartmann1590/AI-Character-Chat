from extensions import db
from datetime import datetime

class ChatRoom(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100))
    description = db.Column(db.String(200))
    messages = db.relationship('Message', backref='room', lazy=True)

class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text)
    sender = db.Column(db.String(50))  # "User" or bot name
    room_id = db.Column(db.Integer, db.ForeignKey('chat_room.id'))
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

class Bot(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    persona = db.Column(db.Text, nullable=False)
    bio = db.Column(db.Text)  # New field: short description of the bot
    profile_pic = db.Column(db.String(100))  # New field: file path or URL for the bot's picture
    model = db.Column(db.String(50), nullable=False, default="llama3.2")  # New field: selected Ollama model
    room_id = db.Column(db.Integer, db.ForeignKey('chat_room.id'), nullable=False)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    age = db.Column(db.Integer)               
    location = db.Column(db.String(100))        
    bio = db.Column(db.Text)                    
    profile_pic = db.Column(db.String(100))     
