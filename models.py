import os
from pathlib import Path
from typing import Optional

from pydantic import BaseModel


class Proxy(BaseModel):
    host: str
    port: str
    username: Optional[str] = None
    password: Optional[str] = None

    def formulate_filename(self) -> str:
        name = f"{self.host}_{self.port}"
        if self.username is not None:
            name += f"_{self.username}_{self.password}"

        return name

    def create_proxy_extension(self):
        path = Path(os.path.abspath("proxy-extensions/" + self.formulate_filename()))
        path.touch(exist_ok=True)

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
                        host: "138.36.94.19",
                        port: 59100
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
                    username: "valetinles",
                    password: "f5bay87SBb"
                  }
                });
              },
              {urls: ["<all_urls>"]},
              ["asyncBlocking"]
            );
            """ % (self.host, self.port, self.username, self.password)

        with open(path + "/manifest.json", 'w') as m_file:
            m_file.write(manifest_json)
        with open(path + "/background.js", 'w') as b_file:
            b_file.write(background_js)
