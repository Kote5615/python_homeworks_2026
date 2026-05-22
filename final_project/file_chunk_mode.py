from openai import OpenAI

from config import AppConfig
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
                'role': 'system',
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


def run_file_chunk_mode(
    client: OpenAI,
    config: AppConfig,
    command: str,
) -> None:
    try:
        mode, value, auto_yes = parse_file_chunk_command(command)
    except ValueError:
        print('Ошибка: неверный формат команды /file_chunk')
        return

    if value <= 0:
        print('Ошибка: введите положительное числом')
        return

    path = input('Введите путь до файла:\n>>> ').strip()

    try:
        text = read_text_file(path)
    except (OSError, ValueError, UnicodeDecodeError) as error:
        print(f'Ошибка чтения файла: {error}')
        return

    user_prompt = input(
        'Принято. Что нужно сделать для каждого фрагмента?\n>>> ',
    ).strip()

    if not user_prompt:
        print('Ошибка: prompt не может быть пустым.')
        return

    if mode == 'len':
        chunks = split_by_len(text, value)
    else:
        chunks = split_by_paragraphs(text, value)

    print('Принято. Начинаю обработку:')

    for chunk in chunks:
        messages = build_chunk_messages(config, user_prompt, chunk)

        try:
            answer = ask_llm(client, config, messages)
        except KeyboardInterrupt:
            print('\nЗапрос прерван')
            return
        except Exception as error:
            print(f'Ошибка при запросе к модели: {error}')
            return

        print(answer)

        if not auto_yes:
            next_action = input(
                '\nНажмите Enter для следующего чанка или \\q для выхода:\n>>> ',
            )

            if next_action.strip() == '\\q':
                print('Обработка файла завершена')
                return

    print('Обработка файла завершена')
