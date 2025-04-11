from flask import Flask, request, jsonify
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
import requests
import time

app = Flask(__name__)

# ✅ Add your actual API keys
HUNTER_API_KEY = 'add'
LINKEDIN_COOKIE = 'add'

@app.route("/")
def home():
    return "✅ LinkedIn Scraper API is running. Use `/search?position=DevOps&location=Bangalore` to fetch data."

def get_profiles(position, location):
    chrome_options = Options()
    # Optional: uncomment to run headless
    # chrome_options.add_argument("--headless")
    chrome_options = Options()
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--enable-unsafe-webgpu")
    chrome_options.add_argument("--enable-unsafe-swiftshader")

    # ✅ Path to your ChromeDriver
    service = Service(r"C:\Windows\chromedriver.exe")

    try:
        driver = webdriver.Chrome(service=service, options=chrome_options)

        # Load LinkedIn and set cookie
        driver.get("https://www.linkedin.com")
        time.sleep(2)

        driver.delete_all_cookies()
        driver.add_cookie({
            "name": "li_at",
            "value": LINKEDIN_COOKIE,
            "domain": ".linkedin.com"
        })

        # Search for people
        search_url = f"https://www.linkedin.com/search/results/people/?keywords={position}%20{location}"
        driver.get(search_url)
        time.sleep(5)

        profiles = []
        results = driver.find_elements(By.CSS_SELECTOR, ".entity-result__content")

        for result in results[:5]:  # Limit to 5 results
            try:
                name = result.find_element(By.CSS_SELECTOR, ".entity-result__title-text span").text.strip()
                title = result.find_element(By.CSS_SELECTOR, ".entity-result__primary-subtitle").text.strip()
                loc = result.find_element(By.CSS_SELECTOR, ".entity-result__secondary-subtitle").text.strip()

                if " at " in title:
                    company = title.split(" at ")[-1].strip()
                    domain_guess = company.lower().replace(" ", "") + ".com"
                else:
                    company = "Unknown"
                    domain_guess = "example.com"

                profiles.append({
                    "name": name,
                    "title": title,
                    "location": loc,
                    "company": company,
                    "domain_guess": domain_guess
                })
                print(profiles);

            except Exception:
                continue

        return profiles

    except Exception as e:
        return [{"error": str(e)}]

    finally:
        try:
            driver.quit()
        except:
            pass

def find_email(name, domain):
    url = f"https://api.hunter.io/v2/email-finder?domain={domain}&full_name={name}&api_key={HUNTER_API_KEY}"
    response = requests.get(url)
    data = response.json()
    print("data ::::::", data)
    return data.get("data", {}).get("email", "Not found")

@app.route("/search", methods=["GET"])
def search():
    position = request.args.get("position")
    location = request.args.get("location")

    if not position or not location:
        return jsonify({"error": "Please provide both 'position' and 'location' in the query string."}), 400

    results = get_profiles(position, location)

    for result in results:
        if "name" in result and "domain_guess" in result:
            result["email"] = find_email(result["name"], result["domain_guess"])

    return jsonify(results)

if __name__ == "__main__":
    app.run(debug=True)
