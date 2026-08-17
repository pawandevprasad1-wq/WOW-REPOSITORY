from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from pymongo import MongoClient
from bson import ObjectId
from werkzeug.security import generate_password_hash, check_password_hash
import os

app = Flask(__name__)
app.secret_key = 'super_secret_key'

# MongoDB कनेक्शन
client = MongoClient('mongodb+srv://pawandevprasad1_db_user:12345@cluster0.acobnxp.mongodb.net/?appName=Cluster0')
db = client['WOW']
props_col = db['WOW']
users_col = db['users']

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/signup', methods=['POST'])
def signup():
    data = request.json
    users_col.insert_one({'username': data['username'], 'password': generate_password_hash(data['password'])})
    return jsonify({'success': True})

@app.route('/login', methods=['POST'])
def login():
    data = request.json
    user = users_col.find_one({'username': data['username']})
    if user and check_password_hash(user['password'], data['password']):
        session['user'] = data['username']
        return jsonify({'success': True})
    return jsonify({'success': False}), 401

@app.route('/dashboard')
def dashboard():
    if 'user' not in session: return redirect(url_for('index'))
    return render_template('dashboard.html')

@app.route('/search')
def search():
    loc = request.args.get('location', '')
    # location field में सर्च करेगा
    results = list(props_col.find({'location': {'$regex': loc, '$options': 'i'}}))
    for r in results: r['_id'] = str(r['_id'])
    return jsonify(results)

@app.route('/property/<id>')
def property_details(id):
    prop = props_col.find_one({'_id': ObjectId(id)})
    prop['_id'] = str(prop['_id'])
    return render_template('details.html', property=prop)

if __name__ == '__main__':
    app.run(debug=True)
    
