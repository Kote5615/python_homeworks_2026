import os
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml


@dataclass
class AppConfig:
    api_key: str
    api_host: str
    model: str
    limit_message: int | None
    limit_chars: int | None
    temperature: float
    system_prompt: str | None


def load_yaml_config(path: str = 'config.yaml') -> dict[str, Any]:
    config_path = Path(path)

    if not config_path.exists():
        return {}

    with config_path.open('r', encoding='utf-8') as file:
        config_data = yaml.safe_load(file)

    if config_data is None:
        return {}

    if not isinstance(config_data, dict):
        return {}

    return config_data


def get_optional_int(value: str | int | None) -> int | None:
    if value is None or value == '':
        return None

    return int(value)


def get_optional_float(value: str | float | None, default: float) -> float:
    if value is None or value == '':
        return default

    return float(value)


def make_optional_str(value: object) -> str | None:
    if value is None:
        return None

    return str(value)


def load_config() -> AppConfig:
    yaml_config = load_yaml_config()

    api_key = os.environ.get('API_KEY') or yaml_config.get('api_key')
    api_host = os.environ.get('API_HOST') or yaml_config.get('api_host')
    model = os.environ.get('MODEL') or yaml_config.get('model') or 'deepseek-chat'

    limit_message: Any = os.environ.get('LIMIT_MESSAGE')
    if limit_message is None:
        limit_message = yaml_config.get('limit_message')

    limit_chars: Any = os.environ.get('LIMIT_CHARS')
    if limit_chars is None:
        limit_chars = yaml_config.get('limit_chars')

    temperature: Any = os.environ.get('TEMPERATURE')
    if temperature is None:
        temperature = yaml_config.get('temperature')

    system_prompt = yaml_config.get('system_prompt')

    if not api_key or not api_host:
        print(
            'Ошибка: не найдены API_KEY/API_HOST ни в переменных окружения, ни в config.yaml.',
        )
        sys.exit(1)

    parsed_temperature = get_optional_float(temperature, default=0.69)

    if not 0 <= parsed_temperature <= 1:
        print('Ошибка: температура от 0 до 1')
        sys.exit(1)

    return AppConfig(
        api_key=str(api_key),
        api_host=str(api_host),
        model=str(model),
        limit_message=get_optional_int(limit_message),
        limit_chars=get_optional_int(limit_chars),
        temperature=parsed_temperature,
        system_prompt=make_optional_str(system_prompt),
    )
