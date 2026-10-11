# How to run DreamPath AI (step by step)

This guide takes you from an empty computer to a running website. Follow the steps in order. Every command can be copied exactly as written.

**Time needed:** about 10 minutes the first time, 10 seconds after that.

---

## Part 1. One-time setup

### Step 1. Install Python

1. Go to https://www.python.org/downloads/ and download Python 3.10 or newer.
2. Run the installer.
   - **Windows:** on the first screen, tick **"Add python.exe to PATH"** before clicking Install. This is the most common thing people miss.
   - **macOS / Linux:** the defaults are fine (Linux usually has Python already).
3. Check it worked. Open a terminal (steps below) and type:

   ```
   python --version
   ```

   You should see `Python 3.10` or higher. On macOS and Linux, if that says "command not found", use `python3 --version` and use `python3` wherever this guide says `python`.

### Step 2. Install VS Code

1. Download from https://code.visualstudio.com and install it.
2. Open VS Code, click the **Extensions** icon on the left (four squares), search for **Python** (by Microsoft), and click **Install**.

### Step 3. Open the project

1. Unzip `dreampath-ai.zip`. You get a folder called `dreampath-ai`.
2. In VS Code choose **File, then Open Folder**, and select the `dreampath-ai` folder.
3. You should see files like `app.py`, `README.md` and a `dreampath` folder in the left sidebar. If you only see one more folder inside, you opened the wrong level. Open the inner `dreampath-ai` folder instead.

### Step 4. Open the terminal inside VS Code

Press **Ctrl + `** (the key above Tab) or choose **Terminal, then New Terminal**. A panel opens at the bottom. All commands below go in this terminal.

---

## Part 2. Start the website

Choose **Option A** (fastest) or **Option B** (manual, so you see what happens).

### Option A. One command

- **Windows:** type `run.bat` and press Enter.
  If PowerShell says it cannot run it, type `.\run.bat` instead.
- **macOS / Linux:** type `bash run.sh` and press Enter.

The script creates the virtual environment, installs Flask, creates your `.env` file and starts the server. When you see `Running on http://127.0.0.1:5000`, go to **Part 3**.

### Option B. Manual steps

