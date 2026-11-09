import os
from flask import Flask, request, jsonify, render_template_string
from huggingface_hub import hf_hub_download
from llama_cpp import Llama

app = Flask(__name__)

# Descarga automáticamente el modelo Qwen 2.5 3B Q4_K_M
model_path = hf_hub_download(
    repo_id="Qwen/Qwen2.5-3B-Instruct-GGUF",
    filename="qwen2.5-3b-instruct-q4_k_m.gguf"
)

llm = Llama(
    model_path=model_path,
    n_ctx=2048,
    verbose=False
)

HTML_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head>
    <title>Ouroboros IA</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        body { font-family: sans-serif; max-width: 600px; margin: 20px auto; padding: 0 10px; background: #121212; color: #e0e0e0; }
        #chat { height: 400px; border: 1px solid #333; overflow-y: scroll; padding: 10px; margin-bottom: 10px; background: #1e1e1e; border-radius: 8px; }
        .msg { margin-bottom: 10px; line-height: 1.4; }
        .user { color: #4fc3f7; }
        .bot { color: #81c784; }
        input, button { width: 100%; padding: 10px; box-sizing: border-box; margin-top: 5px; border-radius: 5px; border: 1px solid #444; background: #222; color: #fff; }
        button { background: #388e3c; color: white; border: none; font-weight: bold; cursor: pointer; }
    </style>
</head>
<body>
    <h2>Ouroboros IA (Nube 24/7)</h2>
    <div id="chat"></div>
    <input type="text" id="userInput" placeholder="Escribe un mensaje..." onkeypress="if(event.key === 'Enter') sendMsg()">
    <button onclick="sendMsg()">Enviar</button>

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
            let data = await res.json();
            
            chat.innerHTML += `<div class="msg bot"><b>Ouroboros:</b> ${data.response}</div>`;
            chat.scrollTop = chat.scrollHeight;
        }
    </script>
</body>
</html>
'''

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route('/chat', methods=['POST'])
def chat():
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
  
