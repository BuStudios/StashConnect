# StashConnect

StashConnect is an easy-to-use API wrapper for [stashcat](https://stashcat.com/) and [schul.cloud](https://schul.cloud).

![PyPI - Downloads](https://img.shields.io/pypi/dm/stashconnect?labelColor=345165&color=4793c9)
![PyPI - Version](https://img.shields.io/pypi/v/stashconnect?label=version&labelColor=345165&color=4793c9)
![PyPI - Status](https://img.shields.io/pypi/status/stashconnect?labelColor=345165&color=44af68)

## Installation

To install StashConnect, use pip in your shell:

```bash
pip install -U stashconnect
```

## Example Usage

```python
import stashconnect

# without proxy / cert
client = stashconnect.Client(
    email="your email", password="your password",
    encryption_password="encryption password"
)

# with proxy & cert
proxies = {
  'http': 'http://1.2.3.4:8080',
  'https': 'http://5.6.7.8:8443',
}

client = stashconnect.Client(
    email="your email", password="your password",
    encryption_password="encryption password",
    proxy = proxies, 
    cert_path = 'path/to/CA.pem'
)

# change account settings
client.account.change_status("new status")
client.account.change_password("new", "old")

# upload or download files
client.files.upload("conversation_id", "hello.png")
client.files.download("file_id")

client.messages.send("conversation_id", "hello")

# get the last 30 messages of a chat
last_messages = client.messages.get_messages("channel_id/conversation_id")
for message in last_messages:
    print(message.content)
```


## Features to be added

- [x] docstrings
- [ ] account functions
- [ ] documentation
- [ ] bot class

## Contributors

- Most code written by [BuStudios](https://github.com/bustudios)
- Create a pull request to contribute code yourself

## Disclaimer

StashConnect is not affiliated with Stashcat GmbH or any of its affiliates.

<img src="https://raw.githubusercontent.com/BuStudios/StashConnect/main/assets/icon-full.png">
