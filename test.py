import asyncio
import logging
import os

from aiohttp import ClientSession, BasicAuth
from selenium.webdriver import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.support.wait import WebDriverWait
# from selenium.webdriver.chrome.webdriver import WebDriver, Options
from undetected_chromedriver import ChromeOptions, Chrome

logger = logging.getLogger(__name__)


async def main():
    logging.basicConfig(level=logging.INFO,
                        format=u'%(filename)s:%(lineno)d #%(levelname)-8s [%(asctime)s] - %(name)s - %(message)s')

    options = ChromeOptions()
    ext_path = os.path.abspath("proxy_extension_test")
    options.add_argument(f"--load-extension={ext_path}")

    test_address = "1133 E 60th St  90001"
    url_address = "https://nuwber.com/search/address?addressQuery=" + "%20".join(test_address.split())
    print(f"url_address = {url_address}")

    with Chrome(options=options) as driver:
        driver.get(url_address)

        input("ad")

        await asyncio.sleep(1000)


async def main2():
    url = "https://habr.com/ru/companies/simbirsoft/articles/598407/"
    proxy = "http://54.38.92.93:10000"

    async with ClientSession() as session:
        async with session.get(url=url, proxy=proxy, timeout=10, ssl=False) as response:
            markup = await response.text()

    with open("index.html", "w", encoding="utf-8") as file:
        file.write(markup)


if __name__ == "__main__":
    asyncio.run(main2())
