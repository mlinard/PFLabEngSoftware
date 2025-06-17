import os
import json
import time
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import hashlib # Para criptografia de senhas

print("--- app.py inicializado (Persistência em db.json)! ---")
print(f"Caminho do arquivo app.py sendo executado: {__file__}")

# --- Configuração de Caminhos para Frontend e Banco de Dados ---
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
FRONTEND_DIR = os.path.join(PROJECT_ROOT, 'frontend')
DATABASE_FILE = os.path.join(os.path.dirname(__file__), 'db.json') # Caminho para o db.json

# --- Funções para Carregar/Salvar Dados do db.json ---
def load_db():
    """Carrega os dados do db.json. Cria o arquivo se não existir."""
    if not os.path.exists(DATABASE_FILE):
        # Inicializa com uma estrutura vazia se o arquivo não existir
        initial_data = {"users": []}
        with open(DATABASE_FILE, 'w', encoding='utf-8') as f:
            json.dump(initial_data, f, indent=2, ensure_ascii=False)
    with open(DATABASE_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_db(data):
    """Salva os dados no db.json."""
    with open(DATABASE_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

# --- Configuração da Aplicação Flask ---
app = Flask(__name__, static_folder=FRONTEND_DIR)
CORS(app)

# --- ROTAS PARA SERVIR O FRONT-END ---
@app.route('/')
def serve_index():
    return send_from_directory(FRONTEND_DIR, 'index.html')

@app.route('/<path:filename>')
def serve_all_static_files(filename):
    return send_from_directory(FRONTEND_DIR, filename)

# --- Rotas da API (Back-end) ---

@app.route('/login', methods=['POST'])
def login():
    email = request.json.get('email')
    password = request.json.get('password')
    
    # RNF de Segurança: Criptografa a senha para comparação
    hashed_password_input = hashlib.sha256(password.encode()).hexdigest()

    db = load_db() # Carrega o db.json
    user = next((u for u in db['users'] if u['email'] == email and u['password_hash'] == hashed_password_input), None)

    if user:
        start_time = time.time()
        time.sleep(0.05) 
        end_time = time.time()
        response_time_ms = round((end_time - start_time) * 1000)

        # Retorna apenas os dados necessários para o frontend
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
        print(f"Login bem-sucedido para {user['name']} (ID: {user['id']}).")
        return jsonify({"message": "Login bem-sucedido!", "user": user_data}), 200
    else:
        print(f"Tentativa de login falhou para email: {email}.")
        return jsonify({"message": "Email ou senha incorretos."}), 401

@app.route('/register', methods=['POST'])
def register():
    email = request.json.get('email')
    password = request.json.get('password')
    name = request.json.get('name', 'Novo Usuário')

    db = load_db() # Carrega o db.json

    if any(u['email'] == email for u in db['users']):
        print(f"Tentativa de registro: email {email} já cadastrado.")
        return jsonify({"message": "Este email já está cadastrado."}), 409

    # RNF de Segurança: Criptografa a senha antes de salvar
    hashed_password = hashlib.sha256(password.encode()).hexdigest()
    
    # Gera um ID de usuário simples
    new_user_id = f"user{len(db['users']) + 1}"
    new_user = {
        "id": new_user_id,
        "email": email,
        "password_hash": hashed_password, # Senha criptografada
        "name": name,
        "points": 0,
        "next_level_points": 10000, 
        "badges": [],
        "recent_discards": []
    }
    db['users'].append(new_user)
    save_db(db) # Salva o db.json
    print(f"Usuário registrado com sucesso: {new_user['name']} (ID: {new_user['id']}).")
    return jsonify({"message": "Usuário registrado com sucesso!", "user": new_user}), 201

@app.route('/user-data/<user_id>', methods=['GET'])
def get_user_data(user_id):
    db = load_db() # Carrega o db.json
    user = next((u for u in db['users'] if u['id'] == user_id), None)
    if user:
        # Retorna apenas os dados necessários para o frontend
        user_data = {
            "id": user["id"],
            "name": user["name"],
            "points": user["points"],
            "next_level_points": user["next_level_points"],
            "badges": user["badges"],
            "recent_discards": user["recent_discards"]
        }
        print(f"Dados do usuário {user['name']} (ID: {user['id']}) solicitados e enviados.")
        return jsonify({"user": user_data}), 200
    else:
        print(f"Usuário {user_id} não encontrado para /user-data.")
        return jsonify({"message": "Usuário não encontrado."}), 404

# --- Endpoint para Registrar Descarte ---
@app.route('/register-discard', methods=['POST'])
def register_discard():
    user_id = request.json.get('userId')
    item = request.json.get('item')
    weight = request.json.get('weight')
    location = request.json.get('location')
    date = request.json.get('date')
    points = request.json.get('points') 

    if not all([user_id, item, weight, location, date, points is not None]):
        print(f"Dados de descarte incompletos para {user_id}. Recebido: {request.json}")
        return jsonify({"message": "Dados de descarte incompletos."}), 400

    db = load_db() # Carrega o db.json
    user_found = False
    for i, user in enumerate(db['users']):
        if user['id'] == user_id:
            user_found = True
            # Adiciona pontos
            user['points'] += points
            print(f"Pontos de {user['name']} atualizados para {user['points']} após descarte de {item}.")

            # Adiciona conquista (badge) se for a primeira vez para este tipo de material
            badge_name = f'Primeiro {item}'
            if badge_name not in user['badges']:
                user['badges'].append(badge_name)
                print(f"Nova conquista '{badge_name}' adicionada para {user['name']}.")
            
            # Assegura que 'recent_discards' é uma lista (para o caso de usuários antigos sem o campo)
            if 'recent_discards' not in user:
                user['recent_discards'] = []
            
            # Adiciona o descarte aos descartes recentes (no início da lista)
            user['recent_discards'].insert(0, {
                "item": item,
                "weight": f"{weight}kg", 
                "location": location,
                "date": date
            })
            # Limita a quantidade de descartes recentes para não sobrecarregar
            user['recent_discards'] = user['recent_discards'][:5] # Mantém os 5 mais recentes
            print(f"Descarte de {item} registrado para {user['name']}. Descartes recentes: {user['recent_discards']}")
            
            save_db(db) # Salva o db.json após as alterações
            return jsonify({"message": "Descarte registrado e pontos adicionados com sucesso!", "new_points": user['points'], "new_badges": user['badges']}), 200
    
    if not user_found:
        print(f"Usuário {user_id} não encontrado para registro de descarte.")
        return jsonify({"message": "Usuário não encontrado."}), 404

# --- NOVO ENDPOINT: Resgatar Recompensa ---
@app.route('/redeem-reward', methods=['POST'])
def redeem_reward():
    user_id = request.json.get('userId')
    reward_name = request.json.get('rewardName')
    reward_cost = request.json.get('rewardCost')

    if not all([user_id, reward_name, reward_cost is not None]):
        print(f"Dados de resgate incompletos para user {user_id}.")
        return jsonify({"message": "Dados de recompensa incompletos."}), 400

    db = load_db()
    user_found = False
    for i, user in enumerate(db['users']):
        if user['id'] == user_id:
            user_found = True
            if user['points'] >= reward_cost:
                user['points'] -= reward_cost
                
                # Opcional: Adicionar a recompensa a um histórico de resgates do usuário
                if 'redeemed_rewards' not in user:
                    user['redeemed_rewards'] = []
                user['redeemed_rewards'].append({
                    "name": reward_name,
                    "cost": reward_cost,
                    "date": time.strftime("%d/%m/%Y")
                })

                save_db(db)
                print(f"Recompensa '{reward_name}' resgatada por {user['name']}. Pontos atuais: {user['points']}.")
                return jsonify({"message": f"Recompensa '{reward_name}' resgatada com sucesso!", "new_points": user['points']}), 200
            else:
                print(f"{user['name']} tentou resgatar '{reward_name}', mas tem {user['points']} pontos, precisa de {reward_cost}.")
                return jsonify({"message": "Pontos insuficientes para resgatar esta recompensa."}), 400
    
    if not user_found:
        print(f"Usuário {user_id} não encontrado para resgate de recompensa.")
        return jsonify({"message": "Usuário não encontrado."}), 404


# --- Execução do Servidor Flask ---
if __name__ == '__main__':
    load_db() # Garante que o db.json exista e esteja com a estrutura inicial
    app.run(host='0.0.0.0', port=5000, debug=False, use_reloader=False)
