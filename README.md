# Selenium For BOX — Nike BOX File Downloader & Combine Flow

An automated pipeline that (1) downloads the weekly **APPS FOB List** Excel files from Nike's Box (app.box.com) for four companies — **HIC, HIT, HSN, HTV** — then (2) combines them into a single Excel file and archives the originals into a dated folder. A flow runner orchestrates the whole sequence and writes a summary log.

## Pipeline Overview

| Stage | Script | What it does |
|---|---|---|
| 1. Download | `main.py` | Logs in to Box and downloads the four companies' weekly Excel files. |
| 2. Combine & archive | `CombineFile.py` | Appends the four Excel files into one `combined.xlsx`, then moves the originals into a folder named with today's date. |
| Orchestrator | *flow runner* (e.g. `run_flow.py`) | Runs the scripts listed in `BOX-FLOW_SCRIPTS` in order, counts success/failure, and appends a summary block to a log file. |

The scripts can be run individually, or all together through the flow runner. Paths and the script list are driven by a `.env` file (see [Configuration](#configuration-env)).

---

## Stage 1 — `main.py` (Download)

### How It Works (Logic Overview)

1. **Setup** — Launches Chrome (via `webdriver-manager`, so no manual chromedriver install) and reads Box credentials from the `.env` file.
2. **Login** — Signs in to Box once with email + password.
3. **Per-company loop** — For each company (`HIC`, `HIT`, `HSN`, `HTV`):
   1. Creates a local folder `Download\<COMPANY>_<YYYY-MM-DD>` and redirects Chrome's download directory to it using the Chrome DevTools Protocol (CDP), since Chrome prefs cannot be changed mid-session.
   2. Navigates back to the Box root folder (`/folder/0`).
   3. Opens the company folder whose row shows an update date of **"Jul 3"**.
   4. Opens the **Apparel** subfolder inside it.
   5. Sorts by the **UPDATED** column so the newest file surfaces.
   6. Right-clicks the row containing **"7_3_2026"** in its filename and chooses **Download** from the context menu.
4. **Teardown** — On error or completion, waits for the user to press Enter before closing the browser (so results/errors can be inspected).

Element targeting relies on XPath text matching against Box's folder-list rows (`div[@role='row']`), combined with `WebDriverWait` (20-second timeout) and fixed `time.sleep()` pauses for page loads.

> **Note:** The date strings `"Jul 3"` (folder row match) and `"7_3_2026"` (filename match) are hardcoded and must be updated for each new weekly file drop.

### Function Reference

All methods belong to the `NikeBOXAutomator` class in `main.py`.

| Method | Description |
|---|---|
| `__init__` | Loads `BOX_EMAIL` / `BOX_PASSWORD` from `.env`, sets the base download path, configures Chrome options (maximized, silent downloads), and starts the driver with a 20s explicit wait. |
| `login()` | Opens `app.box.com/folder/0`, types the email, clicks **Next**, types the password, and clicks **Log in**. |
| `set_download_folder(company)` | Creates `Download\<company>_<today>` and uses the CDP command `Page.setDownloadBehavior` to route all subsequent Chrome downloads into that folder. |
| `go_to_root()` | Navigates the browser back to the Box root folder so each company iteration starts from the same place. |
| `open_company_folder(company)` | Finds the folder row containing both the company code and "Jul 3", then clicks the folder-name link inside that specific row. |
| `open_download_folder()` | Clicks the row containing **Apparel** to enter the Apparel subfolder. |
| `click_updated_sort()` | Clicks the **UPDATED** column header to sort files by their last-updated date. |
| `download_file()` | Locates the row whose filename contains "7_3_2026", right-clicks it, and clicks **Download** in the context menu. |
| `run()` | Orchestrates the whole flow: login once, then run the per-company sequence for HIC, HIT, HSN, and HTV. Catches errors and keeps the browser open until Enter is pressed. |

---

## Stage 2 — `CombineFile.py` (Combine & Archive)

### How It Works (Logic Overview)

1. **Collect sources** — Scans `BOX_FOLDER_PATH` (the `Download` folder) for `*.xlsx` files, excluding any existing `combined.xlsx` left over from a previous run. This list is captured **before** the combined file is written, so the output never gets swept into the archive step.
2. **Append** — Reads each file into a pandas DataFrame and stacks them with `pd.concat(..., ignore_index=True)`. Because the files share the same columns, headers line up automatically.
3. **Save** — Writes the merged result to `Download\combined.xlsx`.
4. **Archive** — Creates a folder named with today's date (e.g. `2026-07-10`) inside `Download`, then moves the original source files into it.

Progress is printed to the console at each step (files found, rows read per file, total combined rows, save location, and each move).

### Requirements

```bash
pip install pandas openpyxl
```

> **Path alignment to verify:** `main.py` downloads each company's file into its own subfolder (`Download\<COMPANY>_<date>\...`), while `CombineFile.py` scans the top level of `Download` for `*.xlsx`. Make sure the two agree — either have `main.py` download directly into `Download`, or update `CombineFile.py` to search recursively (`glob("**/*.xlsx", recursive=True)`) so it can find files inside the company subfolders.

---

## Orchestrator — Flow Runner

Runs the scripts named in `BOX-FLOW_SCRIPTS` (currently `main.py` then `CombineFile.py`) one after another using `subprocess.run`, tracking how many succeeded or failed. When finished it appends a summary block to the log file on the Desktop:

```
=============================================
Process: <BOX-FLOW_RUN_ID>
Start Time: 2026-07-10 14:32:01
End Time:   2026-07-10 14:38:44
Status: SUCCESS
Success Count: 2
Failed Count: 0
=============================================
```

`BOX_SSIS_PATH` is loaded for a potential downstream SSIS (`.dtsx`) execution step, but the runner does not execute it yet.

---

## Configuration (`.env`)

Create a `.env` file in the project folder (never commit it).

**Box login (used by `main.py`):**
```
BOX_EMAIL=your.email@example.com
BOX_PASSWORD=your_password
```

**Flow paths and script list:**
```
BOX-FLOW_BASE_PATH=D:\path\to\Selenium For BOX
BOX_FOLDER_PATH=D:\path\to\Selenium For BOX\Download
BOX_SSIS_PATH=D:\path\to\Package.dtsx
BOX-FLOW_SCRIPTS="main.py, CombineFile.py"
```

| Key | Used by | Purpose |
|---|---|---|
| `BOX_EMAIL` / `BOX_PASSWORD` | `main.py` | Box sign-in credentials. |
| `BOX-FLOW_BASE_PATH` | flow runner | Folder the runner joins with each script name to locate it. |
| `BOX_FOLDER_PATH` | `CombineFile.py` | The `Download` folder to combine from and archive into. |
| `BOX_SSIS_PATH` | flow runner | Path to the SSIS `.dtsx` package (loaded for a future step). |
| `BOX-FLOW_SCRIPTS` | flow runner | Comma-separated list of scripts to run, in order. |
| `BOX-FLOW_RUN_ID` *(optional)* | flow runner | Label written into the log summary. Defaults to `BOX-FLOW_DEFAULT`. |
| `BOX-FLOW_LOG_FILE` *(optional)* | flow runner | Log filename. Defaults to `flow_Log.txt`. |
| `DESKTOP_PATH` *(optional)* | flow runner | Folder for the log file. Defaults to the current user's Desktop. |

> **Tip:** Avoid a leading space after `=` in path values (e.g. `BOX_SSIS_PATH= D:\...`), as the space becomes part of the path. The flow runner defensively `.strip()`s this value.

---

## Setup & Usage

1. Install dependencies:
   ```bash
   pip install selenium webdriver-manager python-dotenv pandas openpyxl
   ```
2. Create the `.env` file as described above.
3. Run the full flow via the orchestrator:
   ```bash
   python run_flow.py
   ```
   …or run either stage on its own:
   ```bash
   python main.py
   python CombineFile.py
   ```

## Output

```
Download\
├── combined.xlsx                     ← merged result of all four files
├── HIC_APPSFOBList_..._7_3_2026.xlsx ┐
├── HIT_APPSFOBList_..._7_3_2026.xlsx │ downloaded originals
├── HSN_APPSFOBList_..._7_3_2026.xlsx │ (moved into the dated folder
├── HTV_APPSFOBList_..._7_3_2026.xlsx ┘  by CombineFile.py)
└── 2026-07-10\                       ← today-dated archive folder
    ├── HIC_APPSFOBList_..._7_3_2026.xlsx
    ├── HIT_APPSFOBList_..._7_3_2026.xlsx
    ├── HSN_APPSFOBList_..._7_3_2026.xlsx
    └── HTV_APPSFOBList_..._7_3_2026.xlsx
```

A summary block is appended to `flow_Log.txt` on the Desktop after each flow run.