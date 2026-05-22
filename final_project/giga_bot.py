import os

from config import load_config
from context_manager import init_messages, trim_context
from file_chunk_mode import run_file_chunk_mode
from file_mentions import replace_file_mentions
from llm_client import ask_llm, create_client


def print_greeting() -> None:
    print('Чат запущен')


def main() -> None:
    config = load_config()
    client = create_client(config)
    messages = init_messages(config)

    print_greeting()

    while True:
        user_input = input('>>> ').strip()

        if user_input == '\\q':
            print('Пока!')
            break

        if user_input == '/reset':
            messages = init_messages(config)
            os.system('cls')
            print('Начнем с чистого листа')
            continue

        if user_input.startswith('/file_chunk'):
            run_file_chunk_mode(client, config, user_input)
            continue
        if not user_input:
            continue
        try:
            prepared_input = replace_file_mentions(user_input)
        except (OSError, ValueError, UnicodeDecodeError) as error:
            print(f'Ошибка: {error}')
            continue

        messages.append(
            {
                'role': 'user',
                'content': prepared_input,
            },
        )

        messages = trim_context(messages, config)

        try:
            answer = ask_llm(client, config, messages)
        except KeyboardInterrupt:
            print('\nпрервали')
            continue
        except Exception as error:
            print(f'Ошибка: {error}')
            continue

        print(answer)

        messages.append(
            {
                'role': 'assistant',
                'content': answer,
            },
        )

        messages = trim_context(messages, config)


if __name__ == '__main__':
    main()
