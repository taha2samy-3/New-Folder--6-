import os
import datetime
from flask import Flask, jsonify, request, render_template, redirect, make_response
from kubernetes import client, config
import mysql.connector
from mysql.connector import Error

app = Flask(__name__)

# Environment variables injected by Kubernetes
APP_VERSION = os.environ.get('APP_VERSION', 'v1')
POD_UID = os.environ.get('POD_UID', 'unknown')
POD_NAME = os.environ.get('POD_NAME', 'unknown')
NAMESPACE = os.environ.get('POD_NAMESPACE', 'default')

def send_k8s_event(reason, message):
    try:
        config.load_incluster_config()
        v1 = client.CoreV1Api()
        
        event = client.CoreV1Event(
            metadata=client.V1ObjectMeta(
                generate_name="flask-app-event-",
                namespace=NAMESPACE
            ),
            involved_object=client.V1ObjectReference(
                kind="Pod",
                name=POD_NAME,
                namespace=NAMESPACE,
                uid=POD_UID,
                api_version="v1"
            ),
            reason=reason,
            message=message,
            type="Normal",
            source=client.V1EventSource(component="flask-demo-app"),
            first_timestamp=datetime.datetime.now(datetime.timezone.utc),
            last_timestamp=datetime.datetime.now(datetime.timezone.utc),
            count=1
        )
        v1.create_namespaced_event(namespace=NAMESPACE, body=event)
        return True
    except Exception as e:
        print(f"Error sending event: {e}")
        return False

def check_db_connection():
    try:
        connection = mysql.connector.connect(
            host=os.environ.get('DB_HOST', 'flask-demo-mysql'),
            database=os.environ.get('DB_NAME', 'demo_db'),
            user=os.environ.get('DB_USER', 'root'),
            password=os.environ.get('DB_PASSWORD', 'password123')
        )
        if connection.is_connected():
            connection.close()
            return "Connected Successfully to MySQL ✅"
    except Error as e:
        return f"Database Error: {e}"
    return "Unknown Error ❌"

@app.route('/')
def dashboard():
    # If the user hasn't selected a role, send them to login page
    if 'dev_mode' not in request.cookies:
        return redirect('/login')

    db_status = check_db_connection()
    event_sent_status = send_k8s_event(
        reason="PageVisit", 
        message=f"Visit to {APP_VERSION} from IP {request.remote_addr}"
    )
    event_sent = "Success ✅" if event_sent_status else "Failed / Not in K8s ⚠️"
    
    return render_template('dashboard.html',
        version=APP_VERSION,
        pod_uid=POD_UID,
        pod_name=POD_NAME,
        db_status=db_status,
        event_sent=event_sent
    )

@app.route('/login')
def login():
    return render_template('login.html')

@app.route('/set-mode/<mode>')
def set_mode(mode):
    resp = make_response(redirect('/'))
    if mode == 'developer':
        # NGINX Ingress looks for 'dev_mode=always' to route to Canary
        resp.set_cookie('dev_mode', 'always', httponly=True, max_age=60*60*24)
    else:
        # Normal user
        resp.set_cookie('dev_mode', 'never', httponly=True, max_age=60*60*24)
    return resp

@app.route('/trigger-panic')
def trigger_panic():
    messages = [
        "أنا بقع يا أسطى، فين الـ Secret؟!",
        "يا ابني الـ Secret مش موجود، أنا هقفل الـ Pod وامشي!",
        "هو أنا بشتغل عندكم ببلاش؟ حط الـ Secret يا حبيبي!",
        "ياحبيب عشان اتشغل لازم تحطط credentails .",
        "يا باشا السيستم بيولع، إنت بتلعب في إيه؟!",
        "خلاص مانا شغال، خلي الـ Kubernetes ينفعك.",
        "يا عم حط الـ Secret خلينا نخلص، ورايا Deployments تانية!",
        "أنا جبت آخري منك، هات حد كبير!",
        "بص، أنا هعمل Restart لنفسي وأريح دماغي.",
        "شوفلي lead بتاعك وقوله تعالى"
    ]
    for i, msg in enumerate(messages):
        send_k8s_event(reason=f"SecretMissingLevel{i+1}", message=msg)
    
    return jsonify({"status": "Panic events sent to Kubernetes!"})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
