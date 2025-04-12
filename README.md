# Character-AI Clone

A Python Flask-based web application that mimics the functionality of Character.AI, enabling engaging, interactive conversations with AI-driven characters. This project leverages local AI models powered by Ollama for generating dynamic and context-aware interactions.

---

## 🚀 Features

- **Interactive AI Chat**: Engage in lifelike conversations with customizable AI characters.
- **Model Flexibility**: Easily select and save different Ollama-powered models per character.
- **Persistent Conversations**: Maintain chat history for continuity and context.
- **Markdown Support**: Rich, formatted text responses for better readability.
- **Reset Conversations**: Clear and restart interactions easily.

---

## 🛠️ Technologies Used

- **Python** with Flask
- **Ollama** (Local AI models)
- **Docker** for containerization
- **SQLite** database for persistence
- **Markdown parsing** for chat responses

---

## 📥 Installation

### 🐍 Python Setup

1. **Clone the repository**:

   ```bash
   git clone https://github.com/chartmann1590/AI-Character-Chat.git
   cd AI-Character-Chat
   ```

2. **Create and activate a virtual environment**:

   ```bash
   python -m venv venv
   source venv/bin/activate  # Linux/Mac
   .\venv\Scripts\activate  # Windows
   ```

3. **Install dependencies**:

   ```bash
   pip install -r requirements.txt
   ```

4. **Setup `.env` configuration**:

   ```bash
   cp .env.example .env
   ```
   Adjust `.env` settings as required.

5. **Run the application**:

   ```bash
   python app.py
   ```

Visit [http://localhost:5000](http://localhost:5000) in your web browser.

---

### 🐳 Docker Setup

1. **Build the Docker image**:

   ```bash
   docker build -t character-ai-clone .
   ```

2. **Run the Docker container**:

   ```bash
   docker run -d -p 5000:5000 --name character-ai character-ai-clone
   ```

Access the app at [http://localhost:5000](http://localhost:5000).

---

## 🌟 Usage

- **Creating AI Characters**: Add new AI bots through the collapsible form.
- **Chatting**: Engage with AI bots and see dynamic, Markdown-formatted responses.
- **Model Management**: Select models from each bot's profile settings for personalized interactions.
- **Reset Conversations**: Click the reset button to clear the current chat history.

---

## 📂 Project Structure

```
AI-Character-Chat/
├── instance/
│   └── app.db
├── migrations/
│   ├── versions/
│   ├── alembic.ini
│   ├── env.py
│   └── script.py.mako
├── static/
│   ├── css/
│   │   └── styles.css
│   ├── js/
│   └── uploads/
├── templates/
│   ├── add_bot.html
│   ├── base.html
│   ├── chatroom.html
│   ├── index.html
│   └── profile.html
├── .dockerignore
├── .env.example
├── .gitignore
├── app.py
├── config.py
├── Dockerfile
├── extensions.py
├── models.py
├── ollama_client.py
├── README.md
└── requirements.txt
```

---

## 🔐 Environment Variables

Create a `.env` file based on `.env.example` and configure your settings such as:

- `OLLAMA_API_URL`: URL for your local Ollama API instance
- `SECRET_KEY`: Flask session secret key

---

## 📝 Contributing

Pull requests and feature suggestions are welcome. Please open an issue first to discuss significant changes.

---

## 📄 License

Distributed under the MIT License. See `LICENSE` for more information.

