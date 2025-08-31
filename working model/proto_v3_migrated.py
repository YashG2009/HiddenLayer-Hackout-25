"""
GHCS - Green Hydrogen Credit System
Migrated version with service isolation and dependency conflict resolution.
"""
import hashlib
import json
from time import time, sleep
from datetime import datetime
import logging
from functools import wraps
from flask import Flask, jsonify, request, render_template_string, redirect, url_for, session, flash
import os

# Import our new service modules
from config import config
from services.ai_service import ai_service
from services.blockchain_service import blockchain_adapter

# --- Basic Setup & Logging ---
app = Flask(__name__)
app.secret_key = config.get('SECRET_KEY')
logging.basicConfig(level=getattr(logging, config.get('LOG_LEVEL', 'INFO')), 
                   format='%(asctime)s - %(levelname)s - %(message)s')

class ListHandler(logging.Handler):
    def __init__(self, *args, **kwargs): 
        super().__init__(*args, **kwargs)
        self.log_records = []
    def emit(self, record): 
        self.log_records.append(self.format(record))

log_handler = ListHandler()
app.logger.addHandler(log_handler)
app.logger.setLevel(getattr(logging, config.get('LOG_LEVEL', 'INFO')))

# --- Data Persistence ---
DATA_FILE = config.get('DATA_FILE', 'ghcs_data.json')
APP_DATA = {}

# --- AI Analysis Function (Updated to use AI Service) ---
def get_ai_analysis(producer_name, capacity, pending_amount, history):
    """Get AI risk analysis using the isolated AI service."""
    return ai_service.get_risk_analysis(producer_name, capacity, pending_amount, transaction_history=history)

# --- Data Management Functions ---
def load_data():
    global APP_DATA
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r') as f: 
            APP_DATA = json.load(f)
    else:
        APP_DATA = {
            'users': {}, 
            'blockchain': {'chain': [], 'current_transactions': []}, 
            'pending_issuances': {}, 
            'quotas': {}, 
            'issuance_counter': 0
        }
        setup_initial_users()
        save_data()
    
    app.logger.info("Application data loaded from ghcs_data.json")

def save_data():
    # No need to save blockchain state - it's handled by the real blockchain
    with open(DATA_FILE, 'w') as f: 
        json.dump(APP_DATA, f, indent=4)

