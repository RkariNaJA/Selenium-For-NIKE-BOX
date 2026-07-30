import pandas as pd
import glob
import os
import shutil
from datetime import date

folder = os.getenv("BOX_FOLDER_PATH") or os.path.join(os.path.dirname(os.path.abspath(__file__)), "Download")

print("Starting combine job...")
print("Folder:", folder)

# 1. Capture the source files FIRST (before the combined file exists)
source_files = [
    f for f in glob.glob(os.path.join(folder, "*.xlsx"))
    if "combined" not in os.path.basename(f).lower()
]
print(f"Found {len(source_files)} file(s) to combine:")
for f in source_files:
    print("   -", os.path.basename(f))

# 2. Read and append all files
dfs = []
for f in source_files:
    df = pd.read_excel(f)
    print(f"Reading {os.path.basename(f)} ... {len(df)} rows")
    dfs.append(df)

combined = pd.concat(dfs, ignore_index=True)
print(f"Combined into {len(combined)} total rows")

# 3. Save the combined file into the Download folder
combined_path = os.path.join(folder, "combined.xlsx")
combined.to_excel(combined_path, index=False)
print("Saved combined file ->", combined_path)

# 4. Create a folder named with today's date
today = date.today().strftime("%Y-%m-%d")
date_folder = os.path.join(folder, today)
os.makedirs(date_folder, exist_ok=True)
print("Created date folder ->", date_folder)

# 5. Move the original files into that date folder
for f in source_files:
    dest = os.path.join(date_folder, os.path.basename(f))
    shutil.move(f, dest)
    print(f"Moved {os.path.basename(f)} -> {date_folder}")

print("Done! All files combined and moved.")