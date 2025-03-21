from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from models import db, User, Product
import jwt
import bcrypt
from datetime import datetime, timedelta
from functools import wraps
import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.sqlite'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = os.getenv('JWT_SECRET')
db.init_app(app)

# Middleware to verify JWT token
def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('Authorization')
        if not token or not token.startswith('Bearer '):
            return jsonify({'error': 'Access denied, token required'}), 401
        try:
            token = token.split(" ")[1]
            data = jwt.decode(token, app.config['SECRET_KEY'], algorithms=["HS256"])
            current_user = User.query.get(data['id'])
            if not current_user:
                return jsonify({'error': 'Invalid token'}), 403
            request.user = current_user
        except:
            return jsonify({'error': 'Invalid token'}), 403
        return f(*args, **kwargs)
    return decorated

# Create database tables
with app.app_context():
    db.create_all()

# Signup endpoint
@app.route('/auth/signup', methods=['POST'])
def signup():
    data = request.get_json()
    name = data.get('name')
    username = data.get('username')
    password = data.get('password')
    
    if not name or not username or not password:
        return jsonify({'error': 'All fields (name, username, password) are required'}), 400
    
    hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
    user = User(name=name, username=username, password=hashed_password)
    db.session.add(user)
    db.session.commit()
    
    return jsonify({'message': 'User registered', 'userId': user.id}), 201

# Login endpoint
@app.route('/auth/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    
    if not username or not password:
        return jsonify({'error': 'Username and password are required'}), 400
    
    user = User.query.filter_by(username=username).first()
    if not user or not bcrypt.checkpw(password.encode('utf-8'), user.password):
        return jsonify({'error': 'Invalid username or password'}), 401
    
    token = jwt.encode({
        'id': user.id,
        'username': user.username,
        'exp': datetime.utcnow() + timedelta(minutes=10)
    }, app.config['SECRET_KEY'])
    
    return jsonify({'token': token})

# Update user endpoint
@app.route('/users/<int:id>', methods=['PUT'])
@token_required
def update_user(id):
    if request.user.id != id:
        return jsonify({'error': 'Unauthorized, this is not your account'}), 403
    
    data = request.get_json()
    name = data.get('name')
    username = data.get('username')
    
    if not name or not username:
        return jsonify({'error': 'Name and username are required'}), 400
    
    user = User.query.get(id)
    user.name = name
    user.username = username
    db.session.commit()
    
    return jsonify({'id': user.id, 'name': user.name, 'username': user.username})

# Create product endpoint
@app.route('/products', methods=['POST'])
@token_required
def create_product():
    data = request.get_json()
    pname = data.get('pname')
    description = data.get('description')
    price = data.get('price')
    stock = data.get('stock')
    
    if not pname or not price or not stock:
        return jsonify({'error': 'Product name, price, and stock are required'}), 400
    
    product = Product(pname=pname, description=description, price=price, stock=stock)
    db.session.add(product)
    db.session.commit()
    
    return jsonify({
        'pid': product.pid,
        'pname': product.pname,
        'description': product.description,
        'price': product.price,
        'stock': product.stock,
        'created_at': product.created_at
    }), 201

# Get all products endpoint
@app.route('/products', methods=['GET'])
@token_required
def get_products():
    products = Product.query.all()
    return jsonify([{
        'pid': p.pid,
        'pname': p.pname,
        'description': p.description,
        'price': p.price,
        'stock': p.stock,
        'created_at': p.created_at
    } for p in products])

# Get single product endpoint
@app.route('/products/<int:pid>', methods=['GET'])
@token_required
def get_product(pid):
    product = Product.query.get(pid)
    if not product:
        return jsonify({'error': 'Product not found'}), 404
    
    return jsonify({
        'pid': product.pid,
        'pname': product.pname,
        'description': product.description,
        'price': product.price,
        'stock': product.stock,
        'created_at': product.created_at
    })

# Update product endpoint
@app.route('/products/<int:pid>', methods=['PUT'])
@token_required
def update_product(pid):
    data = request.get_json()
    pname = data.get('pname')
    description = data.get('description')
    price = data.get('price')
    stock = data.get('stock')
    
    if not pname or not price or not stock:
        return jsonify({'error': 'Product name, price, and stock are required'}), 400
    
    product = Product.query.get(pid)
    if not product:
        return jsonify({'error': 'Product not found'}), 404
    
    product.pname = pname
    product.description = description
    product.price = price
    product.stock = stock
    db.session.commit()
    
    return jsonify({
        'pid': product.pid,
        'pname': product.pname,
        'description': product.description,
        'price': product.price,
        'stock': product.stock,
        'created_at': product.created_at
    })

# Delete product endpoint
@app.route('/products/<int:pid>', methods=['DELETE'])
@token_required
def delete_product(pid):
    product = Product.query.get(pid)
    if not product:
        return jsonify({'error': 'Product not found'}), 404
    
    db.session.delete(product)
    db.session.commit()
    return jsonify({'message': 'Product deleted'})

if __name__ == '__main__':
    app.run(debug=True, port=int(os.getenv('PORT', 3000)))
