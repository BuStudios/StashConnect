# StashConnect

StashConnect is a easy-to-use API wrapper for [stashcat](https://stashcat.com/) and [schul.cloud](https://schul.cloud).

![PyPI - Downloads](https://img.shields.io/pypi/dm/stashconnect?labelColor=345165&color=77b8e5)
![PyPI - Version](https://img.shields.io/pypi/v/stashconnect?label=version&labelColor=345165&color=77b8e5)
![PyPI - Status](https://img.shields.io/pypi/status/stashconnect?labelColor=345165&color=77b8e5)

## Installation

To install StashConnect, use pip in your shell:

```bash
pip install -U stashconnect
```

## Example Usage

```python
import stashconnect

client = stashconnect.Client(
    email="your email", password="you password",
    encryption_password="you enc password",
)

client.users.change_status("new status")
```

## Features to be added

- [x] fix links
- [ ] returnable file object
- [ ] bot file for easy bot setup

## Contributors

- All code made by [BuStudios](https://github.com/bustudios)
- Create a pull request to contribute code yourself

---

StashConnect is not affiliated with Stashcat GmbH or any of its affiliates.

<img src="https://raw.githubusercontent.com/BuStudios/StashConnect/main/assets/icon-full.png">
