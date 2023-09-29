import sys
from flask import Flask, jsonify, Response, request
from flask_restful import Api
from flask_socketio import SocketIO
from flask_cors import CORS
import sqlite3
from utils import *


app = Flask(__name__)




@app.route('/')
def main():
    return 'The Viewer API'


@app.route('/cameras', methods=['GET'])
def index_cameras():
    return ''


@app.route('/cameras/all', methods=['GET'])
def get_cameras():
    cdb = db()
    cams = []
    try:
        cur = cdb.cursor()
        cur.execute(
            "SELECT * FROM cams"
        )
        rows = cur.fetchall()
        for i in rows:
            print(i)
            cam = {"id": i[0], "ipv4": i[1], "state": i[2]}
            cams.append(cam)
    except sqlite3.Error:
        return 'SQL-ERROR', 400
    finally:
        cdb.close()
    return cams


@app.route('/cameras/add', methods=['POST'])
def new_cameras():
    cam = request.json
    cdb = db()
    try:
        cur = cdb.cursor()
        cur.execute(
            "INSERT INTO cams (ipv4,state) VALUES (?,?)",
            (cam.get('ipv4'), cam.get('state'))
        )
        cdb.commit()
        cam_obj = get_cam_from_ip(cam.get('ipv4'))
        new_cam_thread(cam_obj)
    except sqlite3.Error:
        cdb.rollback()
        return 'SQL-ERROR', 400
    finally:
        cdb.close()
    return '[CAM ADDED]'


@app.route('/cameras/<id>/del', methods=['GET'])
def del_cameras(id):
    cdb = db()
    try:
        cur = cdb.cursor()
        cur.execute(
            "DELETE FROM cams WHERE id = ?",
            (id)
        )
        cdb.commit()
        thread_collection[int(id)].join()
        video_buffer_collection[int(id)] = [None]
    except sqlite3.Error:
        cdb.rollback()
        return 'SQL-ERROR', 400
    finally:
        cdb.close()
    return '[CAM DELETED]'


@app.route('/cameras/<id>', methods=['GET'])
def get_cam(id):
    cdb = db()
    try:
        cur = cdb.cursor()
        cur.execute(
            "SELECT * FROM cams WHERE id = ?", (id,)
        )
        row = cur.fetchone()
        if row is None:
            raise sqlite3.Error
        cam = {"id": row[0], "ipv4": row[1], "state": row[2]}
    except sqlite3.Error:
        return 'SQL-ERROR', 400
    finally:
        cdb.close()
    return cam


@app.route('/cameras/<id>/switch_state', methods=['GET'])
def switch_cam_state(id):
    cdb = db()
    try:
        cur = cdb.cursor()
        cur.execute(
            "update cams set state= ((state | 1) - (state & 1)) where id = ?", (id,)
        )
        cdb.commit()
    except sqlite3.Error:
        cdb.rollback()
        return 'SQL-ERROR', 400
    finally:
        cdb.close()
    return 'DONE'



@app.route('/cameras/<id>/stream')
def video_feed(id):
    return Response(redirect_stream(id),
                    mimetype='multipart/x-mixed-replace; boundary=frame')


@app.route('/user/add', methods=['POST'])
def new_user():
    user = request.json
    cdb = db()
    try:
        cur = cdb.cursor()
        if user.get('playerID'):
            cur.execute(
                "INSERT INTO Users (ipv4,state,playerID) VALUES (?,?,?)",
                (user.get('ipv4'), user.get('state'),user.get('playerID'))
            )
        else:
            cur.execute(
                "INSERT INTO Users (ipv4,state) VALUES (?,?)",
                (user.get('ipv4'), user.get('state'))
            )
        cdb.commit()
    except sqlite3.Error:
        cdb.rollback()
        return 'SQL-ERROR', 400
    finally:
        cdb.close()
    return '[CAM ADDED]'


@app.route('/user/<id>/del', methods=['GET'])
def del_user(id):
    cdb = db()
    try:
        cur = cdb.cursor()
        cur.execute(
            "DELETE FROM Users WHERE id = ?",
            (id)
        )
        cdb.commit()
    except sqlite3.Error:
        cdb.rollback()
        return 'SQL-ERROR', 400
    finally:
        cdb.close()
    return '[CAM DELETED]'


def startup():
    cams = get_cameras()
    for cam in cams:
        new_cam_thread(cam)
    app.run()

try:
    startup()
except (KeyboardInterrupt, SystemExit):
    close_cam_threads()
    sys.exit()

