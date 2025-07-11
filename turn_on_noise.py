import time
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
    try:
        requests.get("https://www.google.com", timeout=timeout)
        return True
    except requests.RequestException:
        return False


def parse_config_list(raw_value: str) -> list:
    # Убираем кавычки и делим по запятой
    return [x.strip().strip('"') for x in raw_value.strip().split(",") if x.strip()]


def launch_browser(
    url: str, browser_path: str, chromedriver_path: str, args: list
) -> webdriver.Chrome:
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


def click_button(driver, id):
    try:
        # Ждём 100 секунд пока кнопка play не станет кликабельной

        wait = WebDriverWait(driver, 100)
        play_button = wait.until(EC.element_to_be_clickable((By.ID, id)))

        play_button.click()
        logger.info(f"Клик по кнопке (id={id}) выполнен.")
        return True

    except TimeoutException:
        logger.error("Кнопка 'mute' не стала кликабельной за 60 секунд.")
        return False

    except WebDriverException as e:
        logger.error(f"Selenium-ошибка при попытке клика: {e}")
        return False


def turn_on_noise(config):
    def minimize_browser_window():
        for w in gw.getWindowsWithTitle("Chromium"):
            if w.isActive:
                w.minimize()
                return True
        return False

    browser_path = config.get("browser_path")
    chromedriver_path = config.get("chromedriver_path")
    noise_timer = int(config.get("noise_timer", 60))

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
            time.sleep(60)
            continue

        url = random.choice(all_links)
        logger.info(f"Переключаемся на: {url}")

        try:
            driver.get(url)

            if url in noise_links:
                logger.debug("Ожидаем кнопку Play...")
                time.sleep(10)  # Обязательно иначе багует кнопка
                click_button(driver, "mute")
                if config["slider_animation"]:
                    click_button(driver, "anim")
                minimize_browser_window()
            else:
                logger.warning(
                    'Нет необходимых ссылок, добавьте ссылки: "https://mynoise.net...'
                )

        except Exception as e:
            logger.error(f"Ошибка при переходе: {e}")

        logger.info(f"Следующая смена через {noise_timer} мин")
        time.sleep(noise_timer * 60)
