import json
import logging
import os
from time import time, sleep
from copy import deepcopy
from multiprocessing import Queue
from queue import Empty
from typing import List, Optional, Dict

import requests
from selenium.common import TimeoutException, NoSuchElementException
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
    current_url: Optional[str] = None
    current_value: Optional[str] = None
    time_to_change_address: Optional[float] = None

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

        self.current_url = "https://nuwber.com/"
        self.get_request_to_url()

        for value in self.in_data:
            print(f"value = {value}")
            self.check_timeout_for_change_address()

            value = value.replace("\t", " ").replace("\n", " ").strip()
            self.current_value = value

            self.make_request()
            if "@" in self.current_value:
                result = self.parse_person()
                self.queue_main.put({"type": "new_data", "data": result})
                self.queue_main.put({"type": "parsed_value", "value": value})
                print("SENDED EMAIL")
                continue

            flag = False
            for _ in range(3):
                if self.find_owners_block():
                    logger.info("Нашел блок владельцев! Начинаю парсить...")
                    flag = True
                    break

                if self.find_unexpected_addresses_block():
                    logger.info("Нашел неожиданный блок адресов! Пропускаю....")
                    break

                if (not self.subscribe_msg_is_active()) and self.find_card_block():
                    logger.info("По адресу нету владельцев! Пропускаю...")
                    break

                self.root_cause_search()

            if not flag:
                continue

            owners_els = self.driver.find_element(By.ID, "ownerBlock").find_elements(
                By.CLASS_NAME, "bordered-tiles-header.js-touch-trigger")
            persons_urls = [el.get_attribute("href") for el in owners_els]
            for pers_url in persons_urls:
                logger.info(f"Спарсил ссылку на персону: {pers_url}")
                self.current_url = pers_url
                self.get_request_to_url()
                result = self.parse_person()
                self.queue_main.put({"type": "new_data", "data": result})

            self.queue_main.put({"type": "parsed_value", "value": value})
            print("SENDED ADDRESS")

        logger.info("Процесс успешно закончил свою работу!")

    def get_request_to_url(self, retries: int = 5):
        try:
            self.driver.get(self.current_url)

        except Exception as ex:
            logger.info(f"Не удалось сделать запрос! Осталось попыток: {retries} | {ex}")
            sleep(5)

            if retries <= 0:
                logger.info("Инициализирую новый webdriver...")
                self.get_new_webdriver()
                self.get_request_to_url(retries=5)

            else:
                self.get_request_to_url(retries=retries - 1)

    def find_card_block(self) -> bool:
        try:
            self.driver.find_element(By.ID, "cardBlock")
            return True

        except NoSuchElementException:
            return False

    def find_owners_block(self) -> bool:
        try:
            WebDriverWait(self.driver, 5).until((ec.presence_of_element_located((By.ID, "ownerBlock"))))
            return True

        except TimeoutException:
            return False

    def find_unexpected_addresses_block(self) -> bool:
        try:
            self.driver.find_element(By.CLASS_NAME, "address-item")
            return True

        except NoSuchElementException:
            return False

    def search_processing(self, main_page: bool):
        if main_page:
            search_panel_el = self.driver.find_element(By.ID, "search-panel")
            tabs_els = search_panel_el.find_element(By.CLASS_NAME, "search__tabs").find_elements(By.TAG_NAME, "li")
            if "@" in self.current_value:
                for el in tabs_els:
                    if el.text.strip().lower() == "email":
                        self.driver.execute_script(
                            "arguments[0].scrollIntoView({ behavior: 'smooth', block: 'center' });", el)
                        sleep(0.5)
                        el.click()
                        break

                li_els = self.driver.find_element(By.ID, "search-panel").find_element(
                    By.CLASS_NAME, "search__blocks").find_elements(By.TAG_NAME, "li")
                for el in li_els:
                    if el.get_attribute("class") == "active":
                        el.find_element(By.ID, "search-panel_email").send_keys(self.current_value)
                        sleep(0.5)
                        el.find_element(By.TAG_NAME, "button").click()
                        break

            else:
                for el in tabs_els:
                    if el.text.strip().lower() == "address":
                        self.driver.execute_script(
                            "arguments[0].scrollIntoView({ behavior: 'smooth', block: 'center' });", el)
                        sleep(0.5)
                        el.click()
                        break

                li_els = self.driver.find_element(By.ID, "search-panel").find_element(
                    By.CLASS_NAME, "search__blocks").find_elements(By.TAG_NAME, "li")
                for el in li_els:
                    if el.get_attribute("class") == "active":
                        el.find_element(By.ID, "search-panel_address").send_keys(self.current_value)
                        el.find_element(By.TAG_NAME, "button").click()
                        break

        else:
            header_search_el = self.driver.find_element(By.CLASS_NAME, "header-search-content")
            tabs_els = header_search_el.find_element(By.CLASS_NAME, "search__tabs").find_elements(By.TAG_NAME, "li")
            if "@" in self.current_value:
                for el in tabs_els:
                    if el.text.strip().lower() == "email":
                        self.driver.execute_script(
                            "arguments[0].scrollIntoView({ behavior: 'smooth', block: 'center' });", el)
                        sleep(0.5)
                        el.click()
                        break

                li_els = self.driver.find_element(By.CLASS_NAME, "header-search-content").find_element(
                    By.CLASS_NAME, "search__blocks").find_elements(By.TAG_NAME, "li")
                for el in li_els:
                    if el.get_attribute("class") == "active":
                        el.find_element(By.TAG_NAME, "input").send_keys(self.current_value)
                        el.find_element(By.TAG_NAME, "button").click()

            else:
                for el in tabs_els:
                    if el.text.strip().lower() == "address":
                        self.driver.execute_script(
                            "arguments[0].scrollIntoView({ behavior: 'smooth', block: 'center' });", el)
                        sleep(0.5)
                        el.click()
                        break

                li_els = self.driver.find_element(By.CLASS_NAME, "header-search-content").find_element(
                    By.CLASS_NAME, "search__blocks").find_elements(By.TAG_NAME, "li")
                for el in li_els:
                    if el.get_attribute("class") == "active":
                        el.find_element(By.TAG_NAME, "input").clear()
                        el.find_element(By.TAG_NAME, "input").send_keys(self.current_value)
                        el.find_element(By.TAG_NAME, "button").click()
                        break

    def make_request(self):
        main_page = None
        try:
            self.driver.find_element(By.ID, "search-panel")
            main_page = True

        except NoSuchElementException:
            pass

        if main_page is None:
            try:
                self.driver.find_element(By.CLASS_NAME, "header-search-content")
                main_page = False

            except NoSuchElementException:
                pass

        if main_page is None:
            self.root_cause_search()
            return self.make_request()

        try:
            self.search_processing(main_page=main_page)

        except NoSuchElementException:
            self.root_cause_search()
            return self.make_request()

    def parse_person(self, retries: int = 3) -> List[str]:
        try:
            fullname = WebDriverWait(
                self.driver, 5).until(ec.presence_of_element_located((By.XPATH, '//b[@itemprop="name"]'))).text

        except Exception:
            logger.info("Не удалось получить имя")

            if retries <= 0:
                logger.error(f"Не удалось спарсить - . Пропускаю ссылку...")
                return []

            self.root_cause_search()
            if "@" in self.current_value:
                self.make_request()

            return self.parse_person(retries=retries - 1)

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
            house_info = "\n".join([el.text for el in house_info_els])

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

            landlines_info = "\n".join(landlines_info)

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

            cell_phones_info = "\n".join(cell_phones_info)

        except TimeoutException:
            cell_phones_info = ""

        try:
            emails_els = WebDriverWait(self.driver, 1).until(
                ec.presence_of_element_located((By.ID, "emailsBlock"))).find_elements(By.CLASS_NAME, "person-item")
            emails = "\n".join([el.text.strip() for el in emails_els])

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
            if self.proxy.change_address_url and self.request_to_change_address():
                self.get_request_to_url()
                sleep(10)
                return

            old_proxy = deepcopy(self.proxy)
            self.get_new_proxy()
            if self.proxy.host == old_proxy.host and self.proxy.port == old_proxy.port:
                sleep(45)

            else:
                self.get_new_webdriver()

            self.get_request_to_url()
            self.root_cause_search()
            return

    def many_requests_msg_is_active(self) -> bool:
        try:
            self.driver.find_element(By.CLASS_NAME, "troubleshooting")
            logger.info("Сообщение о запросах на странице!")
            return True

        except NoSuchElementException:
            return False

    def reset_subscribe(self):
        self.driver.delete_all_cookies()
        self.driver.refresh()

        if self.captcha_is_active():
            self.pass_captcha()

    def subscribe_msg_is_active(self) -> bool:
        try:
            self.driver.find_element(By.CLASS_NAME, "lookup-outer")
            logger.info("Бесплатная подписка закончилась!")
            return True

        except NoSuchElementException:
            return False

    def captcha_is_active(self) -> bool:
        try:
            self.driver.find_element(By.CLASS_NAME, "loading-verifying")
            logger.info("Капча на странице!")
            return True

        except NoSuchElementException:
            return False

    def pass_captcha(self):
        x, y = 415, 120

        actions = ActionChains(self.driver)
        actions.move_by_offset(5, 5).perform()
        sleep(0.2)
        actions.move_by_offset(10, -3).perform()
        sleep(0.3)
        actions.move_by_offset(20, 4).perform()
        sleep(0.3)
        actions.move_by_offset(x, y).click().perform()
        actions.move_by_offset(-x - 35, -y - 6).perform()

        sleep(10)
        logger.info("Выполнил действия для решения капчи!")

        if self.captcha_is_active():
            self.pass_captcha()

    def get_new_webdriver(self):
        if self.driver:
            self.driver.quit()

        options = ChromeOptions()
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_argument("--disable-background-timer-throttling")
        options.add_argument("--disable-backgrounding-occluded-windows")
        options.add_argument("--disable-renderer-backgrounding")

        if self.proxy.username:
            ext_path = os.path.abspath(f"proxy_extensions/{self.proxy.formulate_filename()}/")
            options.add_argument(f"--load-extension={ext_path}")

        else:
            options.add_argument(f"--proxy-server=http://{self.proxy.host}:{self.proxy.port}")

        self.driver = Chrome(options=options)
        self.driver.set_window_size(width=1100, height=600)
        self.driver.execute_cdp_cmd(
            "Page.addScriptToEvaluateOnNewDocument",
            {
                "source": """
                    Object.defineProperty(document, 'hidden', {value: false});
                    Object.defineProperty(document, 'visibilityState', {value: 'visible'});
                    document.addEventListener('visibilitychange', (e) => { e.stopImmediatePropagation(); }, true);
                """
            }
        )

        self.time_to_change_address = time()
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

    def check_timeout_for_change_address(self):
        if self.proxy.change_address_url is None:
            return

        if time() - self.time_to_change_address >= Config.REQUEST_TO_CHANGE_ADDRESS_TIMEOUT:
            self.request_to_change_address()

        else:
            logger.info(f"Время смены адреса ещё не настало! Текущий timestamp: {self.time_to_change_address}")

    def request_to_change_address(self) -> bool:
        answer_raw = requests.get(url=self.proxy.change_address_url)
        answer_json = json.loads(answer_raw.text)
        if answer_json.get("success"):
            logger.info("Адрес был успешно сменен!")
            self.time_to_change_address = time()
            return True

        else:
            logger.info("Не удалось сменить адрес!")
            return False
