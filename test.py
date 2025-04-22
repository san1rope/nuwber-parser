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

    with Chrome(options=options) as driver:
        driver.get("https://nuwber.com/address")

        input("ad")

        await asyncio.sleep(1000)


async def main2():
    url = "https://nuwber.com"

    proxy = "http://138.36.94.19:59100"
    proxy_auth = BasicAuth(login="valetinles", password="f5bay87SBb")
    async with ClientSession() as session:
        async with session.get(url=url, timeout=10) as response:
            with open("index.html", "w", encoding="utf-8") as file:
                file.write(await response.text())


if __name__ == "__main__":
    asyncio.run(main2())
