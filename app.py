from flask import Flask, jsonify, request, render_template_string, redirect, session, send_file
from werkzeug.security import check_password_hash, generate_password_hash
import os
import pandas as pd
from datetime import datetime
import io

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'ahsaz-global-secret-key-2026')

# --- DATA STORAGE (In-memory for demo, resets on redeploy) ---
users_db = {'admin': {'password': generate_password_hash('admin123')}}
candidates_db = []

# --- CONFIGURATION ---
POSITION_OPTIONS = ["XPS Operator", "Trailer Driver", "AutoCAD Operator", "House Driver", "Nurse", "Machine Operator", "Engineer", "Bike Rider", "Delivery Driver", "Kitchen Staff", "Hospitality Staff"]
COUNTRY_OPTIONS = ["India", "Saudi Arabia", "UAE", "Qatar", "Oman", "Kuwait", "Bahrain"]
STATUS_OPTIONS = ["Application Received", "Interview Scheduled", "Shortlisted", "Selected", "Rejected", "On Hold"]
SOURCE_OPTIONS = ["Facebook Group", "WhatsApp", "Indeed", "LinkedIn", "Referral", "Job Portal"]

# --- HTML TEMPLATES ---
BASE_STYLE = '''
<style>
    * {box-sizing: border-box; margin: 0; padding: 0; font-family: 'Segoe UI', sans-serif;}
    body {background: #f4f7f6; color: #333;}
    .navbar {background: #667eea; color: white; padding: 1rem 2rem; display: flex; justify-content: space-between; align-items: center;}
    .navbar a {color: white; text-decoration: none; margin-left: 1.5rem; font-weight: 500;}
    .container {max-width: 1200px; margin: 2rem auto; padding: 0 1rem;}
    .card {background: white; padding: 2rem; border-radius: 8px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); margin-bottom: 2rem;}
    h2 {color: #667eea; margin-bottom: 1.5rem;}
    .form-grid {display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 1rem;}
    .form-group {margin-bottom: 1rem;}
    label {display: block; margin-bottom: 0.5rem; font-weight: bold; font-size: 0.9rem;}
    input, select, textarea {width: 100%; padding: 0.75rem; border: 1px solid #ddd; border-radius: 4px;}
    .btn {padding: 0.75rem 1.5rem; border: none; border-radius: 4px; cursor: pointer; font-weight: bold; text-decoration: none; display: inline-block;}
    .btn-primary {background: #667eea; color: white;}
    .btn-success {background: #48bb78; color: white;}
    .btn-danger {background: #f56565; color: white;}
    table {width: 100%; border-collapse: collapse; margin-top: 1rem;}
    th, td {padding: 1rem; text-align: left; border-bottom: 1px solid #eee;}
    th {background: #f8fafc;}
    .status-badge {padding: 0.25rem 0.5rem; border-radius: 999px; font-size: 0.8rem; font-weight: bold;}
    .Selected {background: #c6f6d5; color: #22543d;}
    .Rejected {background: #fed7d7; color: #822727;}
</style>
'''

LOGIN_HTML = BASE_STYLE + '''
<div style="height: 100vh; display: flex; align-items: center; justify-content: center; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);">
    <div class="card" style="width: 400px;">
        <h2 style="text-align: center;">🔐 Ahsaz CRM Login</h2>
        <form method="POST">
            <div class="form-group"><label>Username</label><input name="username" required></div>
            <div class="form-group"><label>Password</label><input type="password" name="password" required></div>
            <button type="submit" class="btn btn-primary" style="width: 100%;">Login</button>
        </form>
        <p style="text-align: center; margin-top: 1rem; color: #666;">Demo: admin / admin123</p>
    </div>
</div>
'''

DASHBOARD_HTML = BASE_STYLE + '''
<div class="navbar"><h1>🚀 Ahsaz Candidate CRM</h1><div><a href="/add">Add Candidate</a><a href="/view">View/Filter</a><a href="/logout">Logout</a></div></div>
<div class="container">
    <div class="card">
        <h2>Welcome, {{user}}!</h2>
        <div class="form-grid">
            <div class="card" style="text-align: center;"><h3>{{total}}</h3><p>Total Candidates</p></div>
            <div class="card" style="text-align: center;"><h3>{{selected}}</h3><p>Selected</p></div>
            <div class="card" style="text-align: center;"><h3>{{interview}}</h3><p>Interviews</p></div>
        </div>
    </div>
</div>
'''

