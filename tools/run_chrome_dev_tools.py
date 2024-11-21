from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import requests
from selenium.webdriver.common.by import By
import time
import subprocess
import os
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def start_clubdeck():
    # Move to the parent directory of the current working directory
    parent_directory = os.path.dirname(os.getcwd())
    os.chdir(parent_directory)

    # Command to execute
    command = "open Clubdeck.app --args --remote-debugging-port=9222"

    # Run the command
    result = subprocess.run(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    # Check if the command was executed successfully
    if result.returncode == 0:
        print("Command executed successfully.")
        print("Output:", result.stdout.decode())
    else:
        print("Command failed.")
        print("Error:", result.stderr.decode())
        
    time.sleep(10)
# start clubdeck
# start_clubdeck()
# start clubdeck

response = requests.get('http://localhost:9222/json')
data = response.json()  # Assuming the response is JSON-formatted
print(data)
print(data[0]['id'])

# Path to your Electron application
# electron_app_path = '../Clubdeck.app/Contents/MacOS/Clubdeck'
chrome_app_path = '../../Google Chrome.app/Contents/MacOS/Google Chrome'

# Specify the path to Chromedriver
chromedriver_path_for_clubdeck = '../chromedriver'

# Add the path of the Electron app as a binary location
chrome_options = Options()
# chrome_options.binary_location = electron_app_path
chrome_options.binary_location = chrome_app_path
chrome_options.path = chromedriver_path_for_clubdeck
# Add additional arguments as needed. This argument is often necessary for Electron apps.
chrome_options.add_argument('--no-sandbox')

# Initialize the driver with the path to chromedriver and the customized options
driver = webdriver.Chrome(options=chrome_options)
# driver.get("http://localhost:9222/devtools/inspector.html?ws=localhost:9222/devtools/page/01875F64A39C266DCDA0D3957B7AEA9B")
driver.get("http://localhost:9222/devtools/inspector.html?ws=localhost:9222/devtools/page/"+data[0]['id'])



# driver.implicitly_wait(10)
time.sleep(10)
# element = driver.find_element_by_xpath('/html/body/div/div/div[2]/div[1]/div[2]/a/svg/path')
# element = driver.find_elements(By.XPATH,"/html/body/div/div/div[2]/div[1]/div[2]/a")
# #root > div > div.header > div.header_profile > div:nth-child(3) > a
# Using CSS Selector to find an element with a specific aria-label
# element = driver.find_element(By.XPATH, '/html/body/div/div/div[1]/div[1]/div[2]')
# print(element.text)

source = driver.page_source

# Save the page source to 'index.html'
with open('index.html', 'w', encoding='utf-8') as file:
    file.write(source)

# wait = WebDriverWait(driver, 10)  # Wait for up to 10 seconds
# element = wait.until(EC.visibility_of_element_located((By.XPATH, '/html/body/div/div/div[1]/div[1]/div[2]/a')))
# print(element.text)

#/html/body/div/div/div[2]/div[1]/div[2]/a/svg/path
# for e in elements:
#     print(e.text)
# element.click()