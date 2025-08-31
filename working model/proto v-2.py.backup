import hashlib
import json
from time import time, sleep
from datetime import datetime
import logging
from functools import wraps
from flask import Flask, jsonify, request, render_template_string, redirect, url_for, session, flash
import os
import google.generativeai as genai

# --- Basic Setup & Logging ---
app = Flask(__name__)
app.secret_key = 'a_very_secret_and_secure_key_for_hackout25'
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
class ListHandler(logging.Handler):
    def __init__(self, *args, **kwargs): super().__init__(*args, **kwargs); self.log_records = []
    def emit(self, record): self.log_records.append(self.format(record))
log_handler = ListHandler()
app.logger.addHandler(log_handler); app.logger.setLevel(logging.INFO)

# --- Data Persistence ---
DATA_FILE = 'ghcs_data.json'
APP_DATA = {}

# --- Integrated Gemini AI Service ---
try:
    with open("api_key.txt", 'r') as f:
        api_key = f.read().strip()
    if not api_key: raise ValueError("API key file is empty.")
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel(model_name="gemini-2.5-flash")
    app.logger.info("Gemini 2.5 Flash model configured successfully.")
except FileNotFoundError:
    app.logger.error("Error: api_key.txt not found. Please create this file with your Google AI API key.")
    model = None
except Exception as e:
    app.logger.error(f"Error configuring Gemini AI: {e}")
    model = None

AI_ANALYST_PROMPT = """You are an expert financial and cybersecurity analyst for a government regulatory body overseeing a Green Hydrogen Credit System. Your task is to assess the risk of a pending credit issuance request. Analyze the provided data for anomalies, fraud, or inconsistencies. DATA PROVIDED: Producer Name, Stated Daily Capacity, Pending Issuance Amount, Recent Transaction History. YOUR ANALYSIS MUST COVER: 1. Volatility Analysis (drastic spikes/drops). 2. Capacity Breach. 3. Pattern Anomalies. RESPONSE FORMAT: You MUST respond with ONLY a valid JSON object. The JSON structure must be: { "risk_score": <integer, 0-100>, "assessment": "<string, "Low Risk" | "Medium Risk" | "High Risk">", "summary": "<string, a one-sentence summary>", "detailed_analysis": ["<string, first point>", "<string, second point>"] } """

def get_ai_analysis(producer_name, capacity, pending_amount, history):
    # This function is correct and remains unchanged.
    if not model: return {"error": "AI model is not configured."}
    history_str = "\n".join([f"- {tx['amount']} credits on {tx['timestamp'][:10]}" for tx in history]) or "No previous transactions."
    user_prompt = f"ANALYSIS REQUEST:\n- Producer Name: {producer_name}\n- Stated Daily Capacity: {capacity}\n- Pending Issuance Amount: {pending_amount}\n- Recent Transaction History:\n{history_str}"
    try:
        app.logger.info(f"Generating AI content for producer: {producer_name}")
        response = model.generate_content([AI_ANALYST_PROMPT, user_prompt])
        cleaned_text = response.text.strip().replace("```json", "").replace("```", "")
        return json.loads(cleaned_text)
    except Exception as e:
        app.logger.error(f"Error during AI analysis or JSON parsing: {e}")
        return {"error": "Failed to get a valid analysis from the AI model."}

# --- Blockchain and App Logic ---
def load_data():
    global APP_DATA
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r') as f: APP_DATA = json.load(f)
    else:
        APP_DATA = {'users': {}, 'blockchain': {'chain': [], 'current_transactions': []}, 'pending_issuances': {}, 'quotas': {}, 'issuance_counter': 0}
        setup_initial_users()
        save_data()
    blockchain.__init__(chain=APP_DATA['blockchain']['chain'], current_transactions=APP_DATA['blockchain']['current_transactions'])
    app.logger.info("Application data loaded from ghcs_data.json")

def save_data():
    APP_DATA['blockchain']['chain'] = blockchain.chain
    APP_DATA['blockchain']['current_transactions'] = blockchain.current_transactions
    with open(DATA_FILE, 'w') as f: json.dump(APP_DATA, f, indent=4)

