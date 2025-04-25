import logging
import os
import time

from selenium.webdriver import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.support.wait import WebDriverWait
# from selenium.webdriver.chrome.webdriver import WebDriver, Options
from undetected_chromedriver import ChromeOptions, Chrome

logger = logging.getLogger(__name__)


def main():
    logging.basicConfig(level=logging.INFO,
                        format=u'%(filename)s:%(lineno)d #%(levelname)-8s [%(asctime)s] - %(name)s - %(message)s')

    options = ChromeOptions()
    ext_path = os.path.abspath("proxy_extension_test")
    options.add_argument(f"--load-extension={ext_path}")

    test_address = "1133 E 60th St  90001"
    url_address = "https://nuwber.com/search/address?addressQuery=" + "%20".join(test_address.split())
    print(f"url_address = {url_address}")

    with Chrome(options=options) as driver:
        driver.set_window_size(width=800, height=600)
        driver.get(url_address)

        time.sleep(15)

        # actions = ActionChains(driver)

        # driver.execute_script(f"""
        #     var el = document.createElement('div');
        #     el.style.position = 'absolute';
        #     el.style.left = '{265}px';
        #     el.style.top = '{100}px';
        #     el.style.width = '10px';
        #     el.style.height = '10px';
        #     el.style.background = 'red';
        #     el.style.zIndex = 9999;
        #     document.body.appendChild(el);
        # """)

        x, y = 265, 100

        actions = ActionChains(driver)
        actions.move_by_offset(5, 5).perform()
        time.sleep(0.2)
        actions.move_by_offset(10, -3).perform()
        time.sleep(0.3)
        actions.move_by_offset(20, 4).perform()
        time.sleep(0.3)
        actions.move_by_offset(x, y).click().perform()
        actions.move_by_offset(-x - 35, -6).perform()

        # actions.move_by_offset(xoffset=265, yoffset=100).perform()
        # actions.click().perform()

        time.sleep(1000)


if __name__ == "__main__":
    main()
