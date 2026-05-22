import re
from pathlib import Path


MAX_FILE_SIZE_BYTES = 5 * 1024 * 1024
FILE_PATTERN = re.compile(r'@::(.+?)::')


def read_text_file(path: str) -> str:
    file_path = Path(path).expanduser()

    if not file_path.exists():
        raise FileNotFoundError(f'Файл не найден: {file_path}')

    if not file_path.is_file():
        raise ValueError(f'Это не файл: {file_path}')

    file_size = file_path.stat().st_size

    if file_size > MAX_FILE_SIZE_BYTES:
        raise ValueError('Максимальный размер файла 5 МБ! Проверяйте это перед загрузкой.')

    return file_path.read_text(encoding='utf-8')


def replace_file_mentions(user_text: str) -> str:
    matches = FILE_PATTERN.finditer(user_text)

    result = user_text

    for match in matches:
        full_mention = match.group(0)
        path = match.group(1).strip()

        file_content = read_text_file(path)

        result = result.replace(full_mention, '\n' + file_content)

    return result
