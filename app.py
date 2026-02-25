from flask import Flask, jsonify, request, render_template_string, redirect, session, make_response
from werkzeug.security import check_password_hash, generate_password_hash
import os
from datetime import datetime

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-key-change-in-production-12345')

# In-memory data
users_db = {}
customers_db = {}
leads_db = {}
sales_db = {}

users_db['admin'] = {'password': generate_password_hash('admin123'), 'email': 'admin@crm.com'}
users_db['user1'] = {'password': generate_password_hash('user123'), 'email': 'user1@crm.com'}

# Login page HTML
LOGIN_HTML = '''
<!DOCTYPE html>
<html>
<head><title>CRM Login</title>
<style>* {margin:0; padding:0; box-sizing:border-box;}
body {font-family: Arial; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); min-height:100vh; display:flex; justify-content:center; align-items:center;}
.container {background: white; padding: 40px; border-radius: 10px; box-shadow: 0 10px 25px rgba(0,0,0,0.2); width: 100%; max-width: 400px;}
h1 {color: #667eea; text-align: center; margin-bottom: 30px;}
.form-group {margin-bottom: 20px;}
label {display: block; margin-bottom: 8px; color: #333; font-weight: 500;}
input {width: 100%; padding: 12px; border: 1px solid #ddd; border-radius: 5px; font-size: 14px;}
input:focus {outline: none; border-color: #667eea;}
.btn {width: 100%; padding: 12px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; border: none; border-radius: 5px; font-size: 16px; cursor: pointer;}
.btn:hover {opacity: 0.9;}
.error {background: #f8d7da; color: #721c24; padding: 10px; border-radius: 5px; margin-bottom: 20px; display:none;}
.info {background: #e7f3ff; padding: 15px; border-radius: 5px; margin-bottom: 20px; font-size: 13px; color: #0066cc;}
</style></head>
<body><div class="container"><h1>🔐 CRM Login</h1><p style="text-align:center; color:#666; margin-bottom:20px;">Ahsaz Global Solutions</p>
<div class="info"><strong>Demo:</strong> admin / admin123</div>
<div id="error" class="error"></div>
<form method="POST"><div class="form-group"><label>Username</label><input type="text" name="username" required></div>
<div class="form-group"><label>Password</label><input type="password" name="password" required></div>
<button type="submit" class="btn">Login</button></form></div></body></html>
'''

# Dashboard HTML
DASHBOARD_HTML = '''
<!DOCTYPE html>
<html>
<head><title>CRM Dashboard</title>
<style>* {margin:0; padding:0; box-sizing:border-box;}
body {font-family: Arial; background: #f5f5f5;}
.navbar {background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 15px 30px; display: flex; justify-content: space-between; align-items: center;}
.navbar h1 {font-size: 24px;}
.navbar a {color: white; text-decoration: none; margin-left: 20px; padding: 8px 15px; border-radius: 5px; background: rgba(255,255,255,0.2);}
.navbar a:hover {background: rgba(255,255,255,0.3);}
.container {max-width: 1200px; margin: 40px auto; padding: 0 20px;}
.welcome {background: white; padding: 30px; border-radius: 10px; margin-bottom: 30px; box-shadow: 0 2px 10px rgba(0,0,0,0.1);}
.stats {display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 20px; margin-top: 20px;}
.stat-card {background: white; padding: 25px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); text-align: center;}
.stat-card h3 {color: #667eea; font-size: 36px; margin-bottom: 10px;}
.stat-card p {color: #666; font-size: 14px;}
.section {background: white; padding: 30px; border-radius: 10px; margin-bottom: 20px; box-shadow: 0 2px 10px rgba(0,0,0,0.1);}
.section h2 {color: #667eea; margin-bottom: 20px;}
.btn {padding: 10px 20px; background: #667eea; color: white; border: none; border-radius: 5px; cursor: pointer; text-decoration: none; display: inline-block;}
.btn:hover {background: #764ba2;}
table {width: 100%; border-collapse: collapse;}
th {background: #f5f5f5; padding: 12px; text-align: left; border-bottom: 2px solid #ddd;}
td {padding: 12px; border-bottom: 1px solid #ddd;}
</style></head>
<body>
<div class="navbar"><h1>CRM Dashboard</h1><div><a href="/customers_page">Customers</a><a href="/leads_page">Leads</a><a href="/sales_page">Sales</a><a href="/logout">Logout</a></div></div>
<div class="container"><div class="welcome"><h2>Welcome, {{ username }}!</h2><p>Manage your CRM from here</p></div>
<div class="stats"><div class="stat-card"><h3>{{ customers }}</h3><p>Total Customers</p></div>
<div class="stat-card"><h3>{{ leads }}</h3><p>Total Leads</p></div>
<div class="stat-card"><h3>{{ sales }}</h3><p>Total Sales</p></div></div></div></body></html>
'''

