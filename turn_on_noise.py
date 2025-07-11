import time
import random
import requests
import ctypes
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from loguru import logger


def internet_on(timeout=5) -> bool:
    try:
        requests.get("https://www.google.com", timeout=timeout)
        return True
    except requests.RequestException:
        return False


def is_english_layout() -> bool:
    user32 = ctypes.WinDLL("user32")
    hwnd = user32.GetForegroundWindow()
    thread_id = user32.GetWindowThreadProcessId(hwnd, 0)
    layout_id = user32.GetKeyboardLayout(thread_id)
    lang_id = layout_id & (2**16 - 1)
    return lang_id == 0x409  # English layout


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

    service = Service(chromedriver_path)
    driver = webdriver.Chrome(service=service, options=options)
    driver.get(url)
    return driver


def click_play_button(driver: webdriver.Chrome) -> bool:
    try:
        driver.implicitly_wait(60)

        # Проверка, есть ли элемент mute
        play_button = driver.find_element(By.ID, "mute")

        # Нажимаем
        play_button.click()
        logger.info("Клик по кнопке Play (id='mute') выполнен.")
        return True
    except Exception as e:
        logger.error(f"Не удалось нажать на Play через Selenium: {e}")
        return False


def turn_on_noise(config):
    browser_path = config.get("browser_path")
    chromedriver_path = config.get("chromedriver_path")
    noise_timer = int(config.get("noise_timer", 60)) * 60

    noise_links = parse_config_list(config.get("noise_links"))
    youtube_links = parse_config_list(config.get("youtube_links"))
    browser_args = parse_config_list(config.get("list_args_browser"))

    all_links = noise_links + youtube_links

    logger.info("Запуск фонового шумогенератора")

    while True:
        if not internet_on():
            logger.warning("Нет подключения к интернету. Повтор через 60 секунд...")
            time.sleep(60)
            continue

        url = random.choice(all_links)
        logger.info(f"Открываем: {url}")

        try:
            driver = launch_browser(url, browser_path, chromedriver_path, browser_args)
            if url in noise_links:
                logger.debug("Обнаружен источник myNoise, ожидаем загрузку...")
                time.sleep(10)  # Ждём загрузки
                click_play_button(driver)
            else:
                logger.debug("YouTube-радио не требует взаимодействия.")
        except Exception as e:
            logger.error(f"Ошибка при запуске браузера или загрузке страницы: {e}")

        logger.info(f"Следующая смена фона через {noise_timer // 60} минут")
        time.sleep(noise_timer)

        try:
            driver.quit()
        except Exception:
            logger.warning("Не удалось закрыть браузер корректно.")
