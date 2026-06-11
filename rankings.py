from selenium import webdriver
from selenium.webdriver.edge.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from webdriver_manager.microsoft import EdgeChromiumDriverManager
import pandas as pd
from io import StringIO
import time

driver = webdriver.Edge(service=Service(EdgeChromiumDriverManager().install()))
driver.get("https://www.fifa.com/fifa-world-ranking/men")

# Just wait 10 seconds for the page to fully load
time.sleep(10)

html = driver.page_source

# Save the raw html so we can inspect it
with open("debug.html", "w", encoding="utf-8") as f:
    f.write(html)

driver.quit()

# Try to find any tables
tables = pd.read_html(StringIO(html))
print(f"Found {len(tables)} tables")

if tables:
    df = tables[0]
    df.to_csv("fifa_rankings.csv", index=False)
    print(f"Done! Saved {len(df)} teams to fifa_rankings.csv")
else:
    print("No tables found - check debug.html to see what the page looks like")