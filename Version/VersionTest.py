from selenium.webdriver.chrome import remote_connection
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.action_chains import ActionChains
from webdriver_manager.chrome import ChromeDriverManager
import os
from datetime import datetime
from dotenv import load_dotenv


load_dotenv()

class NikeBOXAutomator:
    def __init__(self):
        self.email = os.getenv("BOX_EMAIL")
        self.password = os.getenv("BOX_PASSWORD")

        self.base_path = r"D:\path\to\Selenium For BOX\Download"

        options = webdriver.ChromeOptions()
        options.add_argument("--start-maximized")
        options.add_experimental_option("prefs", {
            "download.prompt_for_download": False,
            "download.directory_upgrade": True,
            "safebrowsing.enabled": True,
        })

        self.driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
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

    def set_download_folder(self, company):
        """Create the company's folder and redirect Chrome's downloads into it."""
        today = datetime.now().strftime("%Y-%m-%d")
        self.download_path = os.path.join(self.base_path, f"{company}_{today}")
        os.makedirs(self.download_path, exist_ok=True)

        # CDP lets us change the download dir mid-session (prefs can't)
        self.driver.execute_cdp_cmd("Page.setDownloadBehavior", {
            "behavior": "allow",
            "downloadPath": self.download_path,
        })
        print(f"Downloads for {company} -> {self.download_path}")

    def go_to_root(self):
        print("Returning to root folder...")
        self.driver.get("https://app.box.com/folder/0")
        time.sleep(3)

    def open_company_folder(self, company):
        print(f"Opening {company} folder updated Jul 3...")

        # find the row that contains BOTH the company code AND "Jul 3"
        row = self.wait.until(EC.presence_of_element_located((
            By.XPATH,
            f"//div[@role='row'][contains(., '{company}') and contains(., 'Jul 3')]"
        )))

        # click the folder-name link inside THAT row
        link = row.find_element(
            By.XPATH,
            f".//a[contains(normalize-space(.), '{company}')] | .//*[contains(@aria-label,'{company}')]"
        )
        link.click()
        print(f"Clicked the Jul 3 {company} folder.")
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
        updated_header = self.wait.until(
            EC.element_to_be_clickable((By.XPATH,
                "//a[contains(@class,'SortableHeaderRenderer-link')][.//div[normalize-space()='UPDATED']]"
            ))
        )
        updated_header.click()
        print("Clicked UPDATED sort.")
        time.sleep(3)

    def download_file(self):
        print("Downloading the file with '7_3_2026' in its name...")

        target_row = self.wait.until(EC.presence_of_element_located(
            (By.XPATH, "//div[@role='row'][contains(., '7_3_2026')]")
        ))

        ActionChains(self.driver).context_click(target_row).perform()

        download_btn = self.wait.until(EC.element_to_be_clickable(
            (By.XPATH, "//*[normalize-space()='Download']")
        ))
        download_btn.click()
        print("Clicked Download.")
        time.sleep(5)

    def run(self):
        companies = ["HIC", "HIT", "HSN", "HTV"]
        try:
            self.login()

            for company in companies:
                print(f"\n===== Processing {company} =====")
                self.set_download_folder(company)   # folder + redirect downloads
                self.go_to_root()                   # back to top each time
                self.open_company_folder(company)
                self.open_download_folder()
                self.click_updated_sort()
                self.download_file()

        except Exception as e:
            print(f"Error occurred: {e}")
            input("Error occurred. Press Enter to close the browser...")

        finally:
            input("Press Enter to close the browser...")
            print("Closing browser...")
            self.driver.quit()


if __name__ == "__main__":
    automator = NikeBOXAutomator()
    automator.run()