import os
from pathlib import Path

import eventlet
import socketio

from logger import Logger

sio = socketio.Server(async_mode=None, cors_allowed_origins='*')

app = socketio.WSGIApp(sio)

BASE_DIR = Path(__file__).resolve().parent

MEDIA_DIR = os.path.join(BASE_DIR, 'media')

logger = Logger().logger

download_status = {}
upload_status = {}


@sio.event
def connect(sid, data, session):
    message = f'client {sid} connected'
    logger.debug('connect: ' + message)
    sio.emit('message_all', {'NOTICE': message})


@sio.event
def disconnect_request(sid):
    message = f'client {sid} disconnected'
    logger.debug('disconnect: ' + message)
    sio.emit('message_all', {'NOTICE': message})
    sio.disconnect(sid)


@sio.event
def message(sid, data):
    room = data.get('room', None)
    msg = f'{sid}: {data["msg"]}'
    logger.info(msg)
    sio.emit('message', {'msg': msg}, room=room)


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
    if file_name is None or not file_name:
        logger.warning(f'{sid}: wrong file name - {file_name}')
        sio.emit('message', {'NOTICE': 'No file with input name'})
        return

    # 클라이언트의 sid, file 명으로 chunk를 만들어줄 generator를 구분합니다
    if sid not in download_status:
        download_status[sid] = {}

    if file_name not in download_status[sid]:
        chunk_size = data.get('chunk_size', 524288)
        download_status[sid][file_name] = _file_download_chunk(sid, file_name, chunk_size)

    # 제너레이터가 출력한 값을 반환합니다
    sio.emit('file_download', next(download_status[sid][file_name]), room=sid)


def _file_download_chunk(sid, file_name, chunk_size):
    """
    file chunk를 출력하는 generator 함수입니다
    :param sid: 유저의 sid
    :param file_name: 요청 받은 media 내의 파일명
    :param chunk_size: chunk의 크기를 설정해줍니다
    :return: 파일을 읽으면서 chunk를 출력하고 전부 읽었다면 종료 메시지를 반환합니다
    """
    # 주어진 파일명의 파일을 엽니다
    with open(f'{MEDIA_DIR}\\{file_name}', 'rb') as f:
        # chunk 크기 만큼 파일을 읽어오는 것을 반복합니다
        while file_content := f.read(chunk_size):
            # 읽어온 chunk를 반환합니다
            yield {'content': file_content}
    # 파일을 전부 읽었다면 dict에서 제거합니다
    del download_status[sid][file_name]
    # 종료 메시지를 보냅니다
    yield {'msg': 'file_end'}


@sio.event
def file_upload(sid, data):
    file_name = data.get('file_name', None)
    if file_name is None:
        logger.warning(f'{sid}: wrong file name - {file_name}')
        sio.emit('message', {'NOTICE': 'No file with input name'})

    if sid not in upload_status:
        total = data.get('total', 0)
        upload_status[sid] = {file_name: {'chunk_number': list(range(total)), 'total': total}}

    waiting_chunk_number = upload_status[sid][file_name]['chunk_number']
    file_dir = f'{MEDIA_DIR}\\upload\\{file_name}'
    total_chunk = upload_status[sid][file_name]['total']

    if cursor := data.get('cursor', 0) in waiting_chunk_number:
        with open(f'{file_dir}_{cursor}', 'wb') as f:
            f.write(data.chunk)
            waiting_chunk_number.remove(cursor)

    if not waiting_chunk_number:
        with open(file_dir, 'wb') as mrg:
            for i in range(total_chunk):
                file_chunk_dir = f'{file_dir}_{i}'
                with open(file_chunk_dir, 'rb') as cnk:
                    mrg.write(cnk.read())

    progress = (1 - len(waiting_chunk_number) / total_chunk) * 100

    sio.emit('file_upload', {'msg': f'Upload progress : {progress:2f}%'}, room=sid)


if __name__ == '__main__':
    eventlet.wsgi.server(eventlet.listen(('', 8005)), app)
