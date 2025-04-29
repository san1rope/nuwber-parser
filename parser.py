import logging
import os
import time
from copy import deepcopy
from multiprocessing import Queue
from queue import Empty
from typing import List, Optional, Dict

from selenium.common import TimeoutException, NoSuchElementException
from selenium.webdriver import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.support.wait import WebDriverWait
from undetected_chromedriver import Chrome, ChromeOptions

from models import Proxy

logger = logging.getLogger(__name__)


class Parser:
    proxy: Optional[Proxy] = None
    driver: Optional[Chrome] = None
    current_url: Optional[str] = None
    first_request: Optional[bool] = None

    def __init__(self, queue_dict: Dict[str, Queue], in_data: List[str]):
        self.queue_main = queue_dict["main"]
        self.queue_sub = queue_dict["sub"]
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
                url = f"https://nuwber.com/search/email?email={value.strip()}"
                result = self.parse_person(url=url)
                self.queue_main.put({"type": "new_data", "data": result})
                continue

            else:
                url = "https://nuwber.com/search/address?addressQuery=" + "%20".join(value.split())

            self.current_url = url
            self.driver.get(url)
            logger.info(f"Сделал запрос к {url}")

            flag = False
            while True:
                try:
                    owner_block_el = WebDriverWait(self.driver, 7).until((
                        ec.presence_of_element_located((By.ID, "ownerBlock"))
                    ))
                    logger.info("Нашел блок владельцев! Начинаю парсить...")
                    break

                except TimeoutException:
                    logger.info("Не удалось найти блок владельцев!")
                    try:
                        self.driver.find_element(By.CLASS_NAME, "address-item")
                        logger.info("Нашел неожиданный блок адресов! Пропускаю....")
                        flag = True
                        break

                    except NoSuchElementException:
                        self.root_cause_search()

            if flag:
                continue

            owners_els = owner_block_el.find_elements(By.CLASS_NAME, "bordered-tiles-header.js-touch-trigger")
            persons_urls = [el.get_attribute("href") for el in owners_els]
            for pers_url in persons_urls:
                logger.info(f"Спарсил ссылку на персону: {pers_url}")
                result = self.parse_person(url=pers_url)
                self.queue_main.put({"type": "new_data", "data": result})

        logger.info("Процесс успешно закончил свою работу!")

    def parse_person(self, url: str, retries: int = 3) -> List[str]:
        self.current_url = url
        self.driver.get(url)
        logger.info(f"Сделал запрос к {url}")

        try:
            fullname = WebDriverWait(
                self.driver, 5).until(ec.presence_of_element_located((By.XPATH, '//b[@itemprop="name"]'))).text

        except TimeoutException:
            logger.info("Не удалось получить имя")

            if retries <= 0:
                logger.error(f"Не удалось спарсить - {url}. Пропускаю ссылку...")
                return []

            self.root_cause_search()
            return self.parse_person(url=url, retries=retries - 1)

        try:
            birth_date = WebDriverWait(self.driver, 1).until(
                ec.presence_of_element_located((By.XPATH, '//meta[@itemprop="birthDate"]'))).get_attribute("content")

        except TimeoutException:
            birth_date = ""

        try:
            gender = WebDriverWait(self.driver, 1).until(
                ec.presence_of_element_located((By.XPATH, '//meta[@itemprop="gender"]'))).get_attribute("content")

        except TimeoutException:
            gender = ""

        try:
            address = WebDriverWait(self.driver, 1).until(
                ec.presence_of_element_located((By.CLASS_NAME, 'address-line'))).text.replace('\n', '').strip()

        except TimeoutException:
            address = ""

        try:
            house_info_els = WebDriverWait(self.driver, 1).until(
                ec.presence_of_element_located((By.ID, "propertyBlock"))).find_elements(
                By.CLASS_NAME, "person-item-text")
            house_info = " | ".join([el.text for el in house_info_els])

        except TimeoutException:
            house_info = ""

        try:
            landlines_els = WebDriverWait(self.driver, 1).until(
                ec.presence_of_element_located((By.ID, "landlinePhonesBlock"))).find_elements(
                By.CLASS_NAME, "person-item")
            landlines_info = []
            for el in landlines_els:
                number = el.find_element(By.CLASS_NAME, "person-item-text").text.strip()
                last_seen = el.find_element(By.CLASS_NAME, "person-item-additional").text.replace("Seen", "").strip()
                landlines_info.append(f"{number}; {last_seen}")

            landlines_info = " | ".join(landlines_info)

        except TimeoutException:
            landlines_info = ""

        try:
            cell_phones_els = WebDriverWait(self.driver, 1).until(
                ec.presence_of_element_located((By.ID, "mobilePhonesBlock"))).find_elements(
                By.CLASS_NAME, "person-item")
            cell_phones_info = []
            for el in cell_phones_els:
                number = el.find_element(By.CLASS_NAME, "person-item-text").text.strip()
                last_seen = el.find_element(By.CLASS_NAME, "person-item-additional").text.replace("Seen", "").strip()
                cell_phones_info.append(f"{number}; {last_seen}")

            cell_phones_info = " | ".join(cell_phones_info)

        except TimeoutException:
            cell_phones_info = ""

        try:
            emails_els = WebDriverWait(self.driver, 1).until(
                ec.presence_of_element_located((By.ID, "emailsBlock"))).find_elements(By.CLASS_NAME, "person-item")
            emails = " | ".join([el.text.strip() for el in emails_els])

        except TimeoutException:
            emails = ""

        return [fullname, birth_date, gender, address, house_info, landlines_info, cell_phones_info, emails]

    def root_cause_search(self):
        if self.subscribe_msg_is_active():
            self.reset_subscribe()
            return

        if self.captcha_is_active():
            self.pass_captcha()
            return

        if self.many_requests_msg_is_active():
            old_proxy = deepcopy(self.proxy)
            self.get_new_proxy()
            if self.proxy.host == old_proxy.host and self.proxy.port == old_proxy.port:
                time.sleep(70)

            else:
                self.get_new_webdriver()

            self.driver.get(self.current_url)
            self.root_cause_search()
            return

    def many_requests_msg_is_active(self) -> bool:
        logger.info("Проверяю состояния сообщения о черезмерном количестве запросов...")
        try:
            self.driver.find_element(By.CLASS_NAME, "troubleshooting")
            logger.info("Сообщение о запросах на странице!")
            return True

        except NoSuchElementException:
            logger.info("Сообщение о запросах нету!")
            return False

    def reset_subscribe(self):
        self.driver.delete_all_cookies()
        self.driver.refresh()

        if self.captcha_is_active():
            self.pass_captcha()

    def subscribe_msg_is_active(self) -> bool:
        logger.info("Проверяю состояние сообщения о подписке...")
        try:
            self.driver.find_element(By.CLASS_NAME, "lookup-outer")
            logger.info("Бесплатная подписка закончилась!")
            return True

        except NoSuchElementException:
            logger.info("Бесплатная подписка ещё активна!")
            return False

    def captcha_is_active(self) -> bool:
        logger.info("Проверяю наличие капчи...")
        try:
            self.driver.find_element(By.ID, "ppIS7")
            logger.info("Капча на странице!")
            return True

        except NoSuchElementException:
            logger.info("Капчи нету на странице!")
            return False

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
        actions.move_by_offset(-x - 35, -y - 6).perform()

        time.sleep(10)
        logger.info("Выполнил действия для решения капчи!")

        if self.captcha_is_active():
            self.pass_captcha()

    def get_new_webdriver(self):
        if self.driver:
            self.driver.quit()

        options = ChromeOptions()
        options.add_argument('--disable-blink-features=AutomationControlled')

        if self.proxy.username:
            ext_path = os.path.abspath(f"proxy_extensions/{self.proxy.formulate_filename()}/")
            options.add_argument(f"--load-extension={ext_path}")

        else:
            options.add_argument(f"--proxy-server=http://{self.proxy.host}:{self.proxy.port}")

        self.driver = Chrome(options=options)
        self.driver.set_window_size(width=800, height=600)

        logger.info("Создал новый WebDriver!")

    def get_new_proxy(self):
        self.queue_main.put({"type": "get_new_proxy"})

        while True:
            try:
                msg = self.queue_sub.get_nowait()
                self.proxy = Proxy.model_validate(obj=msg)
                break

            except Empty:
                continue

        logger.info("Получил прокси!")
