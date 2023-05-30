import os
from pathlib import Path

import eventlet
import socketio

from logger import Logger

sio = socketio.Server(async_mode=None)

app = socketio.WSGIApp(sio)

BASE_DIR = Path(__file__).resolve().parent

MEDIA_DIR = os.path.join(BASE_DIR, 'media')

logger = Logger().logger

file_status = {}


@sio.event
def connect(sid, environ):
    message = f'client {sid} connected'
    logger.debug('connect: ' + message)
    sio.emit('message_all', {'NOTICE': message})


@sio.event
def disconnect(sid, data, environ):
    message = f'client {sid} disconnected'
    logger.debug('disconnect: ' + message)
    sio.emit('message_all', {'NOTICE': message})


@sio.event
def message(sid, data):
    room = data.get('room', None)
    msg = f'{sid}: {data["msg"]}'
    logger.info(msg)
    sio.emit('message', {'Message': msg}, room=room)


@sio.event
def file_download(sid, data):
    file_name = data.get('file_name', None)

    if file_name is None:
        logger.warning(f'{sid}: wrong file name - {file_name}')
        sio.emit('message', {'NOTICE': 'No file with input name'})

    if sid not in file_status:
        file_status[sid] = {}

    if file_name not in file_status[sid]:
        chunk_size = data.get('chunk_size', 1024)
        file_status[sid][file_name] = _file_chunk(sid, file_name, chunk_size)

    sio.emit('file', next(file_status[sid][file_name]), room=sid)


def _file_chunk(sid, file_name, chunk_size):
    with open(f'{MEDIA_DIR}/{file_name}', 'rb') as f:
        while file_content := f.read(chunk_size):
            yield {'content': file_content}
    del file_status[sid][file_name]
    yield {'Message': 'file_end'}


if __name__ == '__main__':
    eventlet.wsgi.server(eventlet.listen(('', 5000)), app)
