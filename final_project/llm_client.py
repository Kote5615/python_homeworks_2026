from openai import OpenAI

from config import AppConfig


def create_client(config: AppConfig) -> OpenAI:
    return OpenAI(
        api_key=config.api_key,
        base_url=config.api_host,
    )


def ask_llm(
    client: OpenAI,
    config: AppConfig,
    messages: list[dict[str, str]],
) -> str:
    response = client.chat.completions.create(
        model=config.model,
        messages=messages,
        temperature=config.temperature,
    )

    content = response.choices[0].message.content

    if content is None:
        return ''

    return content
