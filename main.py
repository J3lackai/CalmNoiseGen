import random
import time
import requests
import ctypes
import threading
import configparser
import sys
import os
from loguru import logger
from configparser import ConfigParser
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.keys import Keys

def init_loguru_logging()->None:
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
def load_main_sect_cfg()->ConfigParser:
    config = ConfigParser.read()
    try:
        config = config["Main"]

    except configparser.NoSectionError:
        logger.error("Ошибка: Отсутствует секция в конфиге.")
    return config
def main()
    init_loguru_logging()
    load_main_sect_cfg()
    noise_links = config["noise_links"]
    yt_links = config["youtube_links"]
    BROWSER_PATH = config["browser_path"]
    CHROMEDRIVER_PATH = config["chromedriver_path"]

# Проверка интернета (пингуем google)
def internet_on():
    try:
        requests.get("https://www.google.com", timeout=5)
        return True
    except Exception:
        return False


# Проверка раскладки клавиатуры (Windows)
# Возвращает True если раскладка английская, False если русская (или другая)
def is_english_layout():
    # Используем Windows API через ctypes
    user32 = ctypes.WinDLL("user32")
    hwnd = user32.GetForegroundWindow()
    thread_id = user32.GetWindowThreadProcessId(hwnd, 0)
    layout_id = user32.GetKeyboardLayout(thread_id)
    # низшие 16 бит — языковой идентификатор
    lang_id = layout_id & (2**16 - 1)
    # 0x409 = English US, 0x804 = Chinese, 0x419 = Russian
    # Проверяем на английскую (0x409)
    return lang_id == 0x409


# Запуск браузера с Selenium
def launch_browser(url):
    options = Options()
    options.binary_location = BROWSER_PATH
    # Можно добавить, чтобы не мешал — запускать в режиме окна с минимальным размером и в фоне
    options.add_argument("--window-position=0,0")
    options.add_argument("--window-size=800,600")
    options.add_argument("--mute-audio")
    options.add_argument("--disable-infobars")
    options.add_argument("--no-default-browser-check")
    options.add_argument("--disable-extensions")
    options.add_argument("--disable-popup-blocking")
    options.add_argument("--disable-notifications")

    service = Service(CHROMEDRIVER_PATH)
    driver = webdriver.Chrome(service=service, options=options)

    driver.get(url)
    return driver


# Для myNoise нужно нажать кнопку "P" на английской раскладке
def press_p_key(driver):
    # Проверяем раскладку
    if not is_english_layout():
        print("[INFO] Раскладка не английская — не нажимаем P")
        return False
    # Нажимаем P
    body = driver.find_element("tag name", "body")
    body.send_keys("p")
    print("[INFO] Нажали P")
    return True


# Основной цикл смены фона каждый час
def main_loop():
    current_driver = None

    while True:
        if not internet_on():
            print("[WARN] Нет интернета — жду 60 секунд")
            time.sleep(60)
            continue

        # Закрываем предыдущий браузер если открыт
        if current_driver:
            try:
                current_driver.quit()
            except:
                pass
            current_driver = None

        # Выбираем случайный URL
        url = random.choice(all_links)
        print(f"[INFO] Запускаем: {url}")

        # Запускаем браузер
        current_driver = launch_browser(url)

        # Если ссылка на myNoise — ждем загрузки и нажимаем P
        if url in mynoise_links:
            time.sleep(
                10
            )  # ждем загрузки страницы (можно увеличить если связь медленная)
            press_p_key(current_driver)
        else:
            # YouTube — просто оставляем открытым
            pass

        # Ждем 1 час (3600 секунд)
        for _ in range(60):
            time.sleep(60)
            # Здесь можно вставить проверки прерывания, если нужно


# Запуск в отдельном потоке, чтобы можно было расширять потом (например, GUI)
def start():
    thread = threading.Thread(target=main_loop, daemon=True)
    thread.start()
    print("[INFO] Фоновый цикл запущен. Ctrl+C для выхода.")


if __name__ == "__main__":
    start()

    # Просто держим основной поток живым
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("[INFO] Выход")
