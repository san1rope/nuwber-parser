
            chrome.runtime.onInstalled.addListener(() => {
              chrome.proxy.settings.set(
                { value: {
                    mode: "fixed_servers",
                    rules: {
                      singleProxy: {
                        scheme: "http",
                        host: "5.161.22.114",
                        port: parseInt(14706)
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
                    username: "proxy666",
                    password: "proxy666"
                  }
                });
              },
              {urls: ["<all_urls>"]},
              ["asyncBlocking"]
            );
            