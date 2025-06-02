from flask import Blueprint, request, jsonify
from datetime import datetime
from app.extensions import collections

webhook = Blueprint('Webhook', __name__, url_prefix='/webhook')

# This route returns the latest 10 events from MongoDB (in JSON)
@webhook.route("/events", methods=["GET"])
def get_events():
    events = list(collections.find().sort("timestamp", -1).limit(10))  # Get last 10 by newest timestamp

    # Convert MongoDB's ObjectId to string for JSON compatibility
    for e in events:
        e["_id"] = str(e["_id"])
    return jsonify(events)


# This route displays a basic web page that shows GitHub events, auto-refreshes every 15 seconds
@webhook.route("/ui")
def ui():
    return '''
    <!DOCTYPE html>
    <html>
    <head>
        <title>GitHub Webhook Events</title>
        <style>
            body { font-family: Arial; padding: 20px; background: #f4f4f4; }
            .event { background: white; margin: 10px 0; padding: 10px; border-left: 5px solid #007BFF; }
        </style>
    </head>
    <body>
        <h2>Recent GitHub Events</h2>
        <div id="event-list">Loading...</div>

        <script>
            // Function to load events from /events API and display them
            async function loadEvents() {
                const res = await fetch('/webhook/events');
                const data = await res.json();
                const container = document.getElementById('event-list');   

                // Generate HTML for each event
                container.innerHTML = data.map(event => {
                    const time = new Date(event.timestamp).toLocaleString();
                    if (event.action === "PUSH") {
                        return `<div class="event"><b>${event.author}</b> pushed to <b>${event.to_branch}</b> at ${time}</div>`;
                    } else if (event.action === "PULL_REQUEST") {
                        return `<div class="event"><b>${event.author}</b> opened a PR from <b>${event.from_branch}</b> to <b>${event.to_branch}</b> at ${time}</div>`;
                    } else if (event.action === "MERGE") {
                        return `<div class="event"><b>${event.author}</b> merged <b>${event.from_branch}</b> to <b>${event.to_branch}</b> at ${time}</div>`;
                    }
                    return '';
                }).join('');
            }

            loadEvents();                   // Load immediately
            setInterval(loadEvents, 15000); // Reload every 15 seconds
        </script>
    </body>
    </html>
    '''


@webhook.route('/receiver', methods=["POST"])
def receiver():
    try:
        data = request.json  
        print("Payload received:", data)

        event = request.headers.get('X-GitHub-Event', 'ping')
        print("Event Type:", event)

        if event == 'push':
            author = data['pusher']['name']
            to_branch = data['ref'].split('/')[-1]

            for commit in data.get('commits', []):
                document = {
                    'request_id': commit['id'],
                    'author': author,
                    'action': "PUSH",
                    'from_branch': None,
                    'to_branch': to_branch,
                    'timestamp': commit['timestamp']
                }
                collections.insert_one(document)
                print("Saved commit document:", document)

        elif event == 'pull_request':
            pr = data['pull_request']
            action = data['action']
            document = {
                'request_id': str(pr['id']),
                'author': pr['user']['login'],
                'action': None,
                'from_branch': pr['head']['ref'],
                'to_branch': pr['base']['ref'],
                'timestamp': datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')
            }

            if action == 'opened':
                document['action'] = "PULL_REQUEST"
            elif action == 'closed' and pr.get('merged'):
                document['action'] = "MERGE"
            else:
                return '', 204

            collections.insert_one(document)
            print("Saved PR document:", document)

        else:
            return '', 204

        return "Receiver Work Successfully", 200

    except Exception as e:
        print("ERROR:", e)
        return jsonify({'error': str(e)}), 500
