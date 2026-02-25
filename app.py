from flask import Flask, jsonify, request, render_template_string
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

# HTML Login Page
LOGIN_HTML = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>CRM Login - Ahsaz Global Solutions</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); min-height: 100vh; display: flex; justify-content: center; align-items: center; }
        .container { background: white; padding: 40px; border-radius: 10px; box-shadow: 0 10px 25px rgba(0, 0, 0, 0.2); width: 100%; max-width: 400px; }
        .logo { text-align: center; margin-bottom: 30px; }
        .logo h1 { color: #667eea; font-size: 28px; margin-bottom: 5px; }
        .logo p { color: #666; font-size: 14px; }
        .form-group { margin-bottom: 20px; }
        .form-group label { display: block; margin-bottom: 8px; color: #333; font-weight: 500; }
        .form-group input { width: 100%; padding: 12px; border: 1px solid #ddd; border-radius: 5px; font-size: 14px; transition: border-color 0.3s; }
        .form-group input:focus { outline: none; border-color: #667eea; box-shadow: 0 0 5px rgba(102, 126, 234, 0.1); }
        .btn { width: 100%; padding: 12px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; border: none; border-radius: 5px; font-size: 16px; font-weight: 600; cursor: pointer; transition: transform 0.2s; }
        .btn:hover { transform: translateY(-2px); }
        .btn:active { transform: translateY(0); }
        .message { margin-top: 20px; padding: 15px; border-radius: 5px; text-align: center; display: none; }
        .success { background: #d4edda; color: #155724; border: 1px solid #c3e6cb; }
        .error { background: #f8d7da; color: #721c24; border: 1px solid #f5c6cb; }
        .token-box { margin-top: 20px; padding: 15px; background: #f8f9fa; border-radius: 5px; display: none; }
        .token-box h3 { color: #333; font-size: 14px; margin-bottom: 10px; }
        .token-box textarea { width: 100%; height: 100px; padding: 10px; border: 1px solid #ddd; border-radius: 5px; font-family: 'Courier New', monospace; font-size: 12px; resize: vertical; }
        .copy-btn { margin-top: 10px; padding: 8px 15px; background: #28a745; color: white; border: none; border-radius: 5px; cursor: pointer; font-size: 13px; }
        .copy-btn:hover { background: #218838; }
        .credentials { background: #e7f3ff; padding: 15px; border-radius: 5px; margin-bottom: 20px; font-size: 13px; color: #0066cc; }
        .credentials strong { display: block; margin-bottom: 5px; }
    </style>
</head>
<body>
    <div class="container">
        <div class="logo">
            <h1>🔐 CRM Login</h1>
            <p>Ahsaz Global Solutions</p>
        </div>
        <div class="credentials">
            <strong>Demo Credentials:</strong>
            Username: <code>admin</code> | Password: <code>admin123</code>
        </div>
        <form id="loginForm">
            <div class="form-group">
                <label for="username">Username</label>
                <input type="text" id="username" name="username" placeholder="Enter username" required>
            </div>
            <div class="form-group">
                <label for="password">Password</label>
                <input type="password" id="password" name="password" placeholder="Enter password" required>
            </div>
            <button type="submit" class="btn" id="loginBtn">Login</button>
        </form>
        <div id="message" class="message"></div>
        <div id="tokenBox" class="token-box">
            <h3>✅ Login Successful! Your Token:</h3>
            <textarea id="tokenText" readonly></textarea>
            <button class="copy-btn" onclick="copyToken()">Copy Token</button>
            <p style="margin-top: 10px; font-size: 12px; color: #666;">Use this token in the Authorization header for API requests</p>
        </div>
    </div>
    <script>
        const API_URL = window.location.origin;
        document.getElementById('loginForm').addEventListener('submit', async (e) => {
            e.preventDefault();
            const username = document.getElementById('username').value;
            const password = document.getElementById('password').value;
            const messageDiv = document.getElementById('message');
            const tokenBox = document.getElementById('tokenBox');
            const loginBtn = document.getElementById('loginBtn');
            loginBtn.disabled = true;
            loginBtn.textContent = 'Logging in...';
            messageDiv.style.display = 'none';
            tokenBox.style.display = 'none';
            try {
                const response = await fetch(API_URL + '/login', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ username: username, password: password })
                });
                const data = await response.json();
                if (response.ok && data.success) {
                    messageDiv.className = 'message success';
                    messageDiv.textContent = data.message;
                    messageDiv.style.display = 'block';
                    document.getElementById('tokenText').value = data.token;
                    tokenBox.style.display = 'block';
                    document.getElementById('loginForm').reset();
                    loginBtn.disabled = false;
                    loginBtn.textContent = 'Login';
                } else {
                    messageDiv.className = 'message error';
                    messageDiv.textContent = data.error || 'Login failed';
                    messageDiv.style.display = 'block';
                    loginBtn.disabled = false;
                    loginBtn.textContent = 'Login';
                }
            } catch (error) {
                messageDiv.className = 'message error';
                messageDiv.textContent = 'Connection error: ' + error.message;
                messageDiv.style.display = 'block';
                loginBtn.disabled = false;
                loginBtn.textContent = 'Login';
            }
        });
        function copyToken() {
            const tokenText = document.getElementById('tokenText');
            tokenText.select();
            document.execCommand('copy');
            alert('Token copied to clipboard!');
        }
    </script>
</body>
</html>
'''

@app.route('/')
def index():
    return render_template_string(LOGIN_HTML)

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
