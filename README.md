# IBM z/OS JCL Generator Studio

**Developed by Nagraj Naik**

A 100% offline, browser-based IBM z/OS Job Control Language (JCL) generator. Configure Job Cards, utility steps (IEFBR14, IEBGENER, SORT, IDCAMS, and more), DD statements, COND parameters, and IF/THEN/ELSE blocks — all through a clean web UI backed by a local Python/Flask server.

---

## Features

- 10 built-in mainframe utilities with smart defaults
- Live 80-column JCL preview with syntax highlighting
- Strict z/OS column-71 continuation validation
- Multi-step job queue builder
- Download generated `.jcl` files directly from the browser
- Edit job parameters and DD statements in the builder; source templates are not editable in the UI
- **Light & Dark mode** with preference saved across sessions
- Zero internet required — fully air-gap friendly

---

## Project Structure

```
jcl/
├── app.py                  # Flask web server & API routes
├── jcl_engine.py           # JCL generation engine & validation
├── requirements.txt        # Python dependencies
├── .gitignore
│
├── templates/
│   └── index.html          # Main UI (served by Flask)
│
├── static/
│   ├── css/
│   │   └── style.css       # Light + dark mode stylesheet
│   └── js/
│       └── app.js          # Frontend controller
│
├── jcl_templates/          # Modular JCL step templates (.jcl.tpl)
│   ├── job_card.jcl.tpl
│   ├── iefbr14.jcl.tpl
│   ├── iebgener.jcl.tpl
│   ├── idcams.jcl.tpl
│   ├── sort.jcl.tpl
│   ├── iebcopy.jcl.tpl
│   ├── ikjeft01.jcl.tpl
│   ├── iebcompr.jcl.tpl
│   ├── iebupdte.jcl.tpl
│   ├── icegener.jcl.tpl
│   └── custom_pgm.jcl.tpl
│
└── generated_jcl/          # Output directory for saved .jcl files
```

---

## Local Setup Guide

### Prerequisites

| Requirement | Minimum Version | Check Command |
|-------------|----------------|---------------|
| Python      | 3.9+           | `python --version` |
| pip         | 21+            | `pip --version` |
| Git         | any            | `git --version` |

---

### Step 1 — Clone the Repository

```bash
git clone https://github.com/nagrjnaik/JCLGenerator.git
cd JCLGenerator
```

---

### Step 2 — Create a Virtual Environment

A virtual environment isolates project dependencies from your system Python.

**macOS / Linux:**
```bash
python3 -m venv .venv
source .venv/bin/activate
```

**Windows (PowerShell):**
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

**Windows (Command Prompt):**
```cmd
python -m venv .venv
.venv\Scripts\activate.bat
```

> After activation your terminal prompt will show `(.venv)` at the start.

---

### Step 3 — Install Dependencies

```bash
pip install -r requirements.txt
```

This installs Flask and all required packages. The app has **no other external dependencies** — no Node.js, no npm, no build step.

---

### Step 4 — Run the Server

```bash
python app.py
```

Expected output:
```
Starting JCL Generator Web App (Flask) at http://127.0.0.1:5000
 * Serving Flask app 'app'
 * Running on http://127.0.0.1:5000
```

---

### Step 5 — Open the App

Open your browser and navigate to:

```
http://127.0.0.1:5000
```

The app loads instantly — no login, no internet, no API keys.

---

### Optional: Change Host / Port

```bash
# Custom port
PORT=8080 python app.py

# Listen on all network interfaces (accessible from other machines on LAN)
HOST=0.0.0.0 PORT=5000 python app.py
```

**Windows PowerShell:**
```powershell
$env:PORT = "8080"; python app.py
$env:HOST = "0.0.0.0"; $env:PORT = "5000"; python app.py
```

---

## Stopping the Server

Press `Ctrl + C` in the terminal where the server is running.

---

## Deactivating the Virtual Environment

```bash
deactivate
```

---

## Generating JCL — Quick Start

1. **Job Card** — Set Job Name, Class, MSGCLASS, Accounting Info
2. **Select Utility** — Click one of the 10 radio buttons (e.g., IEBGENER)
3. **DD Statements** — Adjust DSN, DISP, SPACE, DCB as needed
4. **SYSIN** — Enter control cards or select a snippet
5. **Preview** — Live JCL renders in the right panel automatically
6. **Download** — Click "Download .JCL" to save the generated job to your computer

---

## Supported Utilities

| Utility    | Purpose |
|------------|---------|
| IEFBR14    | Allocate / Delete datasets (no-op) |
| IEBGENER   | Sequential file copy / print |
| IDCAMS     | VSAM cluster management, GDG, LISTCAT |
| SORT       | DFSORT — sort, merge, filter, reformat |
| IEBCOPY    | PDS/PDSE copy & in-place compress |
| IKJEFT01   | TSO batch / DB2 COBOL program runner |
| IEBCOMPR   | Compare two sequential or PDS datasets |
| IEBUPDTE   | Create / update PDS members |
| ICEGENER   | High-speed DFSORT drop-in for IEBGENER |
| CUSTOM PGM | Execute any user COBOL / Assembler program |

---

## Troubleshooting

| Problem | Solution |
|---------|----------|
| `ModuleNotFoundError: No module named 'flask'` | Ensure the venv is activated and run `pip install -r requirements.txt` |
| Port 5000 already in use | Set `PORT=8080` or another free port |
| `TemplateNotFound: index.html` | Ensure `templates/index.html` exists (do not move it to root) |
| CSS / JS not loading (404) | Ensure `static/css/style.css` and `static/js/app.js` exist |
| PowerShell Activate.ps1 blocked | Run `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned` then retry |

---


*Developed by **Nagraj Naik***
