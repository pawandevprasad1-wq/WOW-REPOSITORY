import os
import re
from flask import Flask, render_template, request, jsonify
from pymongo import MongoClient

app = Flask(__name__)

# Aapka Direct Mongo Atlas Connection
MONGO_URI = os.getenv("MONGO_URI", "mongodb+srv://pawandevprasad1_db_user:12345@cluster0.acobnxp.mongodb.net/?appName=Cluster0")

client = MongoClient(MONGO_URI)
db = client['WOW']        # Database Name
collection = db['AZ']      # Collection Name

# Home Page Route (Database se Live Properties Load karega)
@app.route('/')
def home():
    try:
        # Direct MongoDB Query: Sponsored pehle sort hongi (-1)
        properties = list(collection.find().sort([("is_sponsored", -1)]).limit(20))
        for p in properties:
            p['_id'] = str(p['_id'])  # ObjectId ko string mein convert kiya
        return render_template('index.html', properties=properties)
    except Exception as e:
        return f"Database Connection Error: {str(e)}"

# 1. Screenshot-style Auto-Complete Suggestions API
@app.route('/api/search/suggest', methods=['GET'])
def search_suggest():
    query = request.args.get('q', '').strip()
    if not query or len(query) < 2:
        return jsonify({"suggestions": []})

    regex = re.compile(f".*{query}.*", re.IGNORECASE)
    suggestions = []

    # MongoDB Aggregation Pipeline for Localities & Cities
    locations = collection.aggregate([
        {"$match": {
            "$or": [
                {"location.city": regex},
                {"location.locality": regex},
                {"location.sub_locality": regex},
                {"City": regex},
                {"location": regex}
            ]
        }},
        {"$group": {
            "_id": "$location.locality",
            "city": {"$first": "$location.city"},
            "type": {"$first": "Locality"}
        }},
        {"$limit": 5}
    ])

    for loc in locations:
        if loc['_id']:
            city_name = loc.get('city', '')
            suggestions.append({
                "title": f"{loc['_id']}" + (f", {city_name}" if city_name else ""),
                "type": "Locality"
            })

    # MongoDB Query for Project Titles
    titles = collection.find(
        {"$or": [{"title": regex}, {"Property Title / Headline": regex}]},
        {"title": 1, "Property Title / Headline": 1, "location.city": 1, "City": 1}
    ).limit(5)

    for t in titles:
        title_text = t.get('title') or t.get('Property Title / Headline', '')
        city_text = t.get('location', {}).get('city') if isinstance(t.get('location'), dict) else t.get('City', '')
        
        suggestions.append({
            "title": f"{title_text}" + (f", {city_text}" if city_text else ""),
            "type": "Project / Listing"
        })

    return jsonify({"suggestions": suggestions})

# 2. Dynamic Search Filter Endpoint
@app.route('/api/search', methods=['GET'])
def search():
    query = request.args.get('q', '').strip()
    regex = re.compile(f".*{query}.*", re.IGNORECASE)

    filter_query = {}
    if query:
        filter_query = {
            "$or": [
                {"title": regex},
                {"Property Title / Headline": regex},
                {"location.city": regex},
                {"City": regex},
                {"location.locality": regex},
                {"location": regex},
                {"location.sub_locality": regex}
            ]
        }

    # Sponsored listings first sorting logic
    results = list(collection.find(filter_query).sort([("is_sponsored", -1)]))
    for r in results:
        r['_id'] = str(r['_id'])

    return jsonify({"results": results})

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
      