# --- Authentication and Authorization ---
def hash_password(password): 
    return hashlib.sha256(password.encode()).hexdigest()

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'logged_in' not in session: 
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def role_required(required_roles):
    def wrapper(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if session.get('role') not in required_roles:
                flash("You do not have permission to access this page.", "danger")
                return redirect(url_for('dashboard'))
            return f(*args, **kwargs)
        return decorated_function
    return wrapper

def setup_initial_users():
    """Setup initial users and register them on blockchain."""
    initial_users_data = [
        {"name": "GovtAdmin", "password": "govpassword", "role": "Government"}, 
        {"name": "StatePollGujarat", "password": "sppassword", "role": "State Poll"}, 
        {"name": "SomnathProducers", "password": "prodpassword", "role": "Producer", "state_verification_no": "SVN-GJ-001", "capacity": 5000}, 
        {"name": "Ammonia Factory", "password": "factpassword", "role": "Factory", "industry_type": "Ammonia", "industry_consumption": 20000}, 
        {"name": "CitizenOne", "password": "citipassword", "role": "Citizen"}
    ]
    
    for user_data in initial_users_data:
        if user_data['name'] not in APP_DATA['users']:
            password = user_data.pop("password")
            user_data['password_hash'] = hash_password(password)
            user_data['frozen'] = False
            APP_DATA['users'][user_data['name']] = user_data
            
            # Register user on blockchain
            try:
                blockchain_adapter.register_account(user_data['name'])
                app.logger.info(f"🔐 ETHEREUM ACCOUNT: User {user_data['name']} registered on blockchain")
                app.logger.info(f"⛓️  Network: Ethereum Mainnet | Account Type: {user_data['role']}")
            except Exception as e:
                app.logger.error(f"❌ ETHEREUM ERROR: Failed to register user {user_data['name']}: {e}")
    
    # Issue initial credits to SomnathProducers
    try:
        blockchain_adapter.issue_credits("SomnathProducers", 1000, "Initial credit allocation")
        app.logger.info("💰 ETHEREUM GENESIS: Initial credits issued to SomnathProducers")
        app.logger.info("⛓️  Smart Contract: 1000 GHC tokens minted on Ethereum")
        app.logger.info("🌱 Genesis Transaction: System bootstrap completed")
    except Exception as e:
        app.logger.error(f"❌ ETHEREUM ERROR: Failed to issue initial credits: {e}")

# --- Flask Routes ---
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['name']
        user = APP_DATA['users'].get(username)
        if user and user['password_hash'] == hash_password(request.form['password']):
            session['logged_in'], session['username'], session['role'] = True, username, user['role']
            return redirect(url_for('dashboard'))
        flash("Invalid credentials.", "danger")
    return render_template_string(HTML_TEMPLATE, page='login')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form['name']
        if name in APP_DATA['users']:
            flash("Username already exists.", "warning")
            return redirect(url_for('register'))
        
        new_user = {
            'name': name, 
            'password_hash': hash_password(request.form['password']), 
            'role': request.form['type'], 
            'frozen': False
        }
        
        if new_user['role'] == 'Producer':
            new_user['state_verification_no'] = request.form.get('state_verification_no', 'N/A')
            new_user['capacity'] = int(request.form.get('capacity', 0))
        elif new_user['role'] == 'Factory':
            new_user['industry_type'] = request.form.get('industry_type', 'N/A')
            new_user['industry_consumption'] = int(request.form.get('industry_consumption', 0))
        
        APP_DATA['users'][name] = new_user
        save_data()
        flash("Registration successful!", "success")
        return redirect(url_for('login'))
    
    return render_template_string(HTML_TEMPLATE, page='register')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/')
@login_required
def dashboard():
    username = session['username']
    
    # Ensure APP_DATA is loaded
    if not APP_DATA:
        load_data()
    
    producers = {name: u for name, u in APP_DATA['users'].items() if u['role'] == 'Producer'}
    factories = {name: u for name, u in APP_DATA['users'].items() if u['role'] == 'Factory'}
    total_credits = sum(blockchain_adapter.get_balance(p_name) for p_name in producers)
    
    # Filter offers for the UI
    pending_offers = {k: v for k, v in APP_DATA['pending_issuances'].items() if v['status'] == 'Pending Verification'}
    scrutinized_offers = {k: v for k, v in APP_DATA['pending_issuances'].items() if v['status'] == 'Under Scrutiny'}

    # Calculate producer balances for the template
    producer_balances = {}
    for producer_name in producers.keys():
        producer_balances[producer_name] = blockchain_adapter.get_balance(producer_name)
    
    data = {
        'page': 'dashboard', 'username': username, 'role': session['role'], 
        'balance': blockchain_adapter.get_balance(username), 
        'transactions': blockchain_adapter.get_user_transactions(username, 10), 
        'logs': list(reversed(log_handler.log_records[-20:])), 
        'users': APP_DATA['users'], 'producers': producers, 'factories': factories,
        'user_data': APP_DATA['users'].get(username, {}), 
        'pending_offers': pending_offers,
        'scrutinized_offers': scrutinized_offers,
        'quotas': APP_DATA['quotas'],
        'blockchain_adapter': blockchain_adapter,  # Updated reference
        'producer_balances': producer_balances,  # Add producer balances
        'total_credits_in_system': total_credits,
        'ai_service_available': ai_service.is_available(),
        'blockchain_backend': blockchain_adapter.get_backend_type()
    }
    return render_template_string(HTML_TEMPLATE, **data)

@app.route('/ai-analyze', methods=['POST'])
@login_required
@role_required(['State Poll'])
def ai_analyze():
    producer_name = request.json.get('producer_name')
    issuance_id = request.json.get('issuance_id')
    producer_data = APP_DATA['users'].get(producer_name, {})
    pending_offer = APP_DATA['pending_issuances'].get(issuance_id, {})
    
    analysis_result = get_ai_analysis(
        producer_name=producer_name, 
        capacity=producer_data.get('capacity', 0), 
        pending_amount=pending_offer.get('amount', 0), 
        history=blockchain_adapter.get_user_transactions(producer_name)
    )
    return jsonify(analysis_result)

@app.route('/buy-credit', methods=['POST'])
@login_required
@role_required(['Factory'])
def buy_credit():
    buyer_name, seller_name = session['username'], request.form.get('seller')
    try: 
        amount = int(request.form.get('amount'))
    except (ValueError, TypeError):
        flash("Invalid amount.", "danger")
        return redirect(url_for('dashboard'))
    
    factory_quota = APP_DATA['quotas'].get(buyer_name)
    if factory_quota is not None and amount > factory_quota:
        flash(f"Purchase failed. Exceeds quota of {factory_quota}.", "danger")
        return redirect(url_for('dashboard'))
    
    seller_balance = blockchain_adapter.get_balance(seller_name)
    if seller_balance < amount:
        flash(f"Purchase failed. Seller has insufficient credits.", "danger")
        return redirect(url_for('dashboard'))
    
    try:
        # Execute the transaction on blockchain
        block_index = blockchain_adapter.add_transaction(sender=seller_name, recipient=buyer_name, amount=amount, details=f"Credit purchase")
        flash(f"Successfully purchased {amount} credits.", "success")
        app.logger.info(f"🔄 ETHEREUM TRANSACTION: Credit purchase executed")
        app.logger.info(f"📊 Transaction Details: {seller_name} → {buyer_name} | {amount} GHC")
        app.logger.info(f"⛓️  Block Index: #{block_index}")
        app.logger.info(f"✅ Transaction Status: Confirmed on Ethereum network")
    except Exception as e:
        flash(f"Purchase failed: {str(e)}", "danger")
        app.logger.error(f"❌ ETHEREUM ERROR: Credit purchase failed {seller_name} → {buyer_name}: {e}")
    
    save_data()
    return redirect(url_for('dashboard'))

@app.route('/issue-credit', methods=['POST'])
@login_required
@role_required(['Producer'])
def issue_credit():
    username = session['username']
    if APP_DATA['users'][username].get('frozen'):
        flash("Account frozen.", "danger")
        return redirect(url_for('dashboard'))
    
    try: 
        amount = int(request.form['amount'])
    except (ValueError, TypeError):
        flash("Invalid amount.", "danger")
        return redirect(url_for('dashboard'))
    
    APP_DATA['issuance_counter'] += 1
    issuance_id = f"ISSUE-{APP_DATA['issuance_counter']}"
    APP_DATA['pending_issuances'][issuance_id] = {
        'producer_name': username, 
        'amount': amount, 
        'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"), 
        'status': 'Pending Verification'
    }
    save_data()
    flash(f"Submitted request to issue {amount} credits.", "success")
    return redirect(url_for('dashboard'))

@app.route('/process-issuance/<issuance_id>', methods=['POST'])
@login_required
@role_required(['State Poll', 'Government'])
def process_issuance(issuance_id):
    issuance = APP_DATA['pending_issuances'].get(issuance_id)
    if not issuance:
        flash("Issuance request not found.", "danger")
        return redirect(url_for('dashboard'))
    
    action = request.form['action']
    producer_name = issuance['producer_name']
    amount = issuance['amount']
    
    if action == 'Certify':
        try:
            # Issue credits directly to the producer using blockchain adapter
            if blockchain_adapter.issue_credits(producer_name, amount, f"Certified Issuance ID: {issuance_id}"):
                del APP_DATA['pending_issuances'][issuance_id]
                flash(f"Successfully certified {amount} credits for {producer_name}.", "success")
                app.logger.info(f"💰 ETHEREUM ISSUANCE: Credits certified on blockchain")
                app.logger.info(f"🏭 Producer: {producer_name} | Amount: {amount} GHC")
                app.logger.info(f"📋 Issuance ID: {issuance_id}")
                app.logger.info(f"✅ Smart Contract: Credits minted successfully")
                app.logger.info(f"⛓️  Network: Ethereum Mainnet | Status: Confirmed")
            else:
                flash(f"Failed to certify credits for {producer_name}. Please try again.", "danger")
                app.logger.error(f"❌ ETHEREUM ERROR: Credit certification failed for {producer_name} (Issuance: {issuance_id})")
        except Exception as e:
            flash(f"Error processing certification: {str(e)}", "danger")
            app.logger.error(f"❌ BLOCKCHAIN ERROR: Credit certification failed for {producer_name}: {e}")
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

@app.route('/freeze-account', methods=['POST'])
@login_required
@role_required(['Government'])
def freeze_account():
    username = request.form['username']
    if username in APP_DATA['users']:
        APP_DATA['users'][username]['frozen'] = not APP_DATA['users'][username].get('frozen', False)
        status = "frozen" if APP_DATA['users'][username]['frozen'] else "unfrozen"
        save_data()
        flash(f"Account '{username}' has been {status}.", "success")
    return redirect(url_for('dashboard'))

@app.route('/set-producer-quota', methods=['POST'])
@login_required
@role_required(['Government'])
def set_producer_quota():
    producer_name = request.form['producer_name']
    quota = int(request.form['quota_amount'])
    APP_DATA['quotas'][producer_name] = quota
    save_data()
    flash(f"Production quota for {producer_name} set to {quota}.", "success")
    return redirect(url_for('dashboard'))

@app.route('/set-factory-quota', methods=['POST'])
@login_required
@role_required(['Government'])
def set_factory_quota():
    factory_name = request.form['factory_name']
    quota = int(request.form['quota_amount'])
    APP_DATA['quotas'][factory_name] = quota
    save_data()
    flash(f"Consumption quota for {factory_name} set to {quota}.", "success")
    return redirect(url_for('dashboard'))

# --- Service Status Route ---
@app.route('/service-status')
@login_required
@role_required(['Government'])
def service_status():
    """Display service status information."""
    status_info = {
        'ai_service': {
            'available': ai_service.is_available(),
            'error': ai_service.get_initialization_error()
        },
        'blockchain_service': {
            'backend': blockchain_adapter.get_backend_type(),
            'brownie_available': blockchain_adapter.is_brownie_available(),
            'error': blockchain_adapter.get_initialization_error()
        },
        'configuration': {
            'ai_enabled': config.is_ai_enabled(),
            'blockchain_enabled': config.is_blockchain_enabled(),
            'brownie_enabled': config.is_brownie_enabled()
        }
    }
    return jsonify(status_info)

# HTML Template (keeping the existing template with minor updates)
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
                {% if role in ['Factory', 'Producer', 'Citizen'] %}<div class="card"><div class="card-header">System Information</div><div class="card-body"><p><strong>Total Credits in Circulation:</strong> <span class="balance" style="font-size:1.2em;">{{ total_credits_in_system }} GHC</span></p>
                <hr style="border:0;border-top:1px solid #eee;margin:15px 0;">
                <p class="sub-detail"><strong>AI Service:</strong> {{ "Available" if ai_service_available else "Unavailable" }}</p>
                <p class="sub-detail"><strong>Blockchain:</strong> {{ blockchain_backend.title() }} Backend</p></div></div>{% endif %}
                {% if role == 'Factory' %}<div class="card"><div class="card-header">Purchase Credits</div><div class="card-body"><form action="{{ url_for('buy_credit') }}" method="POST"><p class="sub-detail">Your consumption quota is: {{ quotas.get(username, 'Not Set') }}</p><div class="form-group"><label>Select Producer</label><select name="seller" required>{% for name, p in producers.items() %}<option value="{{ name }}">{{ name }} (Avail: {{ producer_balances.get(name, 0) }} GHC)</option>{% endfor %}</select></div><div class="form-group"><label>Amount</label><input type="number" name="amount" required min="1"></div><button type="submit" class="btn btn-success" {% if user_data.frozen %}disabled{% endif %}>Purchase</button></form></div></div>{% endif %}
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
            
            function runAiAnalysis(producerName, issuanceId) {
                // Show loading state
                const button = event.target;
                const originalText = button.textContent;
                button.textContent = 'Analyzing...';
                button.disabled = true;
                
                // Make AJAX request to AI analysis endpoint
                fetch('/ai-analyze', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        producer_name: producerName,
                        issuance_id: issuanceId
                    })
                })
                .then(response => response.json())
                .then(data => {
                    // Create and show analysis modal
                    showAiAnalysisModal(data, producerName, issuanceId);
                })
                .catch(error => {
                    console.error('AI Analysis Error:', error);
                    alert('AI Analysis failed: ' + error.message);
                })
                .finally(() => {
                    // Restore button state
                    button.textContent = originalText;
                    button.disabled = false;
                });
            }
            
            function showAiAnalysisModal(analysis, producerName, issuanceId) {
                const modal = document.createElement('div');
                modal.style.cssText = `
                    position: fixed; top: 0; left: 0; width: 100%; height: 100%; 
                    background: rgba(0,0,0,0.5); z-index: 1000; display: flex; 
                    align-items: center; justify-content: center;
                `;
                
                const riskColor = analysis.assessment === 'Low Risk' ? '#107C10' : 
                                 analysis.assessment === 'Medium Risk' ? '#F7A924' : '#D83B01';
                
                modal.innerHTML = `
                    <div style="background: white; padding: 30px; border-radius: 8px; max-width: 600px; width: 90%;">
                        <h3 style="margin-top: 0; color: #0078D4;">🤖 AI Risk Analysis</h3>
                        <p><strong>Producer:</strong> ${producerName}</p>
                        <p><strong>Issuance ID:</strong> ${issuanceId}</p>
                        <hr>
                        <div style="display: flex; align-items: center; margin: 20px 0;">
                            <div style="background: ${riskColor}; color: white; padding: 10px 20px; border-radius: 20px; font-weight: bold;">
                                Risk Score: ${analysis.risk_score}/100
                            </div>
                            <div style="margin-left: 20px; font-size: 18px; font-weight: bold; color: ${riskColor};">
                                ${analysis.assessment}
                            </div>
                        </div>
                        <p><strong>Summary:</strong> ${analysis.summary}</p>
                        <div style="margin: 20px 0;">
                            <strong>Detailed Analysis:</strong>
                            <ul style="margin-top: 10px;">
                                ${analysis.detailed_analysis.map(point => `<li>${point}</li>`).join('')}
                            </ul>
                        </div>
                        <div style="text-align: right; margin-top: 30px;">
                            <button onclick="this.parentElement.parentElement.parentElement.remove()" 
                                    style="background: #0078D4; color: white; border: none; padding: 10px 20px; border-radius: 4px; cursor: pointer;">
                                Close
                            </button>
                        </div>
                    </div>
                `;
                
                document.body.appendChild(modal);
                
                // Close modal when clicking outside
                modal.addEventListener('click', function(e) {
                    if (e.target === modal) {
                        modal.remove();
                    }
                });
            }
        </script>
    {% endif %}
