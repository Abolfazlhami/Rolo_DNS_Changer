# 🌐 Rolo Scanner (Rolo_IP_Dns_CH)

A simple and practical Windows application for **quickly changing DNS settings** and **testing your internet connection with a ping**, with a modern, dark-themed graphical interface.

---

## 📖 Table of Contents

- [Features](#-features)
- [Screenshots](#️-screenshots)
- [Requirements](#️-requirements)
- [Installation & Run](#️-installation--run)
- [Usage](#-usage)
- [Project Structure](#️-project-structure)
- [Roadmap](#️-roadmap)
- [Changelog](#-changelog)
- [License](#-license)

---

## ✨ Features

- 🌐 **Automatic adapter detection** — no need to pick an adapter manually, the app finds the active network adapter itself
- ✏️ **Change DNS** directly (supports both Primary and Secondary DNS)
- 📡 **Ping test** — check your internet connectivity with a single click
- 🎨 Custom dark-themed GUI with rounded animated buttons
- 🔐 Automatic Administrator (UAC) elevation on Windows, since changing DNS requires admin rights

---

## 🖼️ Screenshots

> Screenshots will be added here once available

| Main Screen |
|:---:|
| *(coming soon)* |

---

## 🖥️ Requirements

- **OS:** Windows 10 / 11 — DNS changes are only supported on Windows
- **Python:** 3.8 or higher
- **Privileges:** Administrator access (required for `netsh` commands)
- **Python packages:** see [`requirements.txt`](requirements.txt)
  ```
  psutil>=5.9.0
  ```
  (`tkinter` is part of Python's standard library and comes pre-installed on Windows)

---

## ⚙️ Installation & Run

### Option 1: Run from Python source

1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd Rolo_IP_Dns_CH
   ```

2. (Optional but recommended) create a virtual environment:
   ```bash
   python -m venv venv
   venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Run the application:
   ```bash
   python src/main.py
   ```

> ⚠️ Since changing DNS relies on `netsh` commands, the app automatically triggers a Windows UAC prompt on startup requesting **Administrator** access. Click **Yes** so DNS changes work properly.

### Option 2: Run the standalone executable (EXE)

You don't need Python or any dependencies installed to run **Rolo Scanner**.

1. Go to the [Releases](https://github.com/YOUR_USERNAME/YOUR_REPO_NAME/releases) page.
2. Download the latest `.exe` file.
3. Double-click to run the application.

> ⚠️ **Note:** Since the application executes `netsh` commands to change your network configuration, Windows will show a UAC prompt asking for **Administrator** permissions. Click **Yes** to allow the program to function properly.

---

## 📖 Usage

1. Launch the application and confirm the UAC prompt if it appears.
2. The app automatically detects your active network adapter and loads its current DNS values into the fields.
3. To change DNS:
   - Enter the primary DNS in the first field, and the secondary DNS (optional) in the second field.
   - Click **SET**.
4. To test your connection:
   - Click **PING** — the result (average response time, or `timeout`) appears at the bottom of the window.

---

## 🛠️ Project Structure

The application code has been split into separate modules by responsibility, instead of one large file:

```
Rolo_IP_Dns_CH/
│
├── README.md                    # Project documentation (this file)
├── LICENSE                      # Project license
├── requirements.txt             # Python dependencies
├── .gitignore                   # Ignored files/folders (Python template)
│
├── src/                         # Application source code
│   ├── main.py                  # Entry point — run this file to start the app
│   ├── config.py                # Colors, fonts, and visual/general constants
│   ├── admin_utils.py           # Automatic Administrator (UAC) elevation
│   ├── network_utils.py         # Adapter detection, DNS read/change, ping
│   ├── ui_widgets.py            # Custom widgets: rounded button, rounded combobox
│   └── app.py                   # Main application class (WifiApp) and screen logic
│
└── assets/
    └── screenshots/
```

| File | Description |
|---|---|
| `main.py` | Entry point of the app; calls `ensure_admin()` then launches `WifiApp` |
| `config.py` | Colors, fonts, and other visual/general constants |
| `admin_utils.py` | Automatic Administrator (UAC) elevation |
| `network_utils.py` | Functions to auto-detect the active adapter, read/change DNS, and ping |
| `ui_widgets.py` | Rounded button and custom rounded combobox |
| `app.py` | The main app class (`WifiApp`) — DNS fields, SET button, PING button and status logic |

> ℹ️ All files inside `src/` depend on each other via `import`, so they must stay together in the same folder.

---

## 🗺️ Roadmap

- [x] Auto-detect active network adapter
- [x] Change DNS (Primary + Secondary)
- [x] Ping test
- [x] Split code into separate modules
- [ ] Custom ping target (currently fixed to `8.8.8.8`)

---

## 📌 Changelog

### V1.1.0
- Removed manual adapter selection, IP scanning, and IP editing to simplify the app
- App now auto-detects the active network adapter
- Added a dedicated **PING** button for a quick connectivity test
- Refined the dark color palette for better contrast and readability

### V1.0.0
- Initial release: adapter scan, DNS/IP view and edit, admin elevation

---

**Current version:** `Rolo_IP_Dns_CH V1.1.0`

---

## 📄 License

See the [`LICENSE`](LICENSE) file for details.