class Blockchain: # Unchanged
    def __init__(self, chain=None, current_transactions=None):
        self.chain = chain if chain is not None else []
        self.current_transactions = current_transactions if current_transactions is not None else []
        if not self.chain: self.create_block(previous_hash='1', proof=100)
    def _hash_transaction(self, tx): return hashlib.sha256(json.dumps(tx, sort_keys=True).encode()).hexdigest()
    def create_block(self, proof, previous_hash=None):
        block = {'index': len(self.chain) + 1, 'timestamp': time(), 'transactions': self.current_transactions, 'proof': proof, 'previous_hash': previous_hash or self.hash(self.chain[-1])}
        self.current_transactions = []; self.chain.append(block)
        app.logger.info(f"CHAIN: New block #{block['index']} forged.")
        return block
    def add_transaction(self, sender, recipient, amount, details):
        tx = {'sender': sender, 'recipient': recipient, 'amount': amount, 'details': details, 'timestamp': datetime.now().isoformat()}
        tx['transaction_hash'] = self._hash_transaction(tx); self.current_transactions.append(tx)
        return self.get_last_block()['index'] + 1
    @staticmethod
    def hash(block): return hashlib.sha256(json.dumps(block, sort_keys=True).encode()).hexdigest()
    def get_last_block(self): return self.chain[-1] if self.chain else None
    def proof_of_work(self, last_proof):
        proof = 0
        while self.valid_proof(last_proof, proof) is False: proof += 1
        return proof
    @staticmethod
    def valid_proof(last_proof, proof): return hashlib.sha256(f'{last_proof}{proof}'.encode()).hexdigest()[:4] == "0000"
    def get_balance(self, account_name):
        bal = 0
        for block in self.chain:
            for tx in block['transactions']:
                if tx['recipient'] == account_name: bal += tx['amount']
                if tx['sender'] == account_name: bal -= tx['amount']
        return bal
    def get_user_transactions(self, account_name, limit=25):
        txs = []
        for block in reversed(self.chain):
            for tx in reversed(block['transactions']):
                if tx['recipient'] == account_name or tx['sender'] == account_name:
                    tx_with_ctx = tx.copy(); tx_with_ctx['block_index'] = block['index']; txs.append(tx_with_ctx)
                if len(txs) >= limit: return txs
        return txs
