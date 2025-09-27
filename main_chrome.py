import time
import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options
import config
import streamlit as st

def initialize_browser():
    chrome_options = Options()
    if config.HEADLESS:
        chrome_options.add_argument("--headless")
    chrome_options.add_argument("--disable-notifications")
    driver = webdriver.Chrome(
        service=Service(ChromeDriverManager().install()),
        options=chrome_options
    )
    return driver

def login_to_linkedin(driver):
    driver.get("https://www.linkedin.com/login")
    time.sleep(config.DELAY_BETWEEN_ACTIONS)
    
    email_field = driver.find_element(By.ID, "username")
    email_field.send_keys(config.LINKEDIN_EMAIL)
    
    password_field = driver.find_element(By.ID, "password")
    password_field.send_keys(config.LINKEDIN_PASSWORD)
    
    login_button = driver.find_element(By.XPATH, "//button[@type='submit']")
    login_button.click()
    time.sleep(config.DELAY_BETWEEN_ACTIONS * 3)

def scrape_profile_data(driver, profile_url):
    driver.get(profile_url)
    time.sleep(config.DELAY_BETWEEN_ACTIONS * 2)
    
    try:
        name = driver.find_element(By.XPATH, "//h1[contains(@class, 'text-heading-xlarge')]").text.strip()
        headline = driver.find_element(By.XPATH, "//div[contains(@class, 'text-body-medium')]").text.strip()
        
        try:
            experience_section = driver.find_element(By.ID, "experience")
            current_position = experience_section.find_element(By.XPATH, ".//li[1]//div[contains(@class, 'display-flex')]")
            company = current_position.find_element(By.XPATH, ".//span[contains(@class, 't-14 t-normal')]").text.strip()
            position = current_position.find_element(By.XPATH, ".//span[contains(@class, 't-bold')]").text.strip()
        except:
            company = "their company"
            position = "their role"
        
        try:
            location = driver.find_element(By.XPATH, "//span[contains(@class, 'text-body-small') and contains(., 'Location')]/following-sibling::span").text.strip()
        except:
            location = "your area"
        
        return {
            "name": name.split()[0],
            "full_name": name,
            "headline": headline,
            "company": company,
            "position": position,
            "location": location,
            "profile_url": profile_url
        }
    except Exception as e:
        print(f"Error scraping profile: {e}")
        return None

def generate_personalized_message(profile_data):
    headers = {"Authorization": f"Bearer {config.HF_API_KEY}"}
    
    # Load template
    with open("templates/connection.txt", "r") as f:
        template = f.read()
    
    prompt = f"""
    Create a LinkedIn connection request using this template:
    {template}
    
    Profile information:
    Name: {profile_data['name']}
    Headline: {profile_data['headline']}
    Company: {profile_data['company']}
    Position: {profile_data['position']}
    
    Rules:
    - Keep it professional (2-3 sentences)
    - Reference specific profile details
    - Don't include placeholders
    """
    
    payload = {
        "inputs": prompt,
        "parameters": {
            "max_new_tokens": 100,
            "temperature": 0.7
        }
    }
    
    try:
        response = requests.post(
            f"https://api-inference.huggingface.co/models/{config.HF_MODEL_NAME}",
            headers=headers,
            json=payload
        )
        return response.json()[0]['generated_text']
    except Exception as e:
        print(f"Error generating message: {e}")
        return template.format(**profile_data)

def main(profile_url):
    driver = initialize_browser()
    try:
        login_to_linkedin(driver)
        profile_data = scrape_profile_data(driver, profile_url)
        if not profile_data:
            return "Failed to scrape profile data"
        
        message = generate_personalized_message(profile_data)
        return {
            "profile_data": profile_data,
            "message": message
        }
    finally:
        driver.quit()

def streamlit_app():
    st.title("LinkedIn AI Outreach (Hugging Face)")
    profile_url = st.text_input(
        "Enter LinkedIn Profile URL:",
        value="https://www.linkedin.com/in/example"
    )
    
    if st.button("Generate Connection Message"):
        with st.spinner("Processing profile..."):
            result = main(profile_url)
            
            if isinstance(result, str):
                st.error(result)
            else:
                st.subheader("Profile Information")
                st.json(result["profile_data"])
                
                st.subheader("Generated Message")
                st.text_area("Message", 
                           value=result["message"], 
                           height=150)
                
                st.success("Done!")

if __name__ == "__main__":
    streamlit_app()