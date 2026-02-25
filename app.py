from flask import Flask, render_template, request, session, redirect, url_for, jsonify
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import check_password_hash, generate_password_hash
import os
from datetime import datetime

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-key-change-in-production')
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///crm.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# Database Models
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Customer(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    phone = db.Column(db.String(20))
    company = db.Column(db.String(120))
    status = db.Column(db.String(20), default='active')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

class Lead(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    phone = db.Column(db.String(20))
    company = db.Column(db.String(120))
    status = db.Column(db.String(20), default='new')
    value = db.Column(db.Float, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

class Sales(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(20), default='pending')
    customer_id = db.Column(db.Integer, db.ForeignKey('customer.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

# Routes
@app.route('/')
def index():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        
        if User.query.filter_by(username=username).first():
            return 'Username already exists', 400
        
        user = User(
            username=username,
            email=email,
            password=generate_password_hash(password)
        )
        db.session.add(user)
        db.session.commit()
        
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        user = User.query.filter_by(username=username).first()
        
        if user and check_password_hash(user.password, password):
            session['user_id'] = user.id
            session['username'] = user.username
            return redirect(url_for('dashboard'))
        else:
            return 'Invalid credentials', 401
    
    return render_template('login.html')

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    user_id = session['user_id']
    customers_count = Customer.query.filter_by(user_id=user_id).count()
    leads_count = Lead.query.filter_by(user_id=user_id).count()
    sales_count = Sales.query.filter_by(user_id=user_id).count()
    total_sales = db.session.query(db.func.sum(Sales.amount)).filter_by(user_id=user_id).scalar() or 0
    
    return render_template('dashboard.html', 
                         username=session.get('username'),
                         customers_count=customers_count,
                         leads_count=leads_count,
                         sales_count=sales_count,
                         total_sales=total_sales)

@app.route('/customers')
def customers():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    customers = Customer.query.filter_by(user_id=session['user_id']).all()
    return render_template('customers.html', customers=customers)

@app.route('/customers/add', methods=['POST'])
def add_customer():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    customer = Customer(
        name=request.form.get('name'),
        email=request.form.get('email'),
        phone=request.form.get('phone'),
        company=request.form.get('company'),
        user_id=session['user_id']
    )
    db.session.add(customer)
    db.session.commit()
    
    return redirect(url_for('customers'))

@app.route('/leads')
def leads():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    leads = Lead.query.filter_by(user_id=session['user_id']).all()
    return render_template('leads.html', leads=leads)

@app.route('/leads/add', methods=['POST'])
def add_lead():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    lead = Lead(
        name=request.form.get('name'),
        email=request.form.get('email'),
        phone=request.form.get('phone'),
        company=request.form.get('company'),
        value=request.form.get('value', 0),
        user_id=session['user_id']
    )
    db.session.add(lead)
    db.session.commit()
    
    return redirect(url_for('leads'))

@app.route('/sales')
def sales():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    sales = Sales.query.filter_by(user_id=session['user_id']).all()
    return render_template('sales.html', sales=sales)

@app.route('/sales/add', methods=['POST'])
def add_sales():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    sale = Sales(
        title=request.form.get('title'),
        amount=request.form.get('amount'),
        status=request.form.get('status', 'pending'),
        customer_id=request.form.get('customer_id'),
        user_id=session['user_id']
    )
    db.session.add(sale)
    db.session.commit()
    
    return redirect(url_for('sales'))

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=False)
