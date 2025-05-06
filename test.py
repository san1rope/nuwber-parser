import time
import os

from selenium.webdriver.common.by import By
from undetected_chromedriver import ChromeOptions, Chrome


def main():
    options = ChromeOptions()
    options.add_argument('--disable-blink-features=AutomationControlled')
    options.add_argument("--disable-background-timer-throttling")
    options.add_argument("--disable-backgrounding-occluded-windows")
    options.add_argument("--disable-renderer-backgrounding")
    ext_path = os.path.abspath(f"proxy_extensions/5.161.22.114_14706_proxy666_proxy666/")
    options.add_argument(f"--load-extension={ext_path}")

    with Chrome(options=options) as driver:
        driver.set_window_size(width=1100, height=600)
        driver.execute_cdp_cmd(
            "Page.addScriptToEvaluateOnNewDocument",
            {
                "source": """
                            Object.defineProperty(document, 'hidden', {value: false});
                            Object.defineProperty(document, 'visibilityState', {value: 'visible'});
                            document.addEventListener('visibilitychange', (e) => { e.stopImmediatePropagation(); }, true);
                        """
            }
        )
        driver.get("https://nuwber.com/")

        while True:
            try:
                driver.find_element(By.CLASS_NAME, "loading-verifying")

            except Exception:
                pass

            time.sleep(2.5)

        while True:
            time.sleep(1000)


if __name__ == "__main__":
    main()