**1. Create a virtual environment** (a private folder for this project's packages)

Windows:
```
python -m venv .venv
```
macOS / Linux:
```
python3 -m venv .venv
```

**2. Activate it**

Windows (PowerShell):
```
.venv\Scripts\Activate.ps1
```
If you get "running scripts is disabled", run this once and try again:
```
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
```
Windows (Command Prompt): `.venv\Scripts\activate.bat`

macOS / Linux:
```
source .venv/bin/activate
```

You will see `(.venv)` at the start of the terminal line. That means it worked.

**3. Install the requirement** (only Flask is needed)
```
pip install -r requirements.txt
```

**4. Create your settings file**

Windows: `copy .env.example .env`
macOS / Linux: `cp .env.example .env`

The defaults work as they are. You do not need to edit anything.

**5. Start the app**
```
flask --app app run --debug
```

You can also press **F5** in VS Code. If it asks you to pick a Python interpreter, choose the one that says `.venv`.

---

## Part 3. Use the website

1. Open your browser and go to **http://127.0.0.1:5000**
2. You will see the landing page. Try the interactive Dream Meter on the right.
3. Click a stream card (for example Computer Science) to preview its full curriculum.
4. Click **Start this path free**, create an account, and you will land on setup with that stream already selected.
5. Choose your **target package** with the slider and your **study pace**, then click **Build my roadmap**.
6. You arrive on **My learning**. From here you can:
   - open **Curriculum**, tick lessons as you finish them, and watch the Dream Meter and your finish date update
   - search lessons using the box in the top bar
   - ask the **AI Mentor** what to do next
   - click **Analyse my gaps** on the dashboard
7. Click your initials (top right) for **Account settings** and **Log out**.

To stop the server, click in the terminal and press **Ctrl + C**.

### Starting again next time

Open the folder in VS Code, open the terminal, and either run `run.bat` / `bash run.sh`, or activate the environment (Part 2, Option B, step 2) and run `flask --app app run --debug`. Your accounts and progress are kept in `instance/dreampath.db`.

---

## Part 4. Optional extras

### Create a faculty account (to verify and edit lessons)

Open a **second** terminal (click the `+` in the terminal panel), activate the environment again (Option B, step 2), then run:

```
flask --app app create-faculty
```

Enter a name, an email and a password (8+ characters with a letter and a number). Then log in at `/login` with those details. Faculty land on the **Faculty console**, where they can verify, add, edit and delete lessons and replace a topic search with a specific video link.

### Turn on the real AI mentor

The app works fully without this, using built-in rules. To use an AI model instead:

1. Open the `.env` file in VS Code.
2. Put your key after `ANTHROPIC_API_KEY=` (no spaces or quotes).
3. Stop the server (Ctrl + C) and start it again.

The mentor page shows whether it is answering with the AI model or with rules.

### Reset someone's password

There is no email service, so passwords are reset from the terminal (this also clears a login lockout):

```
flask --app app reset-password
```

### Run the automatic tests

```
python -m unittest discover -s tests -v
```

You should see `OK` at the end. There are 66 tests.

### Start from scratch

Stop the server, delete the `instance` folder, and start again. A fresh database with all streams and lessons is created automatically.

---

## Part 5. Troubleshooting

| What you see | What to do |
| --- | --- |
| `python is not recognized` (Windows) | Python was installed without "Add to PATH". Re-run the installer, choose **Modify**, and tick the PATH option. Then reopen VS Code. |
| `command not found: python` (macOS / Linux) | Use `python3` instead of `python`. |
| `running scripts is disabled` | Run `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass`, then activate again. |
| `No module named flask` | The environment is not active, or step 3 was skipped. Activate it (look for `(.venv)`) and run `pip install -r requirements.txt`. |
| `Address already in use` | Another program uses port 5000. Run `flask --app app run --debug --port 5001` and open http://127.0.0.1:5001 |
| Page looks unstyled or buttons do nothing | Hard refresh with **Ctrl + Shift + R**. Make sure you opened the site through the address above, not by double-clicking an HTML file. |
| "Your session expired" message | The page was open for a long time. Refresh it and try again. |
| "Too many failed attempts" at login | Wait 15 minutes, or run `flask --app app reset-password` to unlock the account. |
| VS Code shows a yellow warning on `import flask` | Press **Ctrl + Shift + P**, type **Python: Select Interpreter**, and choose the one inside `.venv`. |
| Want to see errors in detail | Read the terminal where the server is running. Debug mode prints the full error. |

---

## Part 6. What each file does

```
dreampath-ai/
├── app.py                  Starts the app (entry point)
├── run.bat / run.sh        One-command start for Windows / macOS+Linux
├── requirements.txt        Python packages needed (just Flask)
├── .env.example            Settings template. Copy it to .env
├── HOW_TO_RUN.md           This guide
├── README.md               Project overview, features, security notes
├── .gitignore              Keeps .env and the database out of GitHub
├── .vscode/                One-click debug (F5) and test settings for VS Code
├── .github/workflows/      Runs the tests automatically on GitHub
│
├── dreampath/              The application
│   ├── __init__.py         Builds the app, error pages, template helpers
│   ├── config.py           Reads settings from .env and the environment
│   ├── db.py               Database connection, setup, command-line tools
│   ├── schema.sql          Database tables
│   ├── seed.py             The 5 streams and their lessons
│   ├── catalog.py          Lesson counts and curriculum queries
│   ├── meter.py            Dream Meter, tiers, finish-date and streak maths
│   ├── ai.py               AI mentor, gap analysis, stream suggestion (+ fallback rules)
│   ├── security.py         CSRF, security headers, rate limiting, validation
│   ├── icons.py            Inline SVG icons used in the pages
│   ├── routes_pages.py     Page URLs (/, /dashboard, /roadmap ...)
│   ├── routes_auth.py      Register, log in, log out, account
│   ├── routes_api.py       JSON API the pages call (/api/...)
│   ├── templates/          HTML pages (one file per page, plus base.html)
│   └── static/
│       ├── css/app.css     All styling (light and dark themes)
│       ├── img/favicon.svg Site icon
│       └── js/
│           ├── core.js             Shared helpers (API calls, menus, toasts)
│           ├── page-landing.js     Landing page Dream Meter demo
│           ├── page-auth.js        Login / register form helpers
│           ├── page-setup.js       Stream, package and pace picker
│           ├── page-dashboard.js   My learning dashboard
│           ├── page-roadmap.js     Curriculum page
│           ├── page-mentor.js      AI mentor chat
│           └── page-faculty.js     Faculty console
│
├── tests/test_app.py       66 automatic tests
└── instance/               Created on first run: your database lives here (not in Git)
```
