import logging
from multiprocessing import Queue
from typing import List, Optional

from undetected_chromedriver import Chrome, ChromeOptions

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

        for value in self.in_data:
            pass

    def get_new_webdriver(self):
        options = ChromeOptions()
        options.add_argument()
