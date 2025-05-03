import os
from pathlib import Path
from typing import Optional

from pydantic import BaseModel


class Proxy(BaseModel):
    host: str
    port: str
    username: Optional[str] = None
    password: Optional[str] = None
    change_address_url: Optional[str] = None

    def formulate_filename(self) -> str:
        name = f"{self.host}_{self.port}"
        if self.username is not None:
            name += f"_{self.username}_{self.password}"

        return name

    def create_proxy_extension(self):
        manifest_json = """
            {
              "manifest_version": 3,
              "name": "Proxy Extension",
              "version": "1.0",
              "permissions": [
                "proxy",
                "storage",
                "webRequest",
                "webRequestAuthProvider"
              ],
              "host_permissions": [
                "<all_urls>"
              ],
              "background": {
                "service_worker": "background.js"
              },
              "action": {
                "default_title": "Proxy Extension"
              }
            }
            """

        background_js = """
            chrome.runtime.onInstalled.addListener(() => {
              chrome.proxy.settings.set(
                { value: {
                    mode: "fixed_servers",
                    rules: {
                      singleProxy: {
                        scheme: "http",
                        host: "%s",
                        port: parseInt(%s)
                      },
                      bypassList: ["localhost"]
                    }
                  },
                  scope: "regular"
                },
                function() {}
              );
            });

            chrome.webRequest.onAuthRequired.addListener(
              function(details, callback) {
                callback({
                  authCredentials: {
                    username: "%s",
                    password: "%s"
                  }
                });
              },
              {urls: ["<all_urls>"]},
              ["asyncBlocking"]
            );
            """ % (self.host, self.port, self.username, self.password)

        manifest_path = Path(os.path.abspath("proxy_extensions/" + self.formulate_filename() + "/manifest.json"))
        background_path = Path(os.path.abspath("proxy_extensions/" + self.formulate_filename() + "/background.js"))

        manifest_path.parent.mkdir(exist_ok=True, parents=True)
        manifest_path.touch(exist_ok=True)
        manifest_path.write_text(manifest_json)

        background_path.parent.mkdir(exist_ok=True, parents=True)
        background_path.touch(exist_ok=True)
        background_path.write_text(background_js)
