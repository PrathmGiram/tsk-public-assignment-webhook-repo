from flask import Blueprint, request, jsonify
from datetime import datetime
from app.extensions import collections  # MongoDB collection instance

# Create a Flask Blueprint for webhook-related routes
webhook = Blueprint('Webhook', __name__, url_prefix='/webhook')


# Route to get the latest 10 GitHub event documents from MongoDB
@webhook.route("/events", methods=["GET"])
def get_events():
    # Fetch last 10 documents sorted by descending timestamp (newest first)
    events = list(collections.find().sort("timestamp", -1).limit(10))

    # Convert ObjectId to string for JSON serialization
    for e in events:
        e["_id"] = str(e["_id"])
    return jsonify(events)  # Return the list as a JSON response


# Route to serve a simple HTML page that displays GitHub events
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
            // Asynchronous function to fetch and display recent events
            async function loadEvents() {
                const res = await fetch('/webhook/events');  // Fetch data from /events endpoint
                const data = await res.json();               // Parse the JSON response
                const container = document.getElementById('event-list');   

                // Create and display HTML based on each event type
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

            loadEvents();                   // Initial load of events
            setInterval(loadEvents, 15000); // Auto-refresh every 15 seconds
        </script>
    </body>
    </html>
    '''


# Route to receive and process GitHub webhook POST requests
@webhook.route('/receiver', methods=["POST"])
def receiver():
    try:
        data = request.json  # Get JSON payload from GitHub
        print("Payload received:", data)

        # Identify the event type from GitHub headers
        event = request.headers.get('X-GitHub-Event', 'ping')
        print("Event Type:", event)

        # Handle 'push' events
        if event == 'push':
            author = data['pusher']['name']
            to_branch = data['ref'].split('/')[-1]  # Extract branch name from ref

            # Loop through all commits and store each as a separate document
            for commit in data.get('commits', []):
                document = {
                    'request_id': commit['id'],
                    'author': author,
                    'action': "PUSH",
                    'from_branch': None,
                    'to_branch': to_branch,
                    'timestamp': commit['timestamp']
                }
                collections.insert_one(document)  # Insert into MongoDB
                print("Saved commit document:", document)

        # Handle 'pull_request' events
        elif event == 'pull_request':
            pr = data['pull_request']
            action = data['action']  # e.g., 'opened', 'closed'
            document = {
                'request_id': str(pr['id']),
                'author': pr['user']['login'],
                'action': None,
                'from_branch': pr['head']['ref'],  # Source branch
                'to_branch': pr['base']['ref'],    # Target branch
                'timestamp': datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')  # Current time in ISO format
            }

            # Determine the specific PR action
            if action == 'opened':
                document['action'] = "PULL_REQUEST"
            elif action == 'closed' and pr.get('merged'):
                document['action'] = "MERGE"
            else:
                return '', 204  # Ignore irrelevant PR actions

            collections.insert_one(document)  # Insert into MongoDB
            print("Saved PR document:", document)

        else:
            return '', 204  # Ignore unhandled events

        return "Receiver Work Successfully", 200  # Acknowledge receipt

    except Exception as e:
        # Handle and log any errors
        print("ERROR:", e)
        return jsonify({'error': str(e)}), 500
