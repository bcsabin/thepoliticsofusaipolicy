from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import os
import logging
from datetime import datetime
import glob
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

# Set up logging
log_filename = f"scraper_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_filename),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Create downloads directory if it doesn't exist
download_dir = "your file location here"
os.makedirs(download_dir, exist_ok=True)

# Configure Chrome options for downloads
chrome_options = webdriver.ChromeOptions()
prefs = {
    "download.default_directory": download_dir,
    "download.prompt_for_download": False,
    "download.directory_upgrade": True,
    "safebrowsing.enabled": True
}
chrome_options.add_experimental_option("prefs", prefs)

# Initialize WebDriver with options
driver = webdriver.Chrome(options=chrome_options)

try:
    driver.get("https://www.regulations.gov/document/NTIA-2023-0009-0001/comment?pageNumber=14")
    logger.info("Successfully opened the target page")
except Exception as e:
    logger.error(f"Failed to open target page: {e}")
    driver.quit()
    exit()

# Wait for the page to load
time.sleep(5)

# Function to save text as PDF
def save_text_as_pdf(text, filename):
    """
    Saves extracted text as a PDF file.
    """
    pdf_path = os.path.join(download_dir, filename)
    c = canvas.Canvas(pdf_path, pagesize=letter)
    c.setFont("Helvetica", 12)

    # Split text into lines to fit within PDF page limits
    y_position = 750
    for line in text.split("\n"):
        c.drawString(50, y_position, line)
        y_position -= 20
        if y_position < 50:  # Start a new page if needed
            c.showPage()
            c.setFont("Helvetica", 12)
            y_position = 750
    
    c.save()
    logger.info(f"Text comment saved as PDF: {pdf_path}")

# Scrape all cards and download files or text
while True:
    try:
        # Wait for cards to be present
        WebDriverWait(driver, 10).until(
            EC.presence_of_all_elements_located((By.CLASS_NAME, "card-type-comment"))
        )
        cards = driver.find_elements(By.CLASS_NAME, "card-type-comment")
        logger.info(f"Found {len(cards)} cards on current page")
        
        for index, card in enumerate(cards, 1):
            try:
                link = card.find_element(By.TAG_NAME, "a").get_attribute('href')
                card_name = card.find_element(By.TAG_NAME, "a").text
                logger.info(f"Processing card {index}/{len(cards)}: {card_name}")
                
                driver.get(link)
                time.sleep(5)

                # Check if a downloadable file exists
                file_downloaded = False

                try:
                    download_btn = driver.find_element(By.CSS_SELECTOR, "a.btn.btn-default.btn-block[download]")
                    download_url = download_btn.get_attribute('href')
                    original_filename = download_url.split('/')[-1]

                    logger.info(f"Downloading: {original_filename}")
                    download_btn.click()
                    time.sleep(2)

                    # Wait for the file to appear in the download directory
                    elapsed_time = 0
                    max_wait_time = 50
                    downloaded_file = None

                    while elapsed_time < max_wait_time:
                        files = glob.glob(os.path.join(download_dir, "*.pdf"))
                        if files:
                            downloaded_file = max(files, key=os.path.getctime)
                            if downloaded_file.endswith(".pdf"):
                                file_downloaded = True
                                break
                        time.sleep(5)
                        elapsed_time += 5

                    if downloaded_file:
                        logger.info(f"File successfully downloaded: {downloaded_file}")
                    else:
                        logger.warning(f"Download failed for: {card_name}")

                except Exception as e:
                    logger.warning(f"No downloadable file found: {e}")

                # If no file was downloaded, extract and save text as PDF
                if not file_downloaded:
                    try:
                        # Locate the text inside <div class="px-2">
                        comment_divs = driver.find_elements(By.CLASS_NAME, "px-2")

                        # Extract text
                        comment_texts = [div.text.strip() for div in comment_divs if div.text.strip()]
                        
                        if comment_texts:
                            full_comment_text = "\n\n".join(comment_texts)
                            pdf_filename = f"{card_name.replace(' ', '_')}.pdf"

                            # Save the text as a PDF
                            save_text_as_pdf(full_comment_text, pdf_filename)

                        else:
                            logger.warning("No text found in the comment section.")

                    except Exception as e:
                        logger.error(f"Error extracting text: {e}")

                driver.back()
                time.sleep(5)
            except Exception as e:
                logger.error(f"Error processing card {index}: {e}")
                continue

        # Check for next page
        try:
            # Re-fetch next button dynamically to avoid stale element issues
            next_button = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "button[aria-label='Next page']"))
            )

            # Ensure button is visible and enabled
            if next_button.is_displayed() and next_button.is_enabled():
                logger.info("Moving to next page")
                driver.execute_script("arguments[0].scrollIntoView();", next_button)
                time.sleep(1)
                driver.execute_script("arguments[0].click();", next_button)  # Use JavaScript click
                time.sleep(5)
            else:
                logger.info("Next page button is disabled. Scraping complete.")
                break

        except Exception as e:
            logger.info("No next page button found or reached the last page. Scraping complete.")
            break

    except Exception as e:
        logger.error(f"Error during scraping: {e}")
        break

logger.info("Scraping completed. Closing browser.")
driver.quit()
