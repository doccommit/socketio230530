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
    """
    파일 chunk를 전송해주는 Event handler 입니다
    :param sid: 요청한 사용자
    :param data: 파일명과 chunk 크기를 받습니다
    """
    # 요청에 파일명을 받습니다
    file_name = data.get('file_name', None)

    # 파일명이 주어지지 않으면 에러처리 합니다
    if file_name is None:
        logger.warning(f'{sid}: wrong file name - {file_name}')
        sio.emit('message', {'NOTICE': 'No file with input name'})

    # 클라이언트의 sid, file 명으로 chunk를 만들어줄 generator를 구분합니다
    if sid not in file_status:
        file_status[sid] = {}

    if file_name not in file_status[sid]:
        chunk_size = data.get('chunk_size', 1024)
        file_status[sid][file_name] = _file_chunk(sid, file_name, chunk_size)

    # 제너레이터가 출력한 값을 반환합니다
    sio.emit('file', next(file_status[sid][file_name]), room=sid)


def _file_chunk(sid, file_name, chunk_size):
    """
    file chunk를 출력하는 generator 함수입니다
    :param sid: 유저의 sid
    :param file_name: 요청 받은 media 내의 파일명
    :param chunk_size: chunk의 크기를 설정해줍니다
    :return: 파일을 읽으면서 chunk를 출력하고 전부 읽었다면 종료 메시지를 반환합니다
    """
    # 주어진 파일명의 파일을 엽니다
    with open(f'{MEDIA_DIR}/{file_name}', 'rb') as f:
        # chunk 크기 만큼 파일을 읽어오는 것을 반복합니다
        while file_content := f.read(chunk_size):
            # 읽어온 chunk를 반환합니다
            yield {'content': file_content}
    # 파일을 전부 읽었다면 dict에서 제거합니다
    del file_status[sid][file_name]
    # 종료 메시지를 보냅니다
    yield {'Message': 'file_end'}


if __name__ == '__main__':
    eventlet.wsgi.server(eventlet.listen(('', 5000)), app)
