from flask import Flask, jsonify, request
from werkzeug.security import check_password_hash, generate_password_hash
import os
import json
from datetime import datetime

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-key-change-in-production')

# In-memory data store (in production, use a real database)
users_db = {}
customers_db = {}
leads_db = {}
sales_db = {}
user_sessions = {}

# Demo users
users_db['admin'] = {
    'password': generate_password_hash('admin123'),
    'email': 'admin@crm.com'
}
users_db['user1'] = {
    'password': generate_password_hash('user123'),
    'email': 'user1@crm.com'
}

@app.route('/')
def index():
    return jsonify({
        'message': 'CRM Application API',
        'version': '1.0.0',
        'endpoints': {
            'auth': '/login',
            'dashboard': '/dashboard',
            'customers': '/customers',
            'leads': '/leads',
            'sales': '/sales'
        }
    })

@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    
    if not username or not password:
        return jsonify({'error': 'Missing username or password'}), 400
    
    user = users_db.get(username)
    if user and check_password_hash(user['password'], password):
        session_token = f"token_{username}_{datetime.now().timestamp()}"
        user_sessions[session_token] = username
        return jsonify({
            'success': True,
            'message': f'Welcome {username}!',
            'token': session_token,
            'username': username
        }), 200
    
    return jsonify({'error': 'Invalid credentials'}), 401

def verify_token(token):
    return user_sessions.get(token)

@app.route('/dashboard')
def dashboard():
    token = request.headers.get('Authorization', '').replace('Bearer ', '')
    username = verify_token(token)
    
    if not username:
        return jsonify({'error': 'Unauthorized'}), 401
    
    return jsonify({
        'username': username,
        'stats': {
            'customers': len([c for c in customers_db.values() if c.get('username') == username]),
            'leads': len([l for l in leads_db.values() if l.get('username') == username]),
            'sales': len([s for s in sales_db.values() if s.get('username') == username])
        }
    }), 200

@app.route('/customers', methods=['GET', 'POST'])
def customers():
    token = request.headers.get('Authorization', '').replace('Bearer ', '')
    username = verify_token(token)
    
    if not username:
        return jsonify({'error': 'Unauthorized'}), 401
    
    if request.method == 'POST':
        data = request.get_json()
        customer_id = f"cust_{len(customers_db)+1}"
        customers_db[customer_id] = {
            'id': customer_id,
            'name': data.get('name'),
            'email': data.get('email'),
            'phone': data.get('phone'),
            'company': data.get('company'),
            'status': 'active',
            'username': username,
            'created_at': datetime.now().isoformat()
        }
        return jsonify(customers_db[customer_id]), 201
    
    user_customers = [c for c in customers_db.values() if c.get('username') == username]
    return jsonify({'customers': user_customers}), 200

@app.route('/leads', methods=['GET', 'POST'])
def leads():
    token = request.headers.get('Authorization', '').replace('Bearer ', '')
    username = verify_token(token)
    
    if not username:
        return jsonify({'error': 'Unauthorized'}), 401
    
    if request.method == 'POST':
        data = request.get_json()
        lead_id = f"lead_{len(leads_db)+1}"
        leads_db[lead_id] = {
            'id': lead_id,
            'name': data.get('name'),
            'email': data.get('email'),
            'phone': data.get('phone'),
            'company': data.get('company'),
            'value': data.get('value', 0),
            'status': 'new',
            'username': username,
            'created_at': datetime.now().isoformat()
        }
        return jsonify(leads_db[lead_id]), 201
    
    user_leads = [l for l in leads_db.values() if l.get('username') == username]
    return jsonify({'leads': user_leads}), 200

@app.route('/sales', methods=['GET', 'POST'])
def sales():
    token = request.headers.get('Authorization', '').replace('Bearer ', '')
    username = verify_token(token)
    
    if not username:
        return jsonify({'error': 'Unauthorized'}), 401
    
    if request.method == 'POST':
        data = request.get_json()
        sale_id = f"sale_{len(sales_db)+1}"
        sales_db[sale_id] = {
            'id': sale_id,
            'title': data.get('title'),
            'amount': data.get('amount', 0),
            'status': 'pending',
            'username': username,
            'created_at': datetime.now().isoformat()
        }
        return jsonify(sales_db[sale_id]), 201
    
    user_sales = [s for s in sales_db.values() if s.get('username') == username]
    return jsonify({'sales': user_sales}), 200

@app.route('/health')
def health():
    return jsonify({'status': 'healthy'}), 200

if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
