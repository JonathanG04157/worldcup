from selenium import webdriver
from selenium.webdriver.edge.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.microsoft import EdgeChromiumDriverManager
import pandas as pd
from io import StringIO
import time

driver = webdriver.Edge(service=Service(EdgeChromiumDriverManager().install()))
driver.get("https://www.fifa.com/fifa-world-ranking/men")
time.sleep(10)

try:
    show_all = WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.CSS_SELECTOR, "button[aria-label='Show full rankings']"))
    )
    # Scroll the button into view and click it
    driver.execute_script("arguments[0].scrollIntoView(true);", show_all)
    time.sleep(1)
    driver.execute_script("arguments[0].click();", show_all)
    print("Clicked 'Show full rankings'")
    time.sleep(5)
except Exception as e:
    print(f"Button not found: {e}")

html = driver.page_source
driver.quit()

tables = pd.read_html(StringIO(html))
df = tables[0].copy()

df['Rank'] = df['Rank'].astype(str).str.extract(r'^(\d+)')
df['Points'] = df['Points'].astype(str).str.replace('*', '', regex=False)
df = df[['Rank', 'Team', 'Points']].copy()
df['Team'] = df['Team'].astype(str).str.extract(r'^([A-Za-z\s]+?)(?=[A-Z][a-z]|$)')

df.to_csv("fifa_rankings.csv", index=False)
print(f"Done! Saved {len(df)} teams to fifa_rankings.csv")