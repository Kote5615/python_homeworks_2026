from config import AppConfig
from constants import CONTENT_KEY, ROLE_KEY, SYSTEM_ROLE

Message = dict[str, str]


def init_messages(config: AppConfig) -> list[Message]:
    messages = []

    if config.system_prompt is not None:
        system_message = {
            ROLE_KEY: SYSTEM_ROLE,
            CONTENT_KEY: config.system_prompt,
        }

        messages.append(system_message)

    return messages


def count_chars(messages: list[Message]) -> int:
    chars_sum = 0

    for message in messages:
        text = message[CONTENT_KEY]
        chars_sum += len(text)

    return chars_sum


def split_system_and_chat_messages(
    messages: list[Message],
) -> tuple[list[Message], list[Message]]:
    system_messages = []
    chat_messages = []

    for message in messages:
        if message[ROLE_KEY] == SYSTEM_ROLE:
            system_messages.append(message)
        else:
            chat_messages.append(message)

    return system_messages, chat_messages


def trim_by_message_limit(
    chat_messages: list[Message],
    limit_message: int | None,
) -> None:
    if limit_message is None:
        return

    while len(chat_messages) > limit_message:
        chat_messages.pop(0)


def trim_one_long_message(
    chat_messages: list[Message],
    limit_chars: int,
) -> None:
    old_text = chat_messages[0][CONTENT_KEY]
    new_text = old_text[-limit_chars:]
    chat_messages[0][CONTENT_KEY] = new_text


def trim_by_chars_limit(
    system_messages: list[Message],
    chat_messages: list[Message],
    limit_chars: int | None,
) -> None:
    if limit_chars is None:
        return

    while count_chars(system_messages + chat_messages) > limit_chars:
        if len(chat_messages) == 0:
            return

        if len(chat_messages) == 1:
            trim_one_long_message(chat_messages, limit_chars)
            return

        chat_messages.pop(0)


def trim_context(
    messages: list[Message],
    config: AppConfig,
) -> list[Message]:
    system_messages, chat_messages = split_system_and_chat_messages(messages)

    trim_by_message_limit(chat_messages, config.limit_message)
    trim_by_chars_limit(system_messages, chat_messages, config.limit_chars)

    return system_messages + chat_messages
