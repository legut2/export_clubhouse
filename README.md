# export_clubhouse
This is an unstable script to help export members of groups off of [clubhouse](https://www.clubhouse.com/), a social audio mobile application. It makes use of running a 3rd party application called [clubdeck](https://www.clubdeck.app/). This application can be controlled in a similar way a web browser can be controlled by [selenium](https://www.selenium.dev/). This is due to clubdeck being an electron app. This same method could probably be extended for other popular electron applications such as discord, signal, [and many others](https://en.wikipedia.org/wiki/List_of_software_using_Electron).
  
This script works by slowly grabbing profile data of each member over time. 

# Highlights
* It exports about **362~ members/hour**.
* In theory, a group with **100,000 members** would take about **11.5~ days** of runtime to export.
* Currently stable up up to **25,000 members** before encountering problems.
  
# Requirements
- A physical sim card and cheap phone plan from a company such as tello. (twilio, google voice, etc. won't work)
- An old phone
- Mac w/ 32GB of RAM (or just contribute more performant code because this code is unoptimized and naively implemented)
- Chrome installed to allow for debugging
- Clubdeck installed (tested on version 2.6.4)
- Python 3.12.5
  
# Getting Started  
- Make a clubhouse account  
- Verify through your spare phone with activated phone plan
- Follow person who posted about group most recently
- Clone directory and place within Mac's Applications folder to have paths correct
- Create virtual environment using `python3 -m venv venv`
- `source ./venv/bin/activate`
- Install python dependencies with `pip install -r requirements.txt`
- Verify that the chromedriver in this repo is capable of driving the same version of chrome you have and that this code hasn't experienced code rot. You can find versions of chromedriver [here](https://developer.chrome.com/docs/chromedriver/downloads).
- Identify `club_id` by scripts that are tools for identifying such things. When `clubdeck` launches, the post someone made in your feed should be the first one. It gets to the club through their post.
- Paste `club_id` you found into `export.py`
- `python export.py` to run
- `python export.py member_id_here` to run a continuation where it gets back to place it left off by scrolling to it and then appending once it gets back to its spot it left off at.