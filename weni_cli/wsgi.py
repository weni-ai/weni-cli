import queue

from flask import Flask, request
from threading import Thread
from waitress import serve as waitress_serve

DEFAULT_PORT = 50051

app = Flask(__name__)
server_thread = None
auth_queue = queue.Queue()


@app.route("/sso-callback", methods=["GET"])
def sso_callback():
    global auth_queue
    auth_queue.put(request.args.get("code"))
    return "Successfully logged in, you can close this window now"


def serve():
    global server_thread
    server_thread = Thread(
        target=waitress_serve,
        kwargs={"app": app, "host": "0.0.0.0", "port": DEFAULT_PORT, "_quiet": True},
        daemon=True,
    )
    server_thread.start()


def shutdown():
    global server_thread
    if server_thread is not None:
        server_thread.join(timeout=1)
        server_thread = None
