from flask import Blueprint, request, jsonify
from datetime import datetime
from app.extensions import collections

webhook = Blueprint('Webhook', __name__, url_prefix='/webhook')

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
