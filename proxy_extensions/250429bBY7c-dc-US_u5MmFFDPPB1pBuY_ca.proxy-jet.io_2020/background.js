
            chrome.runtime.onInstalled.addListener(() => {
              chrome.proxy.settings.set(
                { value: {
                    mode: "fixed_servers",
                    rules: {
                      singleProxy: {
                        scheme: "https",
                        host: "250429bBY7c-dc-US",
                        port: parseInt(u5MmFFDPPB1pBuY)
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
                    username: "ca.proxy-jet.io",
                    password: "2020"
                  }
                });
              },
              {urls: ["<all_urls>"]},
              ["asyncBlocking"]
            );
            