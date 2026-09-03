import os
import re
from flask import Flask, render_template, request, jsonify
from pymongo import MongoClient

app = Flask(__name__)

MONGO_URI = os.getenv("MONGO_URI", "mongodb+srv://pawandevprasad1_db_user:12345@cluster0.acobnxp.mongodb.net/?appName=Cluster0")

client = MongoClient(MONGO_URI)
db = client['WOW']
collection = db['AZ']

@app.route('/')
def home():
    try:
        properties = list(collection.find().sort([("is_sponsored", -1)]).limit(20))
        for p in properties:
            p['_id'] = str(p['_id'])
        return render_template('index.html', properties=properties)
    except Exception as e:
        return f"Database Connection Error: {str(e)}"

# FIXED AUTO-SUGGEST: Grouping duplicate localities into a single clean suggestion
@app.route('/api/search/suggest', methods=['GET'])
def search_suggest():
    query = request.args.get('q', '').strip()
    if not query or len(query) < 2:
        return jsonify({"suggestions": []})

    regex = re.compile(f".*{query}.*", re.IGNORECASE)
    suggestions = []

    # 1. GROUPING LOCALITIES & CITIES (Duplicates Hataney Ke Liye)
    locations = collection.aggregate([
        {
            "$match": {
                "$or": [
                    {"location.city": regex},
                    {"location.locality": regex},
                    {"location.sub_locality": regex},
                    {"City": regex},
                    {"location": regex}
                ]
            }
        },
        # Grouping Stage: Unique Localities aur City nikalne ke liye
        {
            "$group": {
                "_id": {
                    "locality": { "$ifNull": ["$location.locality", "$location"] },
                    "city": { "$ifNull": ["$location.city", "$City"] }
                }
            }
        },
        { "$limit": 5 }
    ])

    for loc in locations:
        loc_name = loc['_id']['locality']
        city_name = loc['_id']['city']
        
        if loc_name:
            title_str = f"{loc_name}" + (f", {city_name}" if city_name else "")
            suggestions.append({
                "title": title_str,
                "type": "Locality",
                "search_keyword": loc_name  # Specific search ke liye
            })

    # 2. GROUPING PROJECTS / TITLES (Agar specific housing society/project name match ho)
    titles = collection.aggregate([
        {
            "$match": {
                "$or": [
                    {"title": regex},
                    {"Property Title / Headline": regex}
                ]
            }
        },
        {
            "$group": {
                "_id": { "$ifNull": ["$title", "$Property Title / Headline"] }
            }
        },
        { "$limit": 3 }
    ])

    for t in titles:
        if t['_id']:
            suggestions.append({
                "title": t['_id'],
                "type": "Project / Headline",
                "search_keyword": t['_id']
            })

    return jsonify({"suggestions": suggestions})

# SEARCH RESULTS API
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

    results = list(collection.find(filter_query).sort([("is_sponsored", -1)]))
    for r in results:
        r['_id'] = str(r['_id'])

    return jsonify({"results": results})

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
    
