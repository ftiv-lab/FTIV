# FTIV (Free Text & Image Viewer)

**FTIV** is a high-performance, overlay-based text and image viewer designed for content creators, streamers, and power users. Built with Python 3.14 and PySide6.

## 🚀 Key Features

*   **Overlay Mode**: Place text and images anywhere on your screen with transparent backgrounds.
*   **Mind Map Connections**: Link text and images with customizable connector lines (Shift+Drag).
*   **Highly Customizable**: Adjust fonts, colors, opacity, and animations per window.
*   **Modern UI**: Sleek, dark-themed interface with fluent animations.
*   **Performance**: Optimized for low resource usage.

## 🛠️ System Requirements

*   **OS**: Windows 10/11 (64-bit)
*   **Runtime**: Python 3.14.2 (Recommended for Development) / Python 3.13 (Required for Release Build)

## 📦 Installation (For Developers)

1.  **Clone the repository**
    ```powershell
    git clone https://github.com/Start-to-Finish/FTIV.git
    cd FTIV
    ```

2.  **Create a Virtual Environment (Python 3.14)**
    ```powershell
    py -3.14 -m venv .venv314
    .venv314\Scripts\activate
    ```

3.  **Install Dependencies**
    ```powershell
    pip install -r requirements.txt
    ```

4.  **Run the Application**
    ```powershell
    python main.py
    ```

## 🏗️ Building for Release (EXE)

Uses **Nuitka** to compile a standalone executable.
**Note:** Building currently requires **Python 3.13** due to Nuitka compatibility.

1.  **Setup Build Environment (Python 3.13)**
    ```powershell
    py -3.13 -m venv .venv313
    .venv313\Scripts\pip install -r requirements.txt
    ```

2.  **Run Build Script**
    ```powershell
    & '.venv313\Scripts\python.exe' build_release.py
    ```

3.  **Output**
    The executable will be generated in `dist/FTIV/`.

## 🤝 Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for development guidelines and coding standards.

## 📄 License

(Proprietary / Contact Author)
