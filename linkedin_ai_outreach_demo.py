# linkedin_ai_outreach_demo.py

import time
import openai
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By

# ==== CONFIG ====
LINKEDIN_PROFILE_URL = "https://www.linkedin.com/in/satyanadella/"  # Public demo profile
GPT_TEMPLATE = (
    "Hi {name}, I came across your profile and was really impressed by your experience at {headline}. "
    "I'd love to connect and learn more about your work. Looking forward to connecting!"
)

# ==== SETUP OPENAI ====
openai.api_key = "YOUR_OPENAI_API_KEY"  # <-- Replace this once

# ==== SETUP SELENIUM ====
options = Options()
options.add_argument("--headless")
options.add_argument("--disable-gpu")
driver = webdriver.Chrome(options=options)

# ==== FUNCTION TO SCRAPE PROFILE ====
def scrape_linkedin_profile(url):
    driver.get(url)
    time.sleep(5)  # Wait for page to load

    try:
        name = driver.find_element(By.CSS_SELECTOR, "h1.text-heading-xlarge").text.strip()
    except:
        name = "Professional"

    try:
        headline = driver.find_element(By.CSS_SELECTOR, "div.text-body-medium.break-words").text.strip()
    except:
        headline = "your role"

    try:
        location = driver.find_element(By.CSS_SELECTOR, "span.text-body-small.inline.t-black--light.break-words").text.strip()
    except:
        location = "unknown location"

    return {"name": name, "headline": headline, "location": location}

# ==== FUNCTION TO GENERATE MESSAGE ====
def generate_message(profile):
    prompt = GPT_TEMPLATE.format(**profile)
    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "You are a professional LinkedIn assistant."},
            {"role": "user", "content": prompt}
        ]
    )
    return response.choices[0].message.content.strip()

# ==== MAIN FUNCTION ====
def main():
    print("Scraping LinkedIn profile...")
    profile_data = scrape_linkedin_profile(LINKEDIN_PROFILE_URL)
    print("Profile scraped:", profile_data)

    print("\nGenerating personalized message...")
    message = generate_message(profile_data)

    print("\n\u2705 Final Output:")
    print("-------------------------")
    print(message)
    print("-------------------------")

    driver.quit()

if __name__ == "__main__":
    main()