blockchain = Blockchain()
def hash_password(password): return hashlib.sha256(password.encode()).hexdigest()
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'logged_in' not in session: return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function
def role_required(required_roles):
    def wrapper(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if session.get('role') not in required_roles:
                flash("You do not have permission to access this page.", "danger"); return redirect(url_for('dashboard'))
            return f(*args, **kwargs)
        return decorated_function
    return wrapper
def setup_initial_users(): # Unchanged
    initial_users_data = [{"name": "GovtAdmin", "password": "govpassword", "role": "Government"}, {"name": "StatePollGujarat", "password": "sppassword", "role": "State Poll"}, {"name": "SomnathProducers", "password": "prodpassword", "role": "Producer", "state_verification_no": "SVN-GJ-001", "capacity": 5000}, {"name": "Ammonia Factory", "password": "factpassword", "role": "Factory", "industry_type": "Ammonia", "industry_consumption": 20000}, {"name": "CitizenOne", "password": "citipassword", "role": "Citizen"}]
    for user_data in initial_users_data:
        if user_data['name'] not in APP_DATA['users']:
            password = user_data.pop("password")
            user_data['password_hash'] = hash_password(password)
            user_data['frozen'] = False
            APP_DATA['users'][user_data['name']] = user_data
    blockchain.add_transaction("NETWORK_GENESIS", "SomnathProducers", 1000, "Initial credit allocation")
    last_block = blockchain.get_last_block()
    proof = blockchain.proof_of_work(last_block['proof'])
    blockchain.create_block(proof, blockchain.hash(last_block))

# --- Flask Routes ---
@app.route('/login', methods=['GET', 'POST'])
def login(): # Unchanged
    if request.method == 'POST':
        username = request.form['name']
        user = APP_DATA['users'].get(username)
        if user and user['password_hash'] == hash_password(request.form['password']):
            session['logged_in'], session['username'], session['role'] = True, username, user['role']
            return redirect(url_for('dashboard'))
        flash("Invalid credentials.", "danger")
    return render_template_string(HTML_TEMPLATE, page='login')

@app.route('/register', methods=['GET', 'POST'])
def register(): # Unchanged
    if request.method == 'POST':
        name = request.form['name']
        if name in APP_DATA['users']:
            flash("Username already exists.", "warning"); return redirect(url_for('register'))
        new_user = {'name': name, 'password_hash': hash_password(request.form['password']), 'role': request.form['type'], 'frozen': False}
        if new_user['role'] == 'Producer':
            new_user['state_verification_no'] = request.form.get('state_verification_no', 'N/A')
            new_user['capacity'] = int(request.form.get('capacity', 0))
        elif new_user['role'] == 'Factory':
            new_user['industry_type'] = request.form.get('industry_type', 'N/A')
            new_user['industry_consumption'] = int(request.form.get('industry_consumption', 0))
        APP_DATA['users'][name] = new_user
        save_data()
        flash("Registration successful!", "success"); return redirect(url_for('login'))
    return render_template_string(HTML_TEMPLATE, page='register')

@app.route('/logout')
def logout(): # Unchanged
    session.clear(); return redirect(url_for('login'))

@app.route('/')
@login_required
def dashboard():
    username = session['username']
    producers = {name: u for name, u in APP_DATA['users'].items() if u['role'] == 'Producer'}
    factories = {name: u for name, u in APP_DATA['users'].items() if u['role'] == 'Factory'}
    total_credits = sum(blockchain.get_balance(p_name) for p_name in producers)
    
    # Filter offers for the UI
    pending_offers = {k: v for k, v in APP_DATA['pending_issuances'].items() if v['status'] == 'Pending Verification'}
    scrutinized_offers = {k: v for k, v in APP_DATA['pending_issuances'].items() if v['status'] == 'Under Scrutiny'}

    data = {
        'page': 'dashboard', 'username': username, 'role': session['role'], 
        'balance': blockchain.get_balance(username), 
        'transactions': blockchain.get_user_transactions(username, 10), 
        'logs': list(reversed(log_handler.log_records[-20:])), 
        'users': APP_DATA['users'], 'producers': producers, 'factories': factories,
        'user_data': APP_DATA['users'].get(username, {}), 
        'pending_offers': pending_offers,
        'scrutinized_offers': scrutinized_offers,
        'quotas': APP_DATA['quotas'],
        'blockchain': blockchain,
        'total_credits_in_system': total_credits
    }
    return render_template_string(HTML_TEMPLATE, **data)

@app.route('/ai-analyze', methods=['POST'])
@login_required
@role_required(['State Poll'])
def ai_analyze(): # Unchanged
    producer_name = request.json.get('producer_name')
    issuance_id = request.json.get('issuance_id')
    producer_data = APP_DATA['users'].get(producer_name, {})
    pending_offer = APP_DATA['pending_issuances'].get(issuance_id, {})
    analysis_result = get_ai_analysis(producer_name=producer_name, capacity=producer_data.get('capacity', 0), pending_amount=pending_offer.get('amount', 0), history=blockchain.get_user_transactions(producer_name))
    return jsonify(analysis_result)

@app.route('/buy-credit', methods=['POST'])
@login_required
@role_required(['Factory'])
def buy_credit(): # Unchanged
    buyer_name, seller_name = session['username'], request.form.get('seller')
    try: amount = int(request.form.get('amount'))
    except (ValueError, TypeError):
        flash("Invalid amount.", "danger"); return redirect(url_for('dashboard'))
    factory_quota = APP_DATA['quotas'].get(buyer_name)
    if factory_quota is not None and amount > factory_quota:
        flash(f"Purchase failed. Exceeds quota of {factory_quota}.", "danger"); return redirect(url_for('dashboard'))
    seller_balance = blockchain.get_balance(seller_name)
    if seller_balance < amount:
        flash(f"Purchase failed. Seller has insufficient credits.", "danger"); return redirect(url_for('dashboard'))
    blockchain.add_transaction(sender=seller_name, recipient=buyer_name, amount=amount, details=f"Credit purchase")
    last_block = blockchain.get_last_block()
    proof = blockchain.proof_of_work(last_block['proof'])
    blockchain.create_block(proof, blockchain.hash(last_block))
    save_data()
    flash(f"Successfully purchased {amount} credits.", "success")
    return redirect(url_for('dashboard'))

@app.route('/issue-credit', methods=['POST'])
@login_required
@role_required(['Producer'])
def issue_credit(): # Unchanged
    username = session['username']
    if APP_DATA['users'][username].get('frozen'):
        flash("Account frozen.", "danger"); return redirect(url_for('dashboard'))
    try: amount = int(request.form['amount'])
    except (ValueError, TypeError):
        flash("Invalid amount.", "danger"); return redirect(url_for('dashboard'))
    APP_DATA['issuance_counter'] += 1
    issuance_id = f"ISSUE-{APP_DATA['issuance_counter']}"
    APP_DATA['pending_issuances'][issuance_id] = {'producer_name': username, 'amount': amount, 'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"), 'status': 'Pending Verification'}
    save_data()
    flash(f"Submitted request to issue {amount} credits.", "success")
    return redirect(url_for('dashboard'))

# --- UPDATED: PROCESS ISSUANCE ROUTE ---
@app.route('/process-issuance/<issuance_id>', methods=['POST'])
@login_required
@role_required(['State Poll', 'Government']) # Now accessible by Government as well
def process_issuance(issuance_id):
    issuance = APP_DATA['pending_issuances'].get(issuance_id)
    if not issuance:
        flash("Issuance request not found.", "danger"); return redirect(url_for('dashboard'))
    
    action = request.form['action']
    producer_name = issuance['producer_name']
    amount = issuance['amount']
    
    if action == 'Certify':
        blockchain.add_transaction("NETWORK_CERTIFIER", producer_name, amount, f"Certified Issuance ID: {issuance_id}")
        last_block = blockchain.get_last_block()
        proof = blockchain.proof_of_work(last_block['proof'])
        blockchain.create_block(proof, blockchain.hash(last_block))
        del APP_DATA['pending_issuances'][issuance_id]
        flash(f"Successfully certified {amount} credits for {producer_name}.", "success")
    elif action == 'Scrutinize':
        if session['role'] != 'State Poll':
            flash("Only State Pollution Bodies can send offers for scrutiny.", "danger")
            return redirect(url_for('dashboard'))
        APP_DATA['pending_issuances'][issuance_id]['status'] = 'Under Scrutiny'
        flash(f"Offer from {producer_name} has been escalated for government scrutiny.", "warning")
    elif action == 'Reject':
        del APP_DATA['pending_issuances'][issuance_id]
        flash(f"Offer from {producer_name} for {amount} credits was rejected.", "danger")
    
    save_data()
    return redirect(url_for('dashboard'))

# Unchanged routes for freeze and quotas
@app.route('/freeze-account', methods=['POST'])
@login_required
@role_required(['Government'])
def freeze_account():
    username = request.form['username']
    if username in APP_DATA['users']:
        APP_DATA['users'][username]['frozen'] = not APP_DATA['users'][username].get('frozen', False)
        status = "frozen" if APP_DATA['users'][username]['frozen'] else "unfrozen"; save_data()
        flash(f"Account '{username}' has been {status}.", "success")
    return redirect(url_for('dashboard'))
@app.route('/set-producer-quota', methods=['POST'])
@login_required
@role_required(['Government'])
def set_producer_quota():
    producer_name = request.form['producer_name']; quota = int(request.form['quota_amount'])
    APP_DATA['quotas'][producer_name] = quota; save_data()
    flash(f"Production quota for {producer_name} set to {quota}.", "success")
    return redirect(url_for('dashboard'))
@app.route('/set-factory-quota', methods=['POST'])
@login_required
@role_required(['Government'])
def set_factory_quota():
    factory_name = request.form['factory_name']; quota = int(request.form['quota_amount'])
    APP_DATA['quotas'][factory_name] = quota; save_data()
    flash(f"Consumption quota for {factory_name} set to {quota}.", "success")
    return redirect(url_for('dashboard'))


# --- UPDATED HTML TEMPLATE ---
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8"> <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>GHCS - Green Hydrogen Credit System</title>
    <style>
        :root { --azure-blue: #0078D4; --azure-blue-dark: #005A9E; --bg-light: #f0f2f5; --card-bg: #ffffff; --text-dark: #333333; --text-light: #666666; --border-color: #e1e1e1; --green: #107C10; --red: #D83B01; --yellow: #F7A924; --blue-light: #e7f3fe; --yellow-light: #fff4ce; }
        body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; background-color: var(--bg-light); color: var(--text-dark); margin: 0; }
        .container { max-width: 1400px; margin: 0 auto; padding: 20px; }
        .header { display: flex; justify-content: space-between; align-items: center; background-color: var(--azure-blue); color: white; padding: 10px 30px; }
        h1, h2, h3 { margin: 0; font-weight: 600; } h1 { font-size: 22px; }
        .header a { color: white; text-decoration: none; font-weight: 600; }
        .card { background-color: var(--card-bg); border: 1px solid var(--border-color); border-radius: 4px; margin-bottom: 20px; box-shadow: 0 1px 3px rgba(0,0,0,0.08); }
        .card-header { padding: 15px 20px; border-bottom: 1px solid var(--border-color); font-size: 18px; }
        .card-body { padding: 20px; }
        .grid-2 { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; }
        .grid-3 { display: grid; grid-template-columns: repeat(3, 1fr); gap: 20px; }
        .form-group { margin-bottom: 15px; }
        .form-group label { display: block; margin-bottom: 5px; font-weight: 600; color: var(--text-light); }
        .form-group input, .form-group select { width: 100%; padding: 10px; border: 1px solid #ccc; border-radius: 4px; box-sizing: border-box; }
        .btn { padding: 8px 15px; border: none; border-radius: 4px; cursor: pointer; font-weight: 600; text-transform: uppercase; letter-spacing: 0.5px; transition: background-color 0.2s; }
        .btn-primary { background-color: var(--azure-blue); color: white; } .btn-success { background-color: var(--green); color: white; }
        .btn-danger { background-color: var(--red); color: white; } .btn-warning { background-color: var(--yellow); color: white; } .btn-secondary { background-color: #6c757d; color: white; }
        table { width: 100%; border-collapse: collapse; font-size: 0.9em; }
        th, td { padding: 12px; text-align: left; border-bottom: 1px solid var(--border-color); }
        th { color: var(--text-light); font-weight: 600; }
        .alert { padding: 15px; margin: 10px 0; border-radius: 4px; color: white; font-weight: 600; }
        .alert-success { background-color: var(--green); } .alert-danger { background-color: var(--red); } .alert-warning { background-color: var(--yellow); }
        .log-box { background-color: #2b2b2b; color: #a9b7c6; font-family: monospace; height: 300px; overflow-y: scroll; padding: 15px; border-radius: 4px; white-space: pre-wrap; font-size: 13px; }
        .balance { font-size: 24px; font-weight: bold; color: var(--green); }
        code { font-family: monospace; background-color: #f0f0f0; padding: 2px 5px; border-radius: 3px; font-size: 12px; }
        .login-card { max-width: 400px; margin: 80px auto; }
        .sub-detail { color: var(--text-light); font-size: 0.9em; margin-top: 0; }
        .tabs { display: flex; border-bottom: 2px solid var(--border-color); margin-bottom: 20px; }
        .tab-link { padding: 10px 20px; cursor: pointer; border: none; background: none; font-size: 16px; font-weight: 600; color: var(--text-light); }
        .tab-link.active { color: var(--azure-blue); border-bottom: 2px solid var(--azure-blue); }
        .tab-content { display: none; } .tab-content.active { display: block; }
    </style>
</head>
<body>
    {% if page == 'login' or page == 'register' %}
        <!-- Login/Register page is unchanged -->
        <div class="container"><div class="login-card card"><div class="card-header">{% if page == 'login' %}GHCS Login{% else %}GHCS Registration{% endif %}</div><div class="card-body">{% with m=get_flashed_messages(with_categories=true) %}{% if m %}{% for c,msg in m %}<div class="alert alert-{{c}}">{{msg}}</div>{% endfor %}{% endif %}{% endwith %}<form method="POST"><div class="form-group"><label>Username</label><input type="text" name="name" required></div><div class="form-group"><label>Password</label><input type="password" name="password" required></div>{% if page == 'register' %}<div class="form-group"><label>Account Type</label><select name="type" id="typeSelect" onchange="toggleFields()"><option value="Citizen">Citizen</option><option value="Producer">Producer</option><option value="Factory">Factory</option><option value="State Poll">State Pollution Body</option><option value="Government">Government</option></select></div><div id="producer-fields" style="display:none;"><div class="form-group"><label>State Verification No</label><input type="text" name="state_verification_no"></div><div class="form-group"><label>Capacity (units/day)</label><input type="number" name="capacity"></div></div><div id="factory-fields" style="display:none;"><div class="form-group"><label>Industry Type</label><input type="text" name="industry_type" placeholder="e.g., Ammonia"></div><div class="form-group"><label>Consumption Quota</label><input type="number" name="industry_consumption"></div></div>{% endif %}<button type="submit" class="btn btn-primary" style="width:100%;">{% if page=='login' %}Login{% else %}Register{% endif %}</button><p style="text-align:center;margin-top:15px;">{% if page=='login' %}No account? <a href="{{url_for('register')}}">Register</a>{% else %}Have an account? <a href="{{url_for('login')}}">Login</a>{% endif %}</p></form></div></div></div>
        <script>
            function toggleFields() { const type = document.getElementById('typeSelect').value; document.getElementById('producer-fields').style.display = type === 'Producer' ? 'block' : 'none'; document.getElementById('factory-fields').style.display = type === 'Factory' ? 'block' : 'none'; }
            document.addEventListener('DOMContentLoaded', function() { if (document.getElementById('typeSelect')) { toggleFields(); } });
        </script>
    {% else %}
        <div class="header"><h1>GHCS <span style="font-weight: 300;">| {{ role }} Dashboard</span></h1><div>Welcome, <strong>{{ username }}</strong> &nbsp;&nbsp; <a href="{{ url_for('logout') }}">Logout</a></div></div>
        <div class="container">
            {% with m=get_flashed_messages(with_categories=true) %}{% if m %}{% for c,msg in m %}<div class="alert alert-{{c}}">{{msg}}</div>{% endfor %}{% endif %}{% endwith %}
            {% if user_data.frozen %}<div class="alert alert-danger">ACCOUNT FROZEN. Actions disabled.</div>{% endif %}
            
            <div class="grid-2">
                <div><div class="card"><div class="card-header">Account Overview</div><div class="card-body"><p><strong>Username:</strong> {{ username }}</p><p><strong>Role:</strong> {{ role }}</p>{% if role == 'Producer' and user_data.capacity is defined %}<p class="sub-detail">Capacity: {{ user_data.capacity }} units/day</p>{% endif %}{% if role == 'Factory' and user_data.industry_type is defined %}<p class="sub-detail">Industry: {{ user_data.industry_type }}</p>{% endif %}<hr style="border:0;border-top:1px solid #eee;margin:15px 0;"><p><strong>Credit Balance:</strong> <span class="balance">{{ balance }} GHC</span></p></div></div>
                {% if role in ['Factory', 'Producer', 'Citizen'] %}<div class="card"><div class="card-header">System Information</div><div class="card-body"><p><strong>Total Credits in Circulation:</strong> <span class="balance" style="font-size:1.2em;">{{ total_credits_in_system }} GHC</span></p></div></div>{% endif %}
                {% if role == 'Factory' %}<div class="card"><div class="card-header">Purchase Credits</div><div class="card-body"><form action="{{ url_for('buy_credit') }}" method="POST"><p class="sub-detail">Your consumption quota is: {{ quotas.get(username, 'Not Set') }}</p><div class="form-group"><label>Select Producer</label><select name="seller" required>{% for name, p in producers.items() %}<option value="{{ name }}">{{ name }} (Avail: {{ blockchain.get_balance(name) }} GHC)</option>{% endfor %}</select></div><div class="form-group"><label>Amount</label><input type="number" name="amount" required min="1"></div><button type="submit" class="btn btn-success" {% if user_data.frozen %}disabled{% endif %}>Purchase</button></form></div></div>{% endif %}
                {% if role == 'Producer' %}<div class="card"><div class="card-header">Issue Credits</div><div class="card-body"><p class="sub-detail">Your production quota is: {{ quotas.get(username, 'Not Set') }}</p><form action="{{ url_for('issue_credit') }}" method="POST"><div class="form-group"><label>Amount to Issue</label><input type="number" name="amount" required></div><button type="submit" class="btn btn-primary" {% if user_data.frozen %}disabled{% endif %}>Submit Offer</button></form></div></div>{% endif %}
                </div>
                <div><div class="card"><div class="card-header">System Logs</div><div class="card-body"><div class="log-box">{% for log in logs %}{{ log }}\n{% endfor %}</div></div></div></div>
            </div>

            {% if role == 'State Poll' %}
                <div class="card">
                    <div class="card-header">
                        <div class="tabs">
                            <button class="tab-link active" onclick="openTab(event, 'pending')">Pending Offers ({{ pending_offers|length }})</button>
                            <button class="tab-link" onclick="openTab(event, 'scrutinized')">Scrutinized Offers ({{ scrutinized_offers|length }})</button>
                        </div>
                    </div>
                    <div class="card-body">
                        <div id="pending" class="tab-content active">
                            <h3>Awaiting Initial Verification</h3>
                            {% if pending_offers %}<table><thead><tr><th>Offer ID</th><th>Producer</th><th>Amount</th><th>Actions</th></tr></thead><tbody>
                            {% for id, offer in pending_offers.items() %}<tr><td>{{id}}</td><td>{{offer.producer_name}}</td><td>{{offer.amount}} GHC</td><td><div style="display:flex;gap:5px;">
                                <form onsubmit="return confirm('Are you sure you want to certify this offer?');" action="{{url_for('process_issuance',issuance_id=id)}}" method="POST"><input type="hidden" name="action" value="Certify"><button type="submit" class="btn btn-success">Certify</button></form>
                                <form onsubmit="return confirm('Are you sure you want to escalate this for government scrutiny?');" action="{{url_for('process_issuance',issuance_id=id)}}" method="POST"><input type="hidden" name="action" value="Scrutinize"><button type="submit" class="btn btn-warning">Scrutinize</button></form>
                                <button class="btn btn-secondary" onclick="runAiAnalysis('{{ offer.producer_name }}', '{{ id }}')">AI</button>
                                <form onsubmit="return confirm('Are you sure you want to REJECT this offer? This cannot be undone.');" action="{{url_for('process_issuance',issuance_id=id)}}" method="POST"><input type="hidden" name="action" value="Reject"><button type="submit" class="btn btn-danger">Reject</button></form>
                            </div></td></tr>{% endfor %}</tbody></table>{% else %}<p>No new offers to review.</p>{% endif %}
                        </div>
                        <div id="scrutinized" class="tab-content">
                            <h3>Escalated for Government Review</h3>
                            {% if scrutinized_offers %}<table><thead><tr><th>Offer ID</th><th>Producer</th><th>Amount</th><th>Status</th></tr></thead><tbody>
                            {% for id, offer in scrutinized_offers.items() %}<tr><td>{{id}}</td><td>{{offer.producer_name}}</td><td>{{offer.amount}} GHC</td><td>Under Scrutiny</td></tr>{% endfor %}</tbody></table>
                            {% else %}<p>No offers are currently under scrutiny.</p>{% endif %}
                        </div>
                    </div>
                </div>
            {% endif %}

            {% if role == 'Government' %}
                <div class="card"><div class="card-header">Offers Under Scrutiny</div><div class="card-body">
                    {% if scrutinized_offers %}<table><thead><tr><th>Offer ID</th><th>Producer</th><th>Amount</th><th>Actions</th></tr></thead><tbody>
                    {% for id, offer in scrutinized_offers.items() %}<tr><td>{{id}}</td><td>{{offer.producer_name}}</td><td>{{offer.amount}} GHC</td><td><div style="display:flex;gap:5px;">
                        <form onsubmit="return confirm('As a government authority, are you sure you want to certify this scrutinized offer?');" action="{{url_for('process_issuance',issuance_id=id)}}" method="POST"><input type="hidden" name="action" value="Certify"><button type="submit" class="btn btn-success">Approve</button></form>
                        <form onsubmit="return confirm('Are you sure you want to REJECT this scrutinized offer?');" action="{{url_for('process_issuance',issuance_id=id)}}" method="POST"><input type="hidden" name="action" value="Reject"><button type="submit" class="btn btn-danger">Reject</button></form>
                    </div></td></tr>{% endfor %}</tbody></table>
                    {% else %}<p>No offers have been escalated for government review.</p>{% endif %}
                </div></div>
                <div class="grid-3">
                    <div class="card"><div class="card-header">Account Management</div><div class="card-body"><form action="{{url_for('freeze_account')}}" method="POST"><div class="form-group"><label>Select User</label><select name="username">{% for name, u in users.items() if name != 'GovtAdmin' %}<option value="{{name}}">{{name}} ({{u.role}}) - {%if u.get('frozen')%}Frozen{%else%}Active{%endif%}</option>{% endfor %}</select></div><button type="submit" class="btn btn-danger">Toggle Freeze</button></form></div></div>
                    <div class="card"><div class="card-header">Set Producer Quotas</div><div class="card-body"><form action="{{url_for('set_producer_quota')}}" method="POST"><div class="form-group"><label>Select Producer</label><select name="producer_name">{%for name,u in producers.items()%}<option value="{{name}}">{{name}}</option>{%endfor%}</select></div><div class="form-group"><label>Daily Prod. Quota</label><input type="number" name="quota_amount" required></div><button type="submit" class="btn btn-primary">Set Quota</button></form></div></div>
                    <div class="card"><div class="card-header">Set Factory Quotas</div><div class="card-body"><form action="{{url_for('set_factory_quota')}}" method="POST"><div class="form-group"><label>Select Factory</label><select name="factory_name">{% for name, u in factories.items() %}<option value="{{name}}">{{name}}</option>{% endfor %}</select></div><div class="form-group"><label>Daily Cons. Quota</label><input type="number" name="quota_amount" required></div><button type="submit" class="btn btn-primary">Set Quota</button></form></div></div>
                </div>
            {% endif %}
            
            <div class="card"><div class="card-header">My Recent Transactions</div><div class="card-body">{% if transactions %}<table><thead><tr><th>Block #</th><th>TX Hash</th><th>From</th><th>To</th><th>Amount</th><th>Details</th></tr></thead><tbody>{% for tx in transactions %}<tr><td>{{tx.block_index}}</td><td><code>{{tx.transaction_hash[:12]}}...</code></td><td>{{tx.sender}}</td><td>{{tx.recipient}}</td><td>{{tx.amount}} GHC</td><td>{{tx.details}}</td></tr>{% endfor %}</tbody></table>{% else %}<p>No transactions found.</p>{% endif %}</div></div>
        </div>
        <script>
            function openTab(evt, tabName) {
                var i, tabcontent, tablinks;
                tabcontent = document.getElementsByClassName("tab-content");
                for (i = 0; i < tabcontent.length; i++) { tabcontent[i].style.display = "none"; }
                tablinks = document.getElementsByClassName("tab-link");
                for (i = 0; i < tablinks.length; i++) { tablinks[i].className = tablinks[i].className.replace(" active", ""); }
                document.getElementById(tabName).style.display = "block";
                evt.currentTarget.className += " active";
            }
        </script>
    {% endif %}
</body>
</html>
"""

if __name__ == '__main__':
    load_data()
    app.run(debug=True, port=5050, use_reloader=False)