ADD_HTML = BASE_STYLE + '''
<div class="navbar"><h1>🚀 Ahsaz CRM</h1><div><a href="/">Dashboard</a><a href="/view">View/Filter</a><a href="/logout">Logout</a></div></div>
<div class="container">
    <div class="card">
        <h2>Add New Candidate</h2>
        <form method="POST">
            <div class="form-grid">
                <div class="form-group"><label>Candidate Name</label><input name="name" required></div>
                <div class="form-group"><label>Phone</label><input name="phone"></div>
                <div class="form-group"><label>Email</label><input type="email" name="email"></div>
                <div class="form-group"><label>Position Applied</label>
                    <select name="position">{% for p in pos %}<option>{{p}}</option>{% endfor %}</select>
                </div>
                <div class="form-group"><label>Country</label>
                    <select name="country">{% for c in countries %}<option>{{c}}</option>{% endfor %}</select>
                </div>
                <div class="form-group"><label>Status</label>
                    <select name="status">{% for s in stats %}<option>{{s}}</option>{% endfor %}</select>
                </div>
                <div class="form-group"><label>Source</label>
                    <select name="source">{% for so in sources %}<option>{{so}}</option>{% endfor %}</select>
                </div>
                <div class="form-group"><label>Experience (Years)</label><input name="exp"></div>
            </div>
            <button type="submit" class="btn btn-success" style="margin-top: 1rem;">Save Candidate</button>
        </form>
    </div>
</div>
'''

VIEW_HTML = BASE_STYLE + '''
<div class="navbar"><h1>🚀 Ahsaz CRM</h1><div><a href="/">Dashboard</a><a href="/add">Add Candidate</a><a href="/logout">Logout</a></div></div>
<div class="container">
    <div class="card">
        <h2>Candidate Database</h2>
        <form method="GET" style="margin-bottom: 2rem;" class="form-grid">
            <input name="search" placeholder="Search name..." value="{{search}}">
            <select name="f_status"><option value="">All Status</option>{% for s in stats %}<option {% if f_status==s %}selected{%endif%}>{{s}}</option>{% endfor %}</select>
            <button type="submit" class="btn btn-primary">Apply Filters</button>
            <a href="/export" class="btn btn-success">Export to Excel</a>
        </form>
        <div style="overflow-x: auto;">
            <table>
                <tr><th>S.No</th><th>Name</th><th>Position</th><th>Country</th><th>Status</th><th>Actions</th></tr>
                {% for c in data %}
                <tr>
                    <td>{{loop.index}}</td><td>{{c.name}}</td><td>{{c.position}}</td><td>{{c.country}}</td>
                    <td><span class="status-badge {{c.status}}">{{c.status}}</span></td>
                    <td><a href="/edit/{{loop.index0}}" class="btn btn-primary" style="padding: 0.2rem 0.5rem; font-size: 0.8rem;">Edit</a></td>
                </tr>
                {% endfor %}
            </table>
        </div>
    </div>
</div>
'''

# --- ROUTES ---
@app.route('/')
def index():
    if 'user' not in session: return render_template_string(LOGIN_HTML)
    total = len(candidates_db)
    sel = len([c for c in candidates_db if c['status'] == 'Selected'])
    inter = len([c for c in candidates_db if 'Interview' in c['status']])
    return render_template_string(DASHBOARD_HTML, user=session['user'], total=total, selected=sel, interview=inter)

@app.route('/', methods=['POST'])
def login():
    u, p = request.form.get('username'), request.form.get('password')
    if u in users_db and check_password_hash(users_db[u]['password'], p):
        session['user'] = u
        return redirect('/')
    return "Invalid credentials"

@app.route('/add', methods=['GET', 'POST'])
def add():
    if 'user' not in session: return redirect('/')
    if request.method == 'POST':
        candidates_db.append({
            'name': request.form.get('name'), 'phone': request.form.get('phone'),
            'email': request.form.get('email'), 'position': request.form.get('position'),
            'country': request.form.get('country'), 'status': request.form.get('status'),
            'source': request.form.get('source'), 'exp': request.form.get('exp'),
            'date': datetime.now().strftime("%Y-%m-%d")
        })
        return redirect('/view')
    return render_template_string(ADD_HTML, pos=POSITION_OPTIONS, countries=COUNTRY_OPTIONS, stats=STATUS_OPTIONS, sources=SOURCE_OPTIONS)

@app.route('/view')
def view():
    if 'user' not in session: return redirect('/')
    search = request.args.get('search', '').lower()
    f_status = request.args.get('f_status', '')
    data = candidates_db
    if search: data = [c for c in data if search in c['name'].lower()]
    if f_status: data = [c for c in data if c['status'] == f_status]
    return render_template_string(VIEW_HTML, data=data, stats=STATUS_OPTIONS, search=search, f_status=f_status)

@app.route('/edit/<int:id>', methods=['GET', 'POST'])
def edit(id):
    if 'user' not in session: return redirect('/')
    candidate = candidates_db[id]
    if request.method == 'POST':
        candidate.update({
            'name': request.form.get('name'), 'phone': request.form.get('phone'),
            'status': request.form.get('status'), 'position': request.form.get('position')
        })
        return redirect('/view')
    return f"<h2>Edit {candidate['name']}</h2><form method='POST'>Name: <input name='name' value='{candidate['name']}'><br>Status: <select name='status'>{''.join([f'<option>{s}</option>' for s in STATUS_OPTIONS])}</select><br><button type='submit'>Save</button></form>"

@app.route('/export')
def export():
    if not candidates_db: return "No data to export"
    df = pd.DataFrame(candidates_db)
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False)
    output.seek(0)
    return send_file(output, as_attachment=True, download_name="Ahsaz_Candidates.xlsx", mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect('/')

if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
