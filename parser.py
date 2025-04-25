import logging
import os
import time
from multiprocessing import Queue
from queue import Empty
from typing import List, Optional

from selenium.common import TimeoutException
from selenium.webdriver import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.support.wait import WebDriverWait
from undetected_chromedriver import Chrome, ChromeOptions

from config import Config
from models import Proxy

logger = logging.getLogger(__name__)


class Parser:
    proxy: Optional[Proxy] = None
    driver: Optional[Chrome] = None

    def __init__(self, queue: Queue, in_data: List[str]):
        self.queue = queue
        self.in_data = in_data

        logging.basicConfig(level=logging.INFO,
                            format=u'%(filename)s:%(lineno)d #%(levelname)-8s [%(asctime)s] - %(name)s - %(message)s')

        self.start()

    def start(self):
        logger.info(f"Процесс запущен!")

        self.get_new_proxy()
        self.get_new_webdriver()

        for value in self.in_data:
            if "@" in value:
                url = ""

            else:
                url = "https://nuwber.com/search/address?addressQuery=" + "%20".join(value.split())

            self.driver.get(url)
            logger.info(f"Сделал запрос к {url}")

            while True:
                try:
                    owner_block_el = WebDriverWait(self.driver, 7).until((
                        ec.presence_of_element_located((By.ID, "ownerBlock"))
                    ))
                    logger.info("Нашел блок владельцев! Начинаю парсить...")
                    break

                except TimeoutException:
                    logger.info("Не удалось найти блок владельцев! Перехожу к решению капчи...")
                    self.pass_captcha()

            owners_els = owner_block_el.find_elements(By.CLASS_NAME, "bordered-tiles-header.js-touch-trigger")
            for own_el in owners_els:
                person_url = own_el.get_attribute("href")
                logger.info(f"Спарсил ссылку на персону: {person_url}")

                result = self.parse_person(url=person_url)

            time.sleep(1000)  # temp

        time.sleep(1000)  # temp

    def parse_person(self, url: str):
        self.driver.get(url)
        logger.info(f"Сделал запрос к {url}")

        time.sleep(1000)  # temp

    def pass_captcha(self):
        x, y = 265, 100

        actions = ActionChains(self.driver)
        actions.move_by_offset(5, 5).perform()
        time.sleep(0.2)
        actions.move_by_offset(10, -3).perform()
        time.sleep(0.3)
        actions.move_by_offset(20, 4).perform()
        time.sleep(0.3)
        actions.move_by_offset(x, y).click().perform()
        actions.move_by_offset(-x - 35, -6).perform()

        time.sleep(10)
        logger.info("Выполнил действия для решения капчи!")

    def get_new_webdriver(self):
        options = ChromeOptions()
        ext_path = os.path.abspath(f"proxy_extensions/{self.proxy.formulate_filename()}/")
        options.add_argument(f"--load-extension={ext_path}")

        if Config.HEADLESS:
            options.add_argument("--headless")
            options.add_argument("--no-sandbox")

        self.driver = Chrome(options=options)
        self.driver.set_window_size(width=800, height=600)

        logger.info("Создал новый WebDriver!")

    def get_new_proxy(self):
        self.queue.put({"type": "get_new_proxy"})
        time.sleep(2)

        while True:
            try:
                msg = self.queue.get_nowait()
                self.proxy = Proxy.model_validate(obj=msg)
                break

            except Empty:
                continue

        logger.info("Получил прокси!")
