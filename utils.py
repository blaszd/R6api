import sqlite3
import video_buffer as vb
import cv2
import threading

video_buffer_collection = {}
thread_collection = {}

def db():
    return sqlite3.connect('identifier.sqlite')

def fetch_frames(ip, video_buffer: vb.videoBuffer):
    cap = cv2.VideoCapture(f'http://{ip}:81/stream')

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        video_buffer.add_frame(frame)

    cap.release()

def encode_to_h265(frame):
    # Convert the frame to H.265 encoding
    h265_codec = cv2.VideoWriter_fourcc(*'X265')
    h265_encoded_frame = cv2.imencode('.hevc', frame, (h265_codec, 10, 10))

    return h265_encoded_frame.tobytes()

def new_cam_thread(cam):
    video_buffer_collection[cam["id"]] = vb.videoBuffer()
    thread = threading.Thread(target=fetch_frames, args=(cam["ipv4"], video_buffer_collection[cam["id"]]))
    thread_collection[cam["id"]] = thread
    thread.start()


def close_cam_threads():
    for thread in thread_collection:
        thread_collection[thread].join()


def get_cam_from_ip(ipv4):
    cdb = db()
    try:
        cur = cdb.cursor()
        cur.execute(
            "SELECT * FROM cams WHERE ipv4 = ?", (ipv4,)
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

def redirect_stream(id):
    global buffer_index
    while 1:
        # Get the latest frame from the buffer
        frame = video_buffer_collection[int(id)].get_frame()

        if frame is not None:
            # Convert the frame to JPEG
            ret, jpeg = cv2.imencode('.jpg', frame)
            frame = jpeg.tobytes()

            # Yield the frame as byte data
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n\r\n')

