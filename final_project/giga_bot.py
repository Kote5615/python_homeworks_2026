import os
from typing import Any

from config import AppConfig, load_config
from constants import QUIT_COMMAND
from context_manager import init_messages, trim_context
from file_chunk_mode import run_file_chunk_mode
from file_mentions import replace_file_mentions
from llm_client import ask_llm, create_client


Message = dict[str, str]
CommandResult = tuple[list[Message] | None, bool]
AppData = tuple[AppConfig, Any, list[Message]]


def print_greeting() -> None:
    print('Чат запущен')


def is_reset_command(user_input: str) -> bool:
    return user_input == '/reset'


def is_file_chunk_command(user_input: str) -> bool:
    return user_input.startswith('/file_chunk')


def reset_messages(config: AppConfig) -> list[Message]:
    os.system('cls')
    print('Начнем с чистого листа')

    return init_messages(config)


def prepare_input(user_input: str) -> str | None:
    try:
        return replace_file_mentions(user_input)
    except (UnicodeDecodeError, OSError, ValueError) as error:
        print(f'Ошибка: {error}')
        return None


def request_answer(
    client: Any,
    config: AppConfig,
    messages: list[Message],
) -> str | None:
    try:
        return ask_llm(client, config, messages)
    except KeyboardInterrupt:
        print('\nпрервали')
        return None
    except Exception as error:
        print(f'Ошибка: {error}')
        return None


def add_message(
    messages: list[Message],
    role: str,
    content: str,
) -> None:
    messages.append(
        {
            'role': role,
            'content': content,
        },
    )


def process_chat_message(
    client: Any,
    config: AppConfig,
    messages: list[Message],
    user_input: str,
) -> list[Message]:
    prepared_input = prepare_input(user_input)

    if prepared_input is None:
        return messages

    add_message(messages, 'user', prepared_input)
    messages = trim_context(messages, config)

    answer = request_answer(client, config, messages)

    if answer is None:
        return messages

    print(answer)
    add_message(messages, 'assistant', answer)

    return trim_context(messages, config)


def process_command(
    client: Any,
    config: AppConfig,
    messages: list[Message],
    user_input: str,
) -> CommandResult:
    if user_input == QUIT_COMMAND:
        print('Пока!')
        return messages, True

    if is_reset_command(user_input):
        return reset_messages(config), False

    if is_file_chunk_command(user_input):
        run_file_chunk_mode(client, config, user_input)
        return messages, False

    return None, False


def create_app_data() -> AppData:
    config = load_config()
    client = create_client(config)
    messages = init_messages(config)

    return config, client, messages


def process_main_loop_step(
    client: Any,
    config: AppConfig,
    messages: list[Message],
) -> bool:
    user_input = input('>>> ').strip()

    command_result, should_stop = process_command(
        client,
        config,
        messages,
        user_input,
    )

    if should_stop:
        return True

    if command_result is not None:
        messages.clear()
        messages.extend(command_result)
        return False

    if not user_input:
        return False

    new_messages = process_chat_message(
        client,
        config,
        messages,
        user_input,
    )

    messages.clear()
    messages.extend(new_messages)

    return False


def main() -> None:
    config, client, messages = create_app_data()

    print_greeting()

    while True:
        should_stop = process_main_loop_step(
            client,
            config,
            messages,
        )

        if should_stop:
            break


if __name__ == '__main__':
    main()
