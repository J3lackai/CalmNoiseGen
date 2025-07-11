import configparser
import sys
import os
from turn_on_noise import turn_on_noise
from loguru import logger
from configparser import ConfigParser


def init_loguru_logging() -> None:
    # Инициализация хендлера для вывода сообщений в консоль и в файл (логирование)
    logger.remove()
    logger.add(
        sys.stderr,
        format="|<green> {time: HH:mm:ss} </green>| <level> {level} </level> | {message}",
        level="DEBUG",
    )
    logger.add(
        os.path.join("result.log"),
        format="|{time:YYYY.MM.DD HH:mm}|{level}|{message}|",
        level="DEBUG",
        rotation="500 kb",
    )


def load_main_sect_cfg() -> ConfigParser:
    config = ConfigParser()
    # Проверяем есть ли конфиг в директории скрипта
    if not os.path.exists("config.ini"):
        logger.critical(
            "Ошибка: Не найден файл 'config.ini', создайте его и добавьте него ваши данные! "
            + "Иначе скрипт не будет работать! Шаблон для файла-конфига, можно найти тут:"
        )
        raise
    try:
        config.read("config.ini", encoding="utf-8")
    except configparser.Error as e:
        logger.critical(f"Ошибка при чтении файла конфигурации 'config.ini': {e}.")
        raise
    return config["Main"]


def main():
    init_loguru_logging()
    config = load_main_sect_cfg()
    turn_on_noise(config)


if __name__ == "__main__":
    main()
