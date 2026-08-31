# Selenium For BOX

**Downloads the weekly APPS FOB List from Nike's Box for all four companies, merges them into one workbook, and archives the originals.**

<p>
  <img alt="Python 3" src="https://img.shields.io/badge/Python-3-3776AB?logo=python&logoColor=white">
  <img alt="Selenium" src="https://img.shields.io/badge/Selenium-Chrome%20automation-43B02A?logo=selenium&logoColor=white">
  <img alt="Chrome DevTools Protocol" src="https://img.shields.io/badge/Chrome-CDP%20download%20routing-4285F4?logo=googlechrome&logoColor=white">
  <img alt="pandas" src="https://img.shields.io/badge/pandas-concat%20%2B%20openpyxl-150458?logo=pandas&logoColor=white">
  <img alt="Feeds dbo.PPS" src="https://img.shields.io/badge/feeds-dbo.PPS-CC2927">
  <img alt="Status: internal deployment" src="https://img.shields.io/badge/status-internal%20deployment-success">
</p>

Used at **Hi-Tech Apparel**. Four companies — **HIC, HIT, HSN, HTV** — each publish a weekly FOB
list to Nike's Box. This logs in once, fetches all four, stacks them into a single `combined.xlsx`,
and moves the originals into a dated archive folder. The result feeds **`dbo.PPS`** in the
PPS,ACS,WISDOM database.

```
Box (4 company folders)  →  Download\COMPANY_<date>\  →  combined.xlsx  +  dated archive
```

---

## The problem it solves

The weekly FOB list is not one file — it is four, each buried in its own company folder, inside an
*Apparel* subfolder, and you have to sort by *Updated* to find the newest one. Fetching them by hand
is four rounds of clicking, and then the four sheets still have to be pasted into one before anything
downstream can read them.

Two details make this reliable rather than fiddly:

- **Each company's download is routed to its own folder** — Chrome preferences can't be changed
  mid-session, so the download directory is re-pointed at runtime through the **Chrome DevTools
  Protocol** (`Page.setDownloadBehavior`). One login, four destinations.
- **The archive can't eat its own output.** The source list is captured *before* `combined.xlsx` is
  written, so the merged file is never swept into the dated folder with the originals.

---

## The pipeline

| Stage | Script | What it does |
|---|---|---|
| 1. Download | [`main.py`](main.py) | Logs in to Box, then per company: create `Download\<COMPANY>_<date>`, open the company folder → *Apparel*, sort by **UPDATED**, right-click the week's file → Download |
| 2. Combine & archive | [`CombineFile.py`](CombineFile.py) | Reads every `*.xlsx` with pandas, stacks them with `concat`, writes `combined.xlsx`, then moves the originals into a folder named with today's date |
| Orchestrator | [`FlowPPS.py`](FlowPPS.py) | Runs the scripts listed in `BOX-FLOW_SCRIPTS` in order, counts success/failure, and appends a summary block to `flow_Log.txt` on the Desktop |

Each stage also runs on its own.

---

## Running it

```bash
pip install selenium webdriver-manager python-dotenv pandas openpyxl
# create .env  (Box login, the Download path, the script list — see the guide)
python FlowPPS.py
```

> ⚠️ **The week's date is hardcoded.** The folder row is matched on a date like `"Jul 3"` and the
> filename on `"7_3_2026"`, so both need updating for each new weekly drop. The guide says exactly
> where.

**Needs:** Chrome (ChromeDriver is fetched automatically by `webdriver-manager`), access to Nike's
Box, and a `.env` file — nothing sensitive is hardcoded.

---

## Output

```
Download\
├── combined.xlsx                     ← merged result of all four files
└── 2026-07-10\                       ← today-dated archive
    ├── HIC_APPSFOBList_..._7_3_2026.xlsx
    ├── HIT_APPSFOBList_..._7_3_2026.xlsx
    ├── HSN_APPSFOBList_..._7_3_2026.xlsx
    └── HTV_APPSFOBList_..._7_3_2026.xlsx
```

---

## Documentation

**[docs/DEVELOPER-GUIDE.md](docs/DEVELOPER-GUIDE.md)** — the full guide: every method of
`NikeBOXAutomator`, how the two stages find their files, the complete `.env` reference, the log
format, and the path-alignment check to watch between the two stages.

---

<sub>Internal tool for HI-TECH APPAREL · `.env`, the `Download/` folder, every spreadsheet and the
flow log are excluded by `.gitignore` — no credentials or business data are in this repo.</sub>
