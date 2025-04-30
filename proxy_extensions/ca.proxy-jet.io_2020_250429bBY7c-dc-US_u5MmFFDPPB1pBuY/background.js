
            chrome.runtime.onInstalled.addListener(() => {
              chrome.proxy.settings.set(
                { value: {
                    mode: "fixed_servers",
                    rules: {
                      singleProxy: {
                        scheme: "https",
                        host: "ca.proxy-jet.io",
                        port: parseInt(2020)
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
                    username: "250429bBY7c-dc-US",
                    password: "u5MmFFDPPB1pBuY"
                  }
                });
              },
              {urls: ["<all_urls>"]},
              ["asyncBlocking"]
            );
            