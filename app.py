import os
import threading
from flask import Flask, request, jsonify, render_template_string, session, redirect, url_for
from huggingface_hub import hf_hub_download
from llama_cpp import Llama

app = Flask(__name__)
app.secret_key = "ouroboros_secret_key_segura"

# --- CONFIGURACIÓN DE USUARIOS AUTORIZADOS ---
USERS = {
    "Ouro": "090411",
    "Ale": "Dalessio",
    "Dulce": "cornuda"
}
# ---------------------------------------------

llm = None
model_status = "Descargando modelo ligero en segundo plano..."

def load_model():
    global llm, model_status
    try:
        # Usamos el modelo Qwen 2.5 de 1.5B, mucho más ligero para Render Free Tier
        model_path = hf_hub_download(
            repo_id="Qwen/Qwen2.5-1.5B-Instruct-GGUF",
            filename="qwen2.5-1.5b-instruct-q4_k_m.gguf"
        )
        llm = Llama(
            model_path=model_path,
            n_ctx=2048,
            verbose=False
        )
        model_status = "Listo"
    except Exception as e:
        model_status = f"Error: {str(e)}"

# Iniciar la descarga del modelo en segundo plano
threading.Thread(target=load_model).start()

LOGIN_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head>
    <title>Login - Ouroboros IA</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        body { font-family: sans-serif; max-width: 400px; margin: 100px auto; padding: 20px; background: #121212; color: #e0e0e0; border-radius: 8px; border: 1px solid #333; }
        input, button { width: 100%; padding: 12px; box-sizing: border-box; margin-top: 10px; border-radius: 5px; border: 1px solid #444; background: #222; color: #fff; }
        button { background: #388e3c; color: white; border: none; font-weight: bold; cursor: pointer; }
        .error { color: #ef5350; font-size: 0.9em; margin-top: 5px; }
    </style>
</head>
<body>
    <h2>Iniciar Sesión - Ouroboros IA</h2>
    <form method="POST">
        <input type="text" name="username" placeholder="Usuario (Ouro, Ale, Dulce)" required autocomplete="username">
        <input type="password" name="password" placeholder="Contraseña" required autocomplete="current-password">
        <button type="submit">Entrar</button>
        {% if error %}<div class="error">{{ error }}</div>{% endif %}
    </form>
</body>
</html>
'''

CHAT_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head>
    <title>Ouroboros IA</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        body { font-family: sans-serif; max-width: 600px; margin: 20px auto; padding: 0 10px; background: #121212; color: #e0e0e0; }
        .header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px; }
        .logout { color: #ef5350; text-decoration: none; font-size: 0.9em; border: 1px solid #ef5350; padding: 5px 10px; border-radius: 4px; }
        #chat { height: 400px; border: 1px solid #333; overflow-y: scroll; padding: 10px; margin-bottom: 10px; background: #1e1e1e; border-radius: 8px; }
        .msg { margin-bottom: 10px; line-height: 1.4; }
        .user { color: #4fc3f7; }
        .bot { color: #81c784; }
        input, button { width: 100%; padding: 10px; box-sizing: border-box; margin-top: 5px; border-radius: 5px; border: 1px solid #444; background: #222; color: #fff; }
        button.send-btn { background: #388e3c; color: white; border: none; font-weight: bold; cursor: pointer; }
    </style>
</head>
<body>
    <div class="header">
        <h2>Ouroboros (Hola, {{ user }})</h2>
        <a href="/logout" class="logout">Cerrar Sesión</a>
    </div>
    <div id="chat"><div class="msg bot"><b>Sistema:</b> Servidor iniciado. Estado del modelo ligero: Cargando...</div></div>
    <input type="text" id="userInput" placeholder="Escribe un mensaje..." onkeypress="if(event.key === 'Enter') sendMsg()">
    <button class="send-btn" onclick="sendMsg()">Enviar</button>

    <script>
        async function sendMsg() {
            let input = document.getElementById('userInput');
            let chat = document.getElementById('chat');
            let text = input.value.trim();
            if (!text) return;

            chat.innerHTML += `<div class="msg user"><b>Tú:</b> ${text}</div>`;
            input.value = '';
            chat.scrollTop = chat.scrollHeight;

            let res = await fetch('/chat', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({prompt: text})
            });
            
            if (res.status === 401) {
                window.location.href = '/login';
                return;
            }

            let data = await res.json();
            chat.innerHTML += `<div class="msg bot"><b>Ouroboros:</b> ${data.response}</div>`;
            chat.scrollTop = chat.scrollHeight;
        }
    </script>
</body>
</html>
'''

@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        if username in USERS and USERS[username] == password:
            session['user'] = username
            return redirect(url_for('index'))
        else:
            error = "Usuario o contraseña incorrectos."
            
    return render_template_string(LOGIN_TEMPLATE, error=error)

@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect(url_for('login'))

@app.route('/')
def index():
    if 'user' not in session:
        return redirect(url_for('login'))
    return render_template_string(CHAT_TEMPLATE, user=session['user'])

@app.route('/chat', methods=['POST'])
def chat():
    if 'user' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
        
    global llm, model_status
    if llm is None:
        return jsonify({'response': f'El modelo todavía se está descargando/cargando en la nube. Estado actual: {model_status}'})
    
    user_prompt = request.json.get('prompt', '')
    messages = [
        {"role": "system", "content": "Eres Ouroboros, una IA asistente personal y amigable."},
        {"role": "user", "content": user_prompt}
    ]
    
    response = llm.create_chat_completion(
        messages=messages,
        max_tokens=256,
        temperature=0.7
    )
    
    answer = response["choices"][0]["message"]["content"]
    return jsonify({'response': answer})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
    
