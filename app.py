from flask import Flask, request, jsonify, render_template
from flask_pymongo import PyMongo
from datetime import datetime, timezone

app = Flask(__name__)

# MongoDB Configuration
app.config["MONGO_URI"] = "mongodb://localhost:27017/github_webhooks"
mongo = PyMongo(app)

@app.route('/')
def index():
    return render_template("index.html")

@app.route('/webhook', methods=['POST']) 
def webhook():
    print("Webhook received")

    payload = request.json
    event_type = request.headers.get("X-GitHub-Event")
    print(f"Event Type: {event_type}")

    timestamp = datetime.now(timezone.utc).strftime("%d %B %Y - %I:%M %p UTC")
    data = {}

    if event_type == "push":
        print("Processing push event")
        data = {
            "type": "push",
            "author": payload['pusher']['name'],
            "to_branch": payload['ref'].split("/")[-1],
            "timestamp": timestamp
        }

    elif event_type == "pull_request":
        print("Processing pull request event")
        pr = payload['pull_request']
        action = payload.get("action")

        if action == "opened":
            data = {
                "type": "pull_request",
                "author": pr['user']['login'],
                "from_branch": pr['head']['ref'],
                "to_branch": pr['base']['ref'],
                "timestamp": timestamp
            }

        elif action == "closed" and pr.get("merged"):
            data = {
                "type": "merge",
                "author": pr['user']['login'],
                "from_branch": pr['head']['ref'],
                "to_branch": pr['base']['ref'],
                "timestamp": timestamp
            }

    if data:
        mongo.db.events.insert_one(data)
        print("Data inserted into MongoDB:", data)
    else:
        print("No valid event to store")

    return jsonify({"status": "success"}), 200

@app.route('/events', methods=['GET'])
def get_events():
    print("Fetching latest events from MongoDB")
    events = list(mongo.db.events.find({}, {"_id": 0}).sort("_id", -1).limit(10))
    return jsonify(events)

if __name__ == '__main__':
    print("Starting Flask server...")
    app.run(debug=True, port=5000)
