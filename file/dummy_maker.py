from datetime import date
from pathlib import Path
from random import randbytes

BASE_DIR = Path(__file__).resolve().parent


def write_dummy(length, repeat):
    """
    randbytes를 반복해 더미파일을 생성하는 함수
    :param length: randbytes의 인자
    :param repeat: randbytes 실행 횟수
    :return: done!
    """
    with open(f'{BASE_DIR}\\{date.today()}.dummy', 'wb') as f:
        for _ in range(repeat):
            f.write(randbytes(1 << length))
            f.flush()
    return 'done!'


if __name__ == '__main__':
    """
    32gb 더미 생성
    """
    write_dummy(length=15, repeat=1 << 10)
    # write_dummy(length=15, repeat=1 << 20)
