# 🌐 Rolo Scaner (Rolo_IP_Dns_CH)

A simple and practical Windows application for **viewing network adapter information** and **quickly changing DNS and IP settings**, with a modern, dark-themed graphical interface.

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

- 🔍 **Scan active network adapters** on the system and list them in a dropdown
- 📋 View full information for the selected adapter:
  - **IPv4** address
  - **IPv6** address
  - **MAC** address
  - Average **Ping** (internet connectivity test)
  - **Primary and Secondary DNS**
- ✏️ **Change DNS** directly (supports both Primary and Secondary DNS)
- ✏️ **Change IP** address manually
- 🎨 Custom dark-themed GUI with rounded animated buttons and a loading animation
- 🔐 Automatic Administrator (UAC) elevation on Windows, since changing DNS/IP requires admin rights

---

## 🖼️ Screenshots

> Screenshots will be added here once available

| Main Screen | Scan Results | DNS Change |
|:---:|:---:|:---:|
| <img width="200" height="200" alt="Screenshot 2026-07-06 152836" src="https://github.com/user-attachments/assets/06d89f04-ca8b-4fa3-8325-fed839f3609c" />| *(coming soon)* | *(coming soon)* |

---

## 🖥️ Requirements

- **OS:** Windows 10 / 11 — DNS/IP changes are only supported on Windows
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
   python src/Main.py
   ```

> ⚠️ Since changing DNS/IP relies on `netsh` commands, the app automatically triggers a Windows UAC prompt on startup requesting **Administrator** access. Click **Yes** so DNS/IP changes work properly.

### Option 2: Run the executable (EXE)

> 🚧 A standalone `.exe` build will be added to the `build/` folder soon — no Python installation will be required to run it.

---

## 📖 Usage

1. Launch the application and confirm the UAC prompt if it appears.
2. Select the desired network adapter (e.g. Wi-Fi or Ethernet) from the dropdown list.
3. If your adapter isn't listed, click **REFRESH** to refresh the list.
4. Click **SCAN** to display full adapter details (IP, IPv6, MAC, Ping, DNS).
5. To change DNS:
   - Enter the primary DNS in the first field, and the secondary DNS (optional) in the second field.
   - Click **Save DNS**.
6. To change IP:
   - Enter the new IP address in the corresponding field.
   - Click **Save IP**.

---

## 🛠️ Project Structure

```
Rolo_IP_Dns_CH/
│
├── README.md                    # Project documentation (this file)
├── LICENSE                      # Project license
├── requirements.txt             # Python dependencies
├── .gitignore                   # Ignored files/folders (Python template)
│
├── src/                         # Application source code
│   └── Rolo_IP_dns_CH.py         # Main entry point (UI logic to be split out later)
│
|
|
|──assets/
    └── screenshots
```

| Section | Description |
|---|---|
| Admin Elevation | Automatic Administrator (UAC) elevation |
| Theme & Constants | Colors, fonts, and visual constants |
| Network Helper Functions | Functions to scan adapters and read/change DNS and IP |
| UI Helper Widgets | Rounded button, loading spinner, custom rounded combobox |
| Main Application Class | The main app class and screen logic |

---

## 🗺️ Roadmap

- [x] Scan network adapters
- [x] Change DNS (Primary + Secondary)
- [x] Change IP


---

## 📌 Changelog



**Current version:** `Rolo_IP_Dns_CH V1.0.0`

---

## 📄 License

See the [`LICENSE`](LICENSE) file for details.
