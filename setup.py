from setuptools import find_packages, setup

setup(
    name="ncmu",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "textual",
        "psutil",
    ],
    entry_points={
        "console_scripts": [
            "ncmu=ncmu.memory_analyzer:main",
        ],
    },
    author="Your Name",
    description="NCurses Memory Usage - A TUI memory analyzer",
    long_description="A terminal-based memory usage analyzer that shows process tree and memory consumption",
    keywords="memory, system, tui, process",
    python_requires=">=3.7",
)
