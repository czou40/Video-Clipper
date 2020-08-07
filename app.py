from flask import Flask, request, send_from_directory
from werkzeug.utils import secure_filename
import os
from flask_cors import CORS
import uuid
from threading import Thread
import shutil
from video_clipper import process_video
app = Flask(__name__, static_url_path='')
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'mp4'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
CORS(app)


class Task(Thread):
    def __init__(self, path, id):
        super().__init__()
        self.path = path
        self.id = id

    def run(self):
        os.makedirs(os.path.join("results", self.id))
        source = process_video(self.path)
        save = os.path.join("results", self.id, "result")
        shutil.make_archive(save, 'zip', source)
        f = open(os.path.join("results", self.id, "finished"),"a")
        f.close()


def allowed_file(filename):
    print(filename.rsplit('.', 1)[1].lower())
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route('/newVideo', methods=['POST'])
def upload_file():
    # check if the post request has the file part
    if 'file' not in request.files:
        return {
            "successful": False,
            "error": "No file part"
        }
    file = request.files['file']
    # if user does not select file, browser also
    # submit an empty part without filename
    if file.filename == '':
        return {
            "successful": False,
            "error": "No selected file"
        }
    print(file.filename)
    if file and allowed_file(file.filename):
        try:
            filename = secure_filename(file.filename)
            id = str(uuid.uuid1())
            directory = os.path.join(app.config['UPLOAD_FOLDER'], id)
            os.makedirs(directory)
            path = os.path.join(directory, filename)

            file.save(path)
            Task(path, id).start()
            return {
                "successful": True,
                "id": id
            }
        except Exception as e:
            return {
                "successful": False,
                "error": str(e)
            }
    else:
        return {
            "successful": False,
            "error": "unsupported format"
        }


@app.route("/status", methods=["GET"])
def get_status():
    id = request.args.get("id", "N/A")
    try:
        directory = os.path.join("results", id)
        if not os.path.exists(directory):
            return  {
                "successful": False,
                "error": "task with this id does not exist"
            }
        if not os.path.exists(os.path.join(directory, "finished")):
            return  {
                "successful": False,
                "error": "task is still running"
            }
        return  {
            "successful": True,
            "url": "/results/" + id + "/result.zip"
        }
    except Exception as e:
        return  {
            "successful": False,
            "error": str(e)
        }


@app.route("/results/<path:path>", methods=["GET"])
def get_file(path):
    return send_from_directory('results', path)