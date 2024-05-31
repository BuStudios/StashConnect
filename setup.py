from setuptools import setup, find_packages

VERSION = "0.7.6"
DESCRIPTION = "An API wrapper for stashcat and schul.cloud."

setup(
    name="stashconnect",
    version=VERSION,
    author="BuStudios",
    author_email="support@bustudios.org",
    description=DESCRIPTION,
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/BuStudios/StashConnect",
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Intended Audience :: Developers",
        "Development Status :: 4 - Beta",
    ],
    keywords=[
        "stashconnect",
        "stashcat api",
        "stashcat python",
        "schul.cloud api",
        "schul.cloud python",
        "stashcat bot",
        "schul.cloud bot",
    ],
    install_requires=[
        "requests",
        "pycryptodome",
        "python-socketio",
        "Pillow",
        "websocket-client",
    ],
    project_urls={
        "Bug Tracker": "https://github.com/BuStudios/StashConnect/issues",
        "Documentation": "https://github.com/BuStudios/StashConnect/wiki",
        "Source Code": "https://github.com/BuStudios/StashConnect",
    },
    python_requires=">=3.10",
)
