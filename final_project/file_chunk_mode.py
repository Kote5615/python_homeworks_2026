from openai import OpenAI

from config import AppConfig
from constants import QUIT_COMMAND, SYSTEM_ROLE, ROLE_KEY
from file_mentions import read_text_file
from llm_client import ask_llm


def split_by_len(text: str, chunk_len: int) -> list[str]:
    chunks = []

    for index in range(0, len(text), chunk_len):
        chunks.append(text[index : index + chunk_len])

    return chunks


def split_by_paragraphs(text: str, paragraph_count: int = 1) -> list[str]:
    paragraphs = [paragraph.strip() for paragraph in text.splitlines() if paragraph.strip()]

    chunks = []

    for index in range(0, len(paragraphs), paragraph_count):
        chunk = '\n\n'.join(paragraphs[index : index + paragraph_count])
        chunks.append(chunk)

    return chunks


def parse_file_chunk_command(command: str) -> tuple[str, int, bool]:
    parts = command.split()

    mode = 'paragraph'
    value = 1
    auto_yes = '-y' in parts

    for part in parts[1:]:
        if part.startswith('paragraph='):
            mode = 'paragraph'
            value = int(part.split('=', maxsplit=1)[1])
        elif part.startswith('len='):
            mode = 'len'
            value = int(part.split('=', maxsplit=1)[1])

    return mode, value, auto_yes


def build_chunk_messages(
    config: AppConfig,
    user_prompt: str,
    chunk: str,
) -> list[dict[str, str]]:
    messages = []

    if config.system_prompt:
        messages.append(
            {
                ROLE_KEY: SYSTEM_ROLE,
                'content': config.system_prompt,
            },
        )

    messages.append(
        {
            'role': 'user',
            'content': f'{user_prompt}\n\nТекст фрагмента:\n{chunk}',
        },
    )

    return messages


def parse_file_chunk_settings(command: str) -> tuple[str, int, bool] | None:
    try:
        mode, value, auto_yes = parse_file_chunk_command(command)
    except ValueError:
        print('Ошибка: неверный формат команды /file_chunk')
        return None

    if value <= 0:
        print('Ошибка: введите положительное число')
        return None

    return mode, value, auto_yes


def read_file_text_from_console() -> str | None:
    path = input('Введите путь до файла:\n>>> ').strip()

    try:
        return read_text_file(path)
    except (UnicodeDecodeError, OSError, ValueError) as error:
        print(f'Ошибка чтения файла: {error}')
        return None


def read_user_prompt_from_console() -> str | None:
    user_prompt = input(
        'Принято. Что нужно сделать для каждого фрагмента?\n>>> ',
    ).strip()

    if user_prompt:
        return user_prompt

    print('Ошибка: prompt не может быть пустым.')
    return None


def build_chunks(text: str, mode: str, value: int) -> list[str]:
    if mode == 'len':
        return split_by_len(text, value)

    return split_by_paragraphs(text, value)


def ask_model_for_chunk(
    client: OpenAI,
    config: AppConfig,
    user_prompt: str,
    chunk: str,
) -> str | None:
    messages = build_chunk_messages(config, user_prompt, chunk)

    try:
        return ask_llm(client, config, messages)
    except KeyboardInterrupt:
        print('\nЗапрос прерван')
        return None
    except Exception as error:
        print(f'Ошибка при запросе к модели: {error}')
        return None


def should_continue_chunks(auto_yes: bool) -> bool:
    if auto_yes:
        return True

    next_action = input(
        '\nНажмите Enter для следующего чанка или '
        r'\q'
        ' для выхода:\n>>> ',
    )

    return next_action.strip() != QUIT_COMMAND


def process_chunks(
    client: OpenAI,
    config: AppConfig,
    chunks: list[str],
    user_prompt: str,
    auto_yes: bool,
) -> None:
    for chunk in chunks:
        answer = ask_model_for_chunk(client, config, user_prompt, chunk)

        if answer is None:
            return

        print(answer)

        if not should_continue_chunks(auto_yes):
            print('Обработка файла завершена')
            return

    print('Обработка файла завершена')


def prepare_chunk_mode_data(
    command: str,
) -> tuple[list[str], str, bool] | None:
    settings = parse_file_chunk_settings(command)

    if settings is None:
        return None

    mode, value, auto_yes = settings
    text = read_file_text_from_console()
    if text is None:
        return None

    user_prompt = read_user_prompt_from_console()
    if user_prompt is None:
        return None

    chunks = build_chunks(text, mode, value)

    return chunks, user_prompt, auto_yes


def run_file_chunk_mode(
    client: OpenAI,
    config: AppConfig,
    command: str,
) -> None:
    chunk_mode_data = prepare_chunk_mode_data(command)

    if chunk_mode_data is None:
        return

    chunks, user_prompt, auto_yes = chunk_mode_data

    print('Принято. Начинаю обработку:')
    process_chunks(client, config, chunks, user_prompt, auto_yes)
