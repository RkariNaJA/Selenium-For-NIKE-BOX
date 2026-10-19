#Can be run only on Monday
from selenium.webdriver.chrome import remote_connection
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import TimeoutException
from webdriver_manager.chrome import ChromeDriverManager
import os
from datetime import datetime
from datetime import datetime, timedelta
from dotenv import load_dotenv


load_dotenv()

class NikeBOXAutomator:
    def __init__(self):
        self.email = os.getenv("BOX_EMAIL")
        self.password = os.getenv("BOX_PASSWORD")

        self.base_path = os.getenv("BOX_FOLDER_PATH") or os.path.join(os.path.dirname(os.path.abspath(__file__)), "Download")

        options = webdriver.ChromeOptions()
        options.add_argument("--start-maximized")
        options.add_experimental_option("prefs", {
            "download.prompt_for_download": False,
            "download.directory_upgrade": True,
            "safebrowsing.enabled": True,
        })

        self.driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
        # --start-maximized can give a small window on servers/RDP, which hides Box columns
        self.driver.set_window_size(1920, 1080)
        self.wait = WebDriverWait(self.driver, 20)

    def login(self):
        print("Navigating to Nike BOX...")
        self.driver.get("https://app.box.com/folder/0")

        print("Entering email...")
        email_input = self.wait.until(EC.element_to_be_clickable((By.XPATH, "//input[@type='text' or contains(@name, 'login')]")))
        email_input.send_keys(self.email)
        next_btn = self.wait.until(EC.element_to_be_clickable((By.XPATH, "//button[@type='submit' or contains(text(), 'Next')]")))
        next_btn.click()

        print("Entering password...")
        password_input = self.wait.until(EC.element_to_be_clickable((By.XPATH, "//input[@type='password' or contains(@name, 'password')]")))
        password_input.send_keys(self.password)

        verify_btn = self.wait.until(EC.element_to_be_clickable((By.XPATH, "//button[@type='submit' or @textContent = 'Log in']")))
        verify_btn.click()

        print("Login completed.")
        time.sleep(5)

    def set_download_folder(self):
        """Point Chrome's downloads at the base Download folder."""
        os.makedirs(self.base_path, exist_ok=True)

        self.driver.execute_cdp_cmd("Page.setDownloadBehavior", {
            "behavior": "allow",
            "downloadPath": self.base_path,
        })
        print(f"Downloads -> {self.base_path}")

    def go_to_root(self):
        print("Returning to root folder...")
        self.driver.get("https://app.box.com/folder/0")
        time.sleep(3)

    def open_company_folder(self, company):
        # Monday run -> Friday's folder (3 days back)
        target_date = datetime.now() - timedelta(days=3)
        # Box shows dates like "Jul 10, 2026" (no leading zero on day)
        date_str = f"{target_date.strftime('%b')} {target_date.day}, {target_date.year}"

        print(f"Opening {company} folder updated {date_str} or Today...")

        # match the row with EXACT '{company}' name AND (Friday's date OR "Today")
        row = self.wait.until(EC.presence_of_element_located((
            By.XPATH,
            f"//div[@role='row']"
            f"[.//a[normalize-space(.)='{company}'] "
            f"and (contains(., '{date_str}') or contains(., 'Today'))]"
        )))

        link = row.find_element(By.XPATH, f".//a[normalize-space(.)='{company}']")
        link.click()
        print(f"Clicked the {company} folder.")
        time.sleep(3)

    def open_download_folder(self):
        print("Opening Apparel download folder...")

        row = self.wait.until(EC.presence_of_element_located((
            By.XPATH,
            "//div[@role='row'][contains(., 'Apparel')]"
        )))
        row.click()
        print("Clicked Apparel folder.")
        time.sleep(3)

    def click_updated_sort(self):
        print("Clicking UPDATED column header...")
        try:
            updated_header = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.XPATH,
                    "//a[contains(@class,'SortableHeaderRenderer-link')]"
                    "[.//div[translate(normalize-space(),'updated','UPDATED')='UPDATED']]"
                ))
            )
        except TimeoutException:
            # Box hides the Updated column in narrow windows; download_file finds the row by name anyway
            print("UPDATED header not found - skipping sort.")
            return
        updated_header.click()
        print("Clicked UPDATED sort.")
        time.sleep(3)

    
    def download_file(self):
        # date 2 days ago (run Monday -> targets Friday)
        target_date = datetime.now() - timedelta(days=3)

        # build "M_D_YYYY" with NO leading zeros, e.g. 7_3_2026
        date_str = f"{target_date.month}_{target_date.day}_{target_date.year}"

        print(f"Downloading the file with '{date_str}' in its name...")

        target_row = self.wait.until(EC.presence_of_element_located(
            (By.XPATH, f"//div[@role='row'][contains(., '{date_str}')]")
        ))

        ActionChains(self.driver).context_click(target_row).perform()

        download_btn = self.wait.until(EC.element_to_be_clickable(
            (By.XPATH, "//*[normalize-space()='Download']")
        ))
        download_btn.click()
        print(f"Clicked Download on the {date_str} file.")
        time.sleep(5)
        
    def run(self):
        companies = ["HIC", "HIT", "HSN", "HTV"]
        skip = {"HIG"}
        try:
            self.login()

            for company in companies:
                if company in skip:
                    print(f"\n===== Skipping {company} =====")
                    continue

                print(f"\n===== Processing {company} =====")
                self.go_to_root()                   # back to top each time
                self.open_company_folder(company)
                self.open_download_folder()
                self.click_updated_sort()
                self.download_file()

        except Exception as e:
            print(f"Error occurred: {type(e).__name__}: {e}")
            shot = os.path.join(self.base_path, "error_screenshot.png")
            os.makedirs(self.base_path, exist_ok=True)
            self.driver.save_screenshot(shot)
            print(f"Screenshot saved -> {shot}")
            input("Error occurred. Press Enter to close the browser...")

        finally:
            input("Press Enter to close the browser...")
            print("Closing browser...")
            self.driver.quit()


if __name__ == "__main__":
    automator = NikeBOXAutomator()
    automator.run()