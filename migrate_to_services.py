"""
Migration script to update the existing GHCS application to use the new service architecture.
This script creates a new version of the application with service isolation.
"""
import shutil
import os
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_migrated_application():
    """Create the migrated version of the application."""
    
    # Read the original application
    with open('proto v-2.py', 'r', encoding='utf-8') as f:
        original_content = f.read()
    
    # Create the new application content with service isolation
    migrated_content = '''"""
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
    return ai_service.get_risk_analysis(producer_name, capacity, pending_amount, history)

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
    
    # Initialize blockchain adapter with existing data
    if APP_DATA['blockchain']['chain']:
        blockchain_adapter._simulated_blockchain.chain = APP_DATA['blockchain']['chain']
        blockchain_adapter._simulated_blockchain.current_transactions = APP_DATA['blockchain']['current_transactions']
    
    app.logger.info("Application data loaded from ghcs_data.json")

def save_data():
    # Save blockchain state back to APP_DATA
    if blockchain_adapter._simulated_blockchain:
        APP_DATA['blockchain']['chain'] = blockchain_adapter._simulated_blockchain.chain
        APP_DATA['blockchain']['current_transactions'] = blockchain_adapter._simulated_blockchain.current_transactions
    
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
    """Setup initial users and genesis transactions."""
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
    
    # Add genesis transaction
    blockchain_adapter.add_transaction("NETWORK_GENESIS", "SomnathProducers", 1000, "Initial credit allocation")
    blockchain_adapter.mine_block()

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
    producers = {name: u for name, u in APP_DATA['users'].items() if u['role'] == 'Producer'}
    factories = {name: u for name, u in APP_DATA['users'].items() if u['role'] == 'Factory'}
    total_credits = sum(blockchain_adapter.get_balance(p_name) for p_name in producers)
    
    # Filter offers for the UI
    pending_offers = {k: v for k, v in APP_DATA['pending_issuances'].items() if v['status'] == 'Pending Verification'}
    scrutinized_offers = {k: v for k, v in APP_DATA['pending_issuances'].items() if v['status'] == 'Under Scrutiny'}

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
    
    blockchain_adapter.add_transaction(sender=seller_name, recipient=buyer_name, amount=amount, details=f"Credit purchase")
    blockchain_adapter.mine_block()
    save_data()
    flash(f"Successfully purchased {amount} credits.", "success")
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
        blockchain_adapter.add_transaction("NETWORK_CERTIFIER", producer_name, amount, f"Certified Issuance ID: {issuance_id}")
        blockchain_adapter.mine_block()
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
'''

    # Add the HTML template from the original file
    # Find the HTML_TEMPLATE definition in the original content
    html_start = original_content.find('HTML_TEMPLATE = """')
    html_end = original_content.find('"""', html_start + 19) + 3
    html_template = original_content[html_start:html_end]
    
    # Update the HTML template to show service status
    updated_html_template = html_template.replace(
        '<p><strong>Total Credits in Circulation:</strong> <span class="balance" style="font-size:1.2em;">{{ total_credits_in_system }} GHC</span></p>',
        '''<p><strong>Total Credits in Circulation:</strong> <span class="balance" style="font-size:1.2em;">{{ total_credits_in_system }} GHC</span></p>
                <hr style="border:0;border-top:1px solid #eee;margin:15px 0;">
                <p class="sub-detail"><strong>AI Service:</strong> {{ "Available" if ai_service_available else "Unavailable" }}</p>
                <p class="sub-detail"><strong>Blockchain:</strong> {{ blockchain_backend.title() }} Backend</p>'''
    )
    
    migrated_content += updated_html_template + '''

if __name__ == '__main__':
    # Initialize services and load data
    load_data()
    
    # Log service status
    app.logger.info(f"AI Service Available: {ai_service.is_available()}")
    app.logger.info(f"Blockchain Backend: {blockchain_adapter.get_backend_type()}")
    
    # Start the application
    app.run(debug=True, host='0.0.0.0', port=5000)
'''
    
    return migrated_content

def main():
    """Run the migration."""
    logger.info("Starting migration to service-isolated architecture...")
    
    # Create backup of original file
    backup_name = 'proto v-2.py.backup'
    if not os.path.exists(backup_name):
        shutil.copy2('proto v-2.py', backup_name)
        logger.info(f"Created backup: {backup_name}")
    
    # Create migrated application
    migrated_content = create_migrated_application()
    
    # Write migrated application
    with open('proto_v3_migrated.py', 'w', encoding='utf-8') as f:
        f.write(migrated_content)
    
    logger.info("Migration completed successfully!")
    logger.info("New application created: proto_v3_migrated.py")
    logger.info("Original application backed up as: proto v-2.py.backup")
    logger.info("")
    logger.info("To test the migrated application:")
    logger.info("1. Run: python proto_v3_migrated.py")
    logger.info("2. Check service status at: http://localhost:5000/service-status")

if __name__ == "__main__":
    main()