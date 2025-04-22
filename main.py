import asyncio
import logging
import os

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
    ext_path = os.path.abspath("proxy_extension")
    options.add_argument(f"--load-extension={ext_path}")

    with Chrome(options=options) as driver:
        driver.get("https://nuwber.com/address")
        driver.set_window_size(width=800, height=600)

        input("ad")

        element = driver.find_element(By.ID, "some-element")  # любой элемент

        actions = ActionChains(driver)
        actions.move_to_element_with_offset(element, 50, 30).click().perform()

        await asyncio.sleep(2000)


if __name__ == "__main__":
    asyncio.run(main())
