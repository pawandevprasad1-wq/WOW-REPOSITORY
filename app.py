import os
from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from pymongo import MongoClient
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = os.environ.get('FLASK_SECRET_KEY', 'my-super-secret-key-12345')

# MongoDB Configuration
MONGO_URI = os.environ.get('MONGO_URI', 'mongodb+srv://pawandevprasad1_db_user:12345@cluster0.acobnxp.mongodb.net/?appName=Cluster0')
DB_NAME = 'WOW'
COLLECTION_NAME = 'WOW'

client = MongoClient(MONGO_URI)
db = client[DB_NAME]
props_col = db[COLLECTION_NAME]
users_col = db['users']

@app.route('/')
def index():
    if 'user' in session:
        return redirect(url_for('dashboard'))
    return render_template('index.html')

@app.route('/signup', methods=['POST'])
def signup():
    data = request.json
    username = data.get('username')
    password = data.get('password')

    if users_col.find_one({'username': username}):
        return jsonify({'success': False, 'message': 'Username already exists!'}), 400

    hashed_password = generate_password_hash(password)
    users_col.insert_one({'username': username, 'password': hashed_password})
    return jsonify({'success': True, 'message': 'Account created successfully! Please login.'})

@app.route('/login', methods=['POST'])
def login():
    data = request.json
    username = data.get('username')
    password = data.get('password')

    user = users_col.find_one({'username': username})
    if user and check_password_hash(user['password'], password):
        session['user'] = username
        return jsonify({'success': True})
    
    return jsonify({'success': False, 'message': 'Please signup first or check credentials.'}), 401

@app.route('/dashboard')
def dashboard():
    if 'user' not in session:
        return redirect(url_for('index'))
    return render_template('dashboard.html', user=session['user'])

@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect(url_for('index'))

@app.route('/search')
def search():
    if 'user' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    loc = request.args.get('location', '').strip()
    if not loc:
        return jsonify([])

    # Searches location field across dictionaries
    results = list(props_col.find({'location': {'$regex': loc, '$options': 'i'}}))
    
    output = []
    for doc in results:
        doc['_id'] = str(doc['_id'])
        output.append(doc)
        
    return jsonify(output)

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
  
