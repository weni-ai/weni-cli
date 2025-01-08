import click

from flask import Flask, request
from multiprocessing import Process, Pipe

app = Flask(__name__)
server_process = None
auth_parent_conn, auth_child_conn = Pipe()


@app.route("/sso-callback", methods=["GET"])
def sso_callback():
    auth_child_conn.send(request.args.get("code"))
    return "Successfully logged in, you can close this window now"


def serve():
    from waitress import serve

    global server_process

    server_process = Process(
        target=serve,
        kwargs={"app": app, "host": "0.0.0.0", "port": 8081, "_quiet": True},
    )
    server_process.start()


def shutdown():
    global server_process
    if server_process is not None:
        server_process.terminate()
        server_process = None