CUSTOMERS_HTML = '''
<!DOCTYPE html>
<html><head><title>Customers</title>
<style>* {margin:0; padding:0; box-sizing:border-box;} body {font-family: Arial; background: #f5f5f5;}
.navbar {background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 15px 30px; display: flex; justify-content: space-between; align-items: center;}
.navbar h1 {font-size: 24px;} .navbar a {color: white; text-decoration: none; margin-left: 20px; padding: 8px 15px; border-radius: 5px; background: rgba(255,255,255,0.2);}
.navbar a:hover {background: rgba(255,255,255,0.3);} .container {max-width: 1200px; margin: 40px auto; padding: 0 20px;}
.section {background: white; padding: 30px; border-radius: 10px; margin-bottom: 20px; box-shadow: 0 2px 10px rgba(0,0,0,0.1);}
.section h2 {color: #667eea; margin-bottom: 20px;} table {width: 100%; border-collapse: collapse;}
th {background: #f5f5f5; padding: 12px; text-align: left; border-bottom: 2px solid #ddd;}
td {padding: 12px; border-bottom: 1px solid #ddd;} .btn {padding: 10px 20px; background: #667eea; color: white; border: none; border-radius: 5px; cursor: pointer;}
.btn:hover {background: #764ba2;} .form-group {margin-bottom: 15px;} label {display: block; margin-bottom: 5px; font-weight: 500;}
input {width: 100%; padding: 10px; border: 1px solid #ddd; border-radius: 5px;}</style></head>
<body><div class="navbar"><h1>Customers</h1><div><a href="/dashboard_page">Dashboard</a><a href="/leads_page">Leads</a><a href="/sales_page">Sales</a><a href="/logout">Logout</a></div></div>
<div class="container"><div class="section"><h2>Add New Customer</h2><form method="POST">
<div class="form-group"><label>Name</label><input name="name" required></div>
<div class="form-group"><label>Email</label><input type="email" name="email" required></div>
<div class="form-group"><label>Phone</label><input name="phone"></div>
<div class="form-group"><label>Company</label><input name="company"></div>
<button type="submit" class="btn">Add Customer</button></form></div>
<div class="section"><h2>Customer List</h2><table><tr><th>Name</th><th>Email</th><th>Phone</th><th>Company</th></tr>
{% for c in customers %}<tr><td>{{ c.name }}</td><td>{{ c.email }}</td><td>{{ c.phone }}</td><td>{{ c.company }}</td></tr>{% endfor %}
</table></div></div></body></html>
'''

@app.route('/')
def index():
    if 'username' in session:
        return redirect('/dashboard_page')
    return render_template_string(LOGIN_HTML)

@app.route('/', methods=['POST'])
def login():
    username = request.form.get('username')
    password = request.form.get('password')
    user = users_db.get(username)
    if user and check_password_hash(user['password'], password):
        session['username'] = username
        return redirect('/dashboard_page')
    return render_template_string(LOGIN_HTML.replace('</head>', '<script>document.getElementById("error").style.display="block"; document.getElementById("error").textContent="Invalid credentials";</script></head>'))

@app.route('/dashboard_page')
def dashboard_page():
    if 'username' not in session:
        return redirect('/')
    username = session['username']
    return render_template_string(DASHBOARD_HTML, 
        username=username,
        customers=len([c for c in customers_db.values() if c.get('username') == username]),
        leads=len([l for l in leads_db.values() if l.get('username') == username]),
        sales=len([s for s in sales_db.values() if s.get('username') == username]))

@app.route('/customers_page', methods=['GET', 'POST'])
def customers_page():
    if 'username' not in session:
        return redirect('/')
    username = session['username']
    if request.method == 'POST':
        cust_id = f"cust_{len(customers_db)+1}"
        customers_db[cust_id] = {
            'id': cust_id, 'name': request.form.get('name'),
            'email': request.form.get('email'), 'phone': request.form.get('phone'),
            'company': request.form.get('company'), 'username': username,
            'created_at': datetime.now().isoformat()}
    user_customers = [c for c in customers_db.values() if c.get('username') == username]
    return render_template_string(CUSTOMERS_HTML, customers=user_customers)

@app.route('/leads_page')
def leads_page():
    if 'username' not in session:
        return redirect('/')
    return '<h1>Leads Page - Coming Soon</h1><a href="/dashboard_page">Back to Dashboard</a>'

@app.route('/sales_page')
def sales_page():
    if 'username' not in session:
        return redirect('/')
    return '<h1>Sales Page - Coming Soon</h1><a href="/dashboard_page">Back to Dashboard</a>'

@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect('/')

# API endpoints for compatibility
@app.route('/login', methods=['POST'])
def api_login():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    user = users_db.get(username)
    if user and check_password_hash(user['password'], password):
        return jsonify({'success': True, 'message': f'Welcome {username}!', 'token': f'token_{username}', 'username': username}), 200
    return jsonify({'error': 'Invalid credentials'}), 401

@app.route('/dashboard')
def api_dashboard():
    username = request.headers.get('Authorization', '').replace('Bearer ', '').split('_')[1] if 'Bearer' in request.headers.get('Authorization', '') else None
    if not username:
        return jsonify({'error': 'Unauthorized'}), 401
    return jsonify({'username': username, 'stats': {'customers': len(customers_db), 'leads': len(leads_db), 'sales': len(sales_db)}}), 200

@app.route('/health')
def health():
    return jsonify({'status': 'healthy'}), 200

if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
