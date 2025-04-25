import logging
import math
import time
from multiprocessing import Process, Queue
from queue import Empty
from typing import Dict, Optional, List

from config import Config
from models import Proxy
from parser import Parser

logger = logging.getLogger(__name__)


def main():
    logging.basicConfig(level=logging.INFO,
                        format=u'%(filename)s:%(lineno)d #%(levelname)-8s [%(asctime)s] - %(name)s - %(message)s')
    logger.info("Запускаю софт...")

    Config.IN_DATA_PATH.touch(exist_ok=True)
    content_in_data = Config.IN_DATA_PATH.read_text(encoding="utf-8")
    if (not content_in_data) or (not content_in_data.strip()):
        logger.info(f"Файл {Config.IN_DATA_PATH.name} пуст! Программа завершает свою работу...")
        return

    Config.PROXIES_PATH.touch(exist_ok=True)
    content_proxies = Config.PROXIES_PATH.read_text(encoding="utf-8")
    if (not content_proxies) or (not content_proxies.strip()):
        logger.info(f"Файл {Config.PROXIES_PATH.name} пуст! Программа завершает свою работу...")
        return

    in_data = content_in_data.split("\n")

    proxies_list: List[Proxy] = []
    for proxy in content_proxies.split("\n"):
        char_count = proxy.count(":")
        if char_count not in [1, 3]:
            logger.warning(f"Неверный формат прокси: {proxy}! Пропускаю его.")
            continue

        if char_count == 1:
            host, port = proxy.split(":")
            login, password = None, None

        else:
            login, password, host, port = proxy.split(":")

        proxy = Proxy(host=host, port=port, username=login, password=password)
        proxy.create_proxy_extension()
        proxies_list.append(proxy)

    if len(proxies_list) < Config.PROCESSES_COUNT:
        logger.error("Не хватает прокси на все процессы! Завершаю работу...")
        return

    values_per_process = math.ceil(len(in_data) / Config.PROCESSES_COUNT)
    queues_list = [Queue() for _ in range(Config.PROCESSES_COUNT)]
    last_index = 0
    for queue in queues_list:
        Process(target=Parser, args=(queue, in_data[last_index:last_index + values_per_process])).start()
        last_index += values_per_process

    occupied_proxies: Dict[int, Queue] = {}
    while True:
        for queue in queues_list:
            try:
                msg = queue.get_nowait()
                if msg["type"] == "get_new_proxy":
                    new_proxy: Optional[Proxy] = None
                    while new_proxy is None:
                        for proxy in proxies_list:
                            if proxies_list.index(proxy) not in occupied_proxies:
                                new_proxy = proxy
                                break

                    occupied_proxies[proxies_list.index(new_proxy)] = queue
                    queue.put(new_proxy.model_dump())
                    time.sleep(2)

                    occupied_values = list(occupied_proxies.values())
                    if queue in occupied_values:
                        proxy_index = occupied_values.index(queue)
                        occupied_proxies.pop(list(occupied_proxies.keys())[proxy_index])

            except Empty:
                continue

        time.sleep(0.5)


if __name__ == "__main__":
    main()
