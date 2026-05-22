from config import AppConfig


def init_messages(config: AppConfig) -> list[dict[str, str]]:
    messages = []

    if config.system_prompt is not None:
        system_message = {
            'role': 'system',
            'content': config.system_prompt,
        }

        messages.append(system_message)

    return messages


def count_chars(messages: list[dict[str, str]]) -> int:
    summ = 0

    for message in messages:
        text = message['content']
        summ += len(text)

    return summ


def trim_context(
    messages: list[dict[str, str]],
    config: AppConfig,
) -> list[dict[str, str]]:
    system_messages = []
    chat_messages = []

    for message in messages:
        if message['role'] == 'system':
            system_messages.append(message)
        else:
            chat_messages.append(message)

    if config.limit_message is not None:
        while len(chat_messages) > config.limit_message:
            chat_messages.pop(0)

    if config.limit_chars is not None:
        while count_chars(system_messages + chat_messages) > config.limit_chars:
            if len(chat_messages) == 0:
                break

            if len(chat_messages) == 1:
                old_text = chat_messages[0]['content']
                new_text = old_text[-config.limit_chars :]
                chat_messages[0]['content'] = new_text
                break

            chat_messages.pop(0)

    return system_messages + chat_messages
