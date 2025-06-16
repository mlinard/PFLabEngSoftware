import os
import json
import time
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS # Importa o CORS

# --- Configuração de Caminhos para Frontend e Banco de Dados ---
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
FRONTEND_DIR = os.path.join(PROJECT_ROOT, 'frontend')
DATABASE_FILE = os.path.join(os.path.dirname(__file__), 'db.json')

# --- Configuração da Aplicação Flask ---
# Removido static_url_path='/' daqui. Ele será manipulado pelas rotas abaixo.
app = Flask(__name__, static_folder=FRONTEND_DIR)
CORS(app)

# --- Funções para Carregar/Salvar Dados do "Banco de Dados" (db.json) ---
def load_db():
    if not os.path.exists(DATABASE_FILE):
        with open(DATABASE_FILE, 'w', encoding='utf-8') as f:
            json.dump({"users": []}, f)
    with open(DATABASE_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_db(data):
    with open(DATABASE_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

# --- NOVAS ROTAS PARA SERVIR O FRONT-END (MAIS EXPLÍCITAS) ---
# Rota para a página inicial (index.html) na raiz do site
@app.route('/')
def serve_index():
    return send_from_directory(FRONTEND_DIR, 'index.html')

# Rota para servir todos os outros arquivos estáticos (CSS, JS, Imagens, outras HTMLs)
# Garante que o Flask sirva qualquer arquivo da pasta frontend/
@app.route('/<path:filename>')
def serve_all_static_files(filename):
    return send_from_directory(FRONTEND_DIR, filename)
# --- FIM DAS NOVAS ROTAS ---


# --- Rotas da API (Back-end) ---

@app.route('/login', methods=['POST'])
def login():
    email = request.json.get('email')
    password = request.json.get('password')

    db = load_db()
    user = next((u for u in db['users'] if u['email'] == email and u['password'] == password), None)

    if user:
        start_time = time.time()
        time.sleep(0.05)
        end_time = time.time()
        response_time_ms = round((end_time - start_time) * 1000)

        user_data = {
            "id": user["id"],
            "email": user["email"],
            "name": user["name"],
            "points": user["points"],
            "next_level_points": user["next_level_points"],
            "badges": user["badges"],
            "recent_discards": user["recent_discards"],
            "login_response_time_ms": response_time_ms
        }
        return jsonify({"message": "Login bem-sucedido!", "user": user_data}), 200
    else:
        return jsonify({"message": "Email ou senha incorretos."}), 401

@app.route('/register', methods=['POST'])
def register():
    email = request.json.get('email')
    password = request.json.get('password')
    name = request.json.get('name', 'Novo Usuário')

    db = load_db()

    if any(u['email'] == email for u in db['users']):
        return jsonify({"message": "Este email já está cadastrado."}), 409

    new_user = {
        "id": f"user{len(db['users']) + 1}",
        "email": email,
        "password": password,
        "name": name,
        "points": 0,
        "next_level_points": 100,
        "badges": [],
        "recent_discards": []
    }
    db['users'].append(new_user)
    save_db(db)

    return jsonify({"message": "Usuário registrado com sucesso!", "user": new_user}), 201

@app.route('/user-data/<user_id>', methods=['GET'])
def get_user_data(user_id):
    db = load_db()
    user = next((u for u in db['users'] if u['id'] == user_id), None)
    if user:
        user_data = {
            "id": user["id"],
            "name": user["name"],
            "points": user["points"],
            "next_level_points": user["next_level_points"],
            "badges": user["badges"],
            "recent_discards": user["recent_discards"]
        }
        return jsonify({"user": user_data}), 200
    else:
        return jsonify({"message": "Usuário não encontrado."}), 404

# --- Execução do Servidor Flask ---
if __name__ == '__main__':
    app.run(debug=True, port=5000)