import os
from flask import Flask, render_template, request, jsonify
from pymongo import MongoClient
from bson.objectid import ObjectId

app = Flask(__name__)

# ==================== DATABASE CONFIGURATION ====================
MONGO_URI = "mongodb+srv://pawandevprasad1_db_user:12300pawandevprasad03112010@cluster0.acobnxp.mongodb.net/?appName=Cluster0"
DB_NAME = "BUY_PROPERTY_KOLKATA"
COLLECTION_NAME = "KOLKATA_LISTING"

# MongoDB कनेक्शन
client = MongoClient(MONGO_URI)
db = client[DB_NAME]
collection = db[COLLECTION_NAME]
# =================================================================

@app.route('/')
def home():
    return render_template('index.html')

# Autocomplete search API for locations
@app.route('/api/search_location')
def search_location():
    query = request.args.get('q', '').strip()
    if not query:
        return jsonify([])

    regex = {"$regex": query, "$options": "i"}
    pipeline = [
        {"$match": {"$or": [
            {"location.locality": regex},
            {"location.sub_locality": regex},
            {"location.city": regex}
        ]}},
        {"$project": {
            "locality": "$location.locality",
            "sub_locality": "$location.sub_locality",
            "city": "$location.city"
        }},
        {"$limit": 10}
    ]

    results = list(collection.aggregate(pipeline))
    locations = set()

    for doc in results:
        loc = doc.get("location", doc)
        if loc.get("locality"):
            locations.add(loc.get("locality"))
        if loc.get("sub_locality"):
            locations.add(loc.get("sub_locality"))

    return jsonify(list(locations))

# Listings page based on location
@app.route('/listings')
def listings():
    location_query = request.args.get('location', '')
    regex = {"$regex": location_query, "$options": "i"}
    
    query = {"$or": [
        {"location.locality": regex},
        {"location.sub_locality": regex},
        {"location.city": regex}
    ]}
    
    properties = list(collection.find(query))
    for p in properties:
        p['_id'] = str(p['_id'])  # ObjectId को String में कन्वर्ट करना

    return render_template('listings.html', properties=properties, location=location_query)

# Detail page for a specific property
@app.route('/property/<property_id>')
def property_detail(property_id):
    try:
        query = None
        if ObjectId.is_valid(property_id):
            query = {"_id": ObjectId(property_id)}
        else:
            query = {"_id": property_id}

        prop = collection.find_one(query)
        if prop:
            prop['_id'] = str(prop['_id'])
            return render_template('detail.html', p=prop)
        else:
            return "<h1>प्रॉपर्टी नहीं मिली (Property Not Found)</h1>", 404
    except Exception as e:
        return f"<h1>Error: {str(e)}</h1>", 500

if __name__ == '__main__':
    app.run(debug=True)
    