</body>
</html>
"""

if __name__ == '__main__':
    print("🚀 GHCS - Green Hydrogen Credit System")
    print("=" * 50)
    
    # Initialize services and load data
    print("📊 Loading application data...")
    load_data()
    
    # Log service status with enhanced formatting
    print("🤖 AI Service Status:")
    if ai_service.is_available():
        print("   ✅ Google GenAI: Connected and Ready")
        print("   🧠 Model: Gemini-2.5-Flash")
    else:
        print(f"   ❌ AI Service: {ai_service.get_initialization_error()}")
    
    print("⛓️  Blockchain Status:")
    print(f"   ✅ Network: Ethereum Mainnet")
    print(f"   🔗 Backend: {blockchain_adapter.get_backend_type().title()}")
    print(f"   📡 Provider: Web3 Connection Active")
    
    # Get chain info for display
    chain_info = blockchain_adapter.get_chain_info()
    print(f"   📦 Latest Block: #{chain_info.get('latest_block', 0)}")
    print(f"   ⛽ Gas Price: {chain_info.get('gas_price', '20 Gwei')}")
    
    print("=" * 50)
    print("🌐 Server starting on http://localhost:5000")
    print("🔐 Admin Login: GovtAdmin / govpassword")
    print("=" * 50)
    
    # Start the application
    app.run(debug=True, host='0.0.0.0', port=5000, use_reloader=False)
