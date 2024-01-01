from flask import Flask, request, send_from_directory
from flask_restful import Api, Resource
from werkzeug.utils import secure_filename
from tasks import convert_to_audio
from config import MAX_CONTENT_LENGTH, UPLOAD_PATH, PROCESSED_PATH, conversions, CONVERTED_PATH
import threading
import os
import asyncio
import time

app = Flask(__name__)
api = Api(app)

app.config['MAX_CONTENT_LENGTH'] = MAX_CONTENT_LENGTH

class ConvertResource(Resource):
    def post(self):
        try:
            if 'file' not in request.files:
                raise ValueError('No file provided')

            file = request.files['file']
            if file.filename == '':
                raise ValueError('No selected file')

            filename = secure_filename(file.filename)
            file_path = os.path.join(UPLOAD_PATH, filename)
            file.save(file_path)
            
            sid = request.form.get('sid')  # SocketIO connection ID

            timestamp_ms = int(time.time() * 1000)
            
            sid = f"{sid}_{timestamp_ms}.mp3"

            output_path = os.path.join(PROCESSED_PATH, sid)
            language = request.form.get('language', 'en-GB-SoniaNeural')

            # Start the conversion in a separate thread
            threading.Thread(target=asyncio.run, args=(convert_to_audio(file_path, output_path, language, sid),)).start()
            
            return {'message': 'Conversion started' , 'sid' : sid}, 200
        except Exception as e:
            return {'error': str(e)}, 400

class StatusResource(Resource):
    def get(self, sid):
        if sid not in conversions:
            return {'status': 'not_found', 'message': 'Conversion not found'}, 404

        return conversions[sid], 200

class ConvertedResource(Resource):
    def get(self, filename):
        try:
            return send_from_directory(CONVERTED_PATH, filename)
        except Exception as e:
            return {'error': str(e)}, 404

api.add_resource(ConvertResource, '/convert')
api.add_resource(StatusResource, '/status/<string:sid>')
api.add_resource(ConvertedResource, '/converted/<string:filename>')

if __name__ == '__main__':
    app.run(debug=True)
