
# 📡 GitHub Webhook Receiver with Flask + MongoDB + Live UI

A lightweight Flask app to receive GitHub webhook events (Push, Pull Request, Merge), store them in MongoDB, and display the most recent 10 in a live web UI.

---

## ⚙️ Technologies Used

- Flask (with Blueprints)
- MongoDB (via PyMongo)
- JavaScript (for UI auto-refresh)
- Ngrok (for exposing localhost to GitHub)

#  📋 Procedure

This project sets up a Flask-based GitHub webhook receiver connected to MongoDB. First, a Flask app is created using the factory pattern and organized with blueprints. MongoDB is configured to store webhook event data. The server runs locally and is exposed using ngrok to generate a public URL. This URL is then added as the payload URL in GitHub’s webhook settings. When GitHub events like push or pull requests occur, GitHub sends payloads to this Flask endpoint, which stores them in MongoDB. A web UI displays the latest events, auto-refreshing every 15 seconds for real-time monitoring and analysis.



# Dev Assessment - Webhook Receiver

Please use this repository for constructing the Flask webhook receiver.

*******************

## Setup

* Create a new virtual environment

```bash
pip install virtualenv
```

* Create the virtual env

```bash
virtualenv venv
```

* Activate the virtual env

```bash
source venv/bin/activate
```

* Install requirements

```bash
pip install -r requirements.txt
```

* Run the flask application (In production, please use Gunicorn)

```bash
python run.py
```

* The endpoint is at:

```bash
POST http://127.0.0.1:5000/webhook/receiver
```

You need to use this as the base and setup the flask app. Integrate this with MongoDB (commented at `app/extensions.py`)

*******************
