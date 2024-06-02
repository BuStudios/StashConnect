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

client = stashconnect.Client(
    email="your email", password="you password",
    encryption_password="you enc password",
)

client.users.change_status("new status")
```

## Features to be added

- [X] fix links
- [X] file functions
- [X] returnable file object
- [ ] docstrings
- [ ] account functions
- [ ] bot method

## Contributors

- All code made by [BuStudios](https://github.com/bustudios)
- Create a pull request to contribute code yourself

---

StashConnect is not affiliated with Stashcat GmbH or any of its affiliates.

<img src="https://raw.githubusercontent.com/BuStudios/StashConnect/main/assets/icon-full.png">
