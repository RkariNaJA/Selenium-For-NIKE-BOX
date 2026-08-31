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

        # build + create the download folder now, so Chrome can use it
        base_path = r"D:\path\to\Selenium For BOX\Download"
        today = datetime.now().strftime("%Y-%m-%d")
        self.download_path = os.path.join(base_path, f"HIC_{today}")
        os.makedirs(self.download_path, exist_ok=True)
        print(f"Download folder: {self.download_path}")

        options = webdriver.ChromeOptions()
        options.add_argument("--start-maximized")
        options.add_experimental_option("prefs", {
            "download.default_directory": self.download_path,
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

        # try:
        #     remind_btn = WebDriverWait(self.driver, 5).until(
        #         EC.element_to_be_clickable((By.XPATH, "//*[contains(text(), 'เตือนฉันในภายหลัง') or contains(text(), 'Remind me later') or @id='KmsiCheckboxField']"))
        #     )
        #     remind_btn.click()
        #     print("Clicked 'Remind me later'")
        # except Exception:
        #     print("No 'Remind me later' prompt appeared.")

        print("Login completed.")
        time.sleep(5)
    
    def open_company_folder(self):
        print("Opening HIC folder updated Jul 3...")

        # find the row that contains BOTH "HIC" and "Jul 3"
        row = self.wait.until(EC.presence_of_element_located((
            By.XPATH,
            "//div[@role='row'][contains(., 'HIC') and contains(., 'Jul 3')]"
        )))

        # click the folder-name link inside THAT row
        hic_link = row.find_element(
            By.XPATH,
            ".//a[contains(normalize-space(.), 'HIC')] | .//*[contains(@aria-label,'HIC')]"
        )
        hic_link.click()
        print("Clicked the Jul 3 HIC folder.")
        time.sleep(3)
        
    def open_download_folder(self):
        print("Opening Apparel download folder...")

        row = self.wait.until(EC.presence_of_element_located((
            By.XPATH,
            "//div[@role='row'][contains(., 'Apparel')]"
        )))
        row.click()  # or use the link inside the row (see below)
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
        print("Right-clicking the 2nd file...")

        # get all file rows (folders are rows too, so filter if needed)
        target_row = self.wait.until(EC.presence_of_element_located(
            (By.XPATH, "//div[@role='row'][contains(., '7_3_2026')]")
        ))

        # right-click to open the context menu
        ActionChains(self.driver).context_click(target_row).perform()

        # click "Download" in the menu
        download_btn = self.wait.until(EC.element_to_be_clickable(
            (By.XPATH, "//*[normalize-space()='Download']")
        ))
        download_btn.click()
        print("Clicked Download on the 2nd file.")
        time.sleep(3)

    def run(self):
        try:
            self.login()
            self.open_company_folder()
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