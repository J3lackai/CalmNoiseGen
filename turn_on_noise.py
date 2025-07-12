from time import sleep
import random
import requests
import os
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from loguru import logger
import pygetwindow as gw


def internet_on(timeout=5) -> bool:
    """
    Проверяет наличие интернет-соединения путём обращения к Google.

    :param timeout: Таймаут запроса в секундах.
    :return: True, если соединение установлено, иначе False.
    """
    try:
        requests.get("https://www.google.com", timeout=timeout)
        return True
    except requests.RequestException:
        return False


def parse_config_list(raw_value: str) -> list:
    """
    Преобразует строку из config в список строк, удаляя кавычки и пробелы.
    """
    return [x.strip().strip('"') for x in raw_value.strip().split(",") if x.strip()]


def launch_browser(
    url: str, browser_path: str, chromedriver_path: str, args: list
) -> webdriver.Chrome:
    """
    Запускает Chrome-браузер с заданными аргументами и открывает нужную ссылку.

    :param url: URL для перехода
    :param browser_path: Путь до исполняемого файла браузера
    :param chromedriver_path: Путь до chromedriver.exe
    :param args: Список аргументов запуска браузера
    :return: Объект драйвера Selenium
    """
    options = Options()
    options.binary_location = browser_path
    for arg in args:
        options.add_argument(arg)

    service = Service(
        chromedriver_path, log_path=os.devnull
    )  # Подавляем логи, чтобы не всплывали не нужные сообщения
    driver = webdriver.Chrome(service=service, options=options)
    driver.get(url)
    return driver


def change_volume_button(driver, val_dif=0) -> None:
    """
    Изменяет громкость на mynoise.net нажатием кнопок volUp/volDown.

    :param driver: Экземпляр webdriver
    :param val_dif: Изменение громкости (отрицательное - тише, положительное - громче)
    :return: True, если удалось, иначе False
    """
    try:
        wait = WebDriverWait(driver, 30)
        id = "volDown" if val_dif < 0 else "volUp"
        label = "тише" if val_dif < 0 else "громче"
        for _ in range(abs(val_dif) * 2):
            play_button = wait.until(EC.element_to_be_clickable((By.ID, id)))
            play_button.click()
            sleep(0.85)
        logger.info(f"Сделали {label} на {abs(val_dif)} от средней громкости.")
        return True

    except TimeoutException:
        logger.error(f"Кнопка (id={id}) не стала кликабельной за 60 секунд.")
        return False

    except WebDriverException as e:
        logger.error(f"Selenium-ошибка при попытке клика: {e}")
        return False


def click_button(driver, id) -> None:
    """
    Пытается нажать на кнопку по ID, ожидая её появления до 100 секунд.

    :param driver: Экземпляр webdriver
    :param id: HTML id кнопки
    :return: True, если успешно, иначе False
    """
    try:
        # Ждём 100 секунд пока кнопка play не станет кликабельной

        wait = WebDriverWait(driver, 100)
        play_button = wait.until(EC.element_to_be_clickable((By.ID, id)))

        play_button.click()
        logger.info(f"Клик по кнопке (id={id}) выполнен.")
        return True

    except TimeoutException:
        logger.error(f"Кнопка (id={id}) не стала кликабельной за 60 секунд.")
        return False

    except WebDriverException as e:
        logger.error(f"Selenium-ошибка при попытке клика: {e}")
        return False


def turn_on_noise(config) -> None:
    """
    Основная функция: запускает браузер и периодически переключает фоновые шумы.
    Работает бесконечно, проверяя интернет, выбирая ссылку и настраивая шум.

    :param config: Объект конфигурации из configparser
    """

    def minimize_browser_window() -> None:
        """
        Функция сворачивает окно браузера
        """
        for w in gw.getWindowsWithTitle("Chromium"):
            if w.isActive:
                w.minimize()
                return True
        return False

    browser_path = config.get("browser_path")
    chromedriver_path = config.get("chromedriver_path")
    noise_timer = int(config.get("noise_timer", 60))
    volume = int(config["volume"])
    if not (0 <= volume <= 10):
        logger.error("Ошибка: value может принимать значения только от 0 до 10")
        logger.info("Взято значение по-умолчанию 5")
        volume = 5
    noise_links = parse_config_list(config.get("mynoise.net_links"))
    browser_args = parse_config_list(config.get("list_args_browser"))

    all_links = noise_links

    logger.info("Запуск фонового шумогенератора")

    driver = launch_browser(
        "about:blank", browser_path, chromedriver_path, browser_args
    )
    while True:
        if not internet_on():
            logger.warning("Нет интернета — жду 60 секунд")
            sleep(60)
            continue

        url = random.choice(all_links)
        logger.info(f"Переключаемся на: {url}")

        try:
            driver.get(url)

            if url in noise_links:
                logger.debug("Ожидаем кнопку Play...")
                sleep(10)  # Обязательно иначе багует кнопка
                click_button(driver, "mute")
                if config.getboolean("slider_animation", fallback=True):
                    click_button(driver, "anim")
                if volume != 5:
                    if volume < 5:
                        val_dif = -(5 - volume % 5)
                    else:
                        val_dif = ((volume // 5 - 1) * 5) + volume % 5
                    change_volume_button(driver, val_dif)
                minimize_browser_window()
            else:
                logger.warning(
                    'Нет необходимых ссылок, добавьте ссылки: "https://mynoise.net...'
                )

        except Exception as e:
            logger.error(f"Ошибка при переходе: {e}")

        logger.info(f"Следующая смена через {noise_timer} мин")
        sleep(noise_timer * 60)
