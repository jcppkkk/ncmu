# NCMU (NCurses Memory Usage)

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

A modern terminal-based memory usage analyzer that displays process trees and memory consumption in a beautiful TUI interface. Built with [Textual](https://textual.textualize.io/).

## ✨ Features

- 🌳 Interactive process tree visualization
- 📊 Real-time memory usage monitoring
- 🎨 Beautiful terminal UI with modern styling
- 🚀 Fast and lightweight
- 🔍 Deep process inspection
- ⌨️ Vim-style keyboard navigation

## 🚀 Installation

### Using pip

```bash
pip install ncmu
```

### Using uv (recommended)

```bash
uv pip install ncmu
```

### From source

```bash
git clone https://github.com/yourusername/ncmu.git
cd ncmu
uv pip install -e .
```

## 🎮 Usage

Simply run:

```bash
ncmu
```

### Keyboard Controls

- `↑`/`↓`: Navigate through processes
- `Enter`: Expand/collapse process tree
- `Esc`: Go back to parent process
- `q`: Quit application

## 🛠️ Development

Requirements:
- Python 3.11+
- uv (recommended) or pip

Setting up development environment:

```bash
# Clone the repository
git clone https://github.com/yourusername/ncmu.git
cd ncmu

# Create and activate virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
uv pip install -e .
```

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request. For major changes, please open an issue first to discuss what you would like to change.

1. Fork the Project
2. Create your Feature Branch (`git checkout -b feature/AmazingFeature`)
3. Commit your Changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the Branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- [Textual](https://textual.textualize.io/) for the amazing TUI framework
- [psutil](https://github.com/giampaolo/psutil) for system and process utilities

## 📊 Project Status

Active development - Bug reports and feature requests are welcome!

## 📫 Contact

Project Link: [https://github.com/yourusername/ncmu](https://github.com/yourusername/ncmu)
