import json
import websocket
import requests
import time
import os
import subprocess
import csv
import pandas as pd
import queue
import threading
import sys
import logging

# Set up logging
def setup_logging():
    # Configure logging to output to console and a file
    logging.basicConfig(
        level=logging.DEBUG,  # Set to DEBUG to capture all levels of log messages
        format='%(asctime)s [%(levelname)s] %(message)s',
        handlers=[
            logging.FileHandler("debug.log", mode='w', encoding='utf-8'),
            logging.StreamHandler()
        ]
    )
    logging.info("Logging is set up.")

# Initialize logging
setup_logging()

club_id = ""
member_id_to_continue_from = "1954522788"
has_found_member_id = True

csv_file_path = './export_clubhouse/data.csv'

todo = []
done = []

# Create a thread-safe queue for messages
message_queue = queue.Queue()

# Global variables
capture_requests = {}
next_request_id = 1000  # Starting from 1000 to avoid conflicts

def get_unique_id():
    global next_request_id
    next_request_id += 1
    return next_request_id

def trigger_dialog(ws):
    logging.info("Triggering a JavaScript alert dialog.")
    js_script = '''
    (function() {
        alert("This is a test dialog.");
    })();
    '''
    ws.send(json.dumps({
        "id": 9000,
        "method": "Runtime.evaluate",
        "params": {
            "expression": js_script,
            "returnByValue": True
        }
    }))
    logging.debug("Sent trigger_dialog command.")

def prevent_dialogs(ws):
    logging.info("Injecting script to prevent dialogs.")
    js_script = '''
    window.alert = function(message) {
      console.log(message); // Do something when alert is called
      // Automatically "click" OK by not displaying the alert or handling the logic here
    };
    window.confirm = function(message) {
      console.log(message); // Do something with the confirmation dialog's message
      return true; // Automatically "clicks" OK, simulating a user clicking "OK"
    };
    '''
    ws.send(json.dumps({
        "id": get_unique_id(),
        "method": "Runtime.evaluate",
        "params": {
            "expression": js_script
        }
    }))
    logging.debug("Sent prevent_dialogs script.")


def worker():
    """Process messages from the queue in a separate thread."""
    logging.info("Worker thread started.")
    while True:
        item = message_queue.get()
        if item is None:
            # None is the signal to stop
            logging.info("Worker thread received stop signal.")
            break
        logging.debug(f"Worker thread processing item: {item}")
        process_message(item)

def process_message(message):
    global has_found_member_id, member_id_to_continue_from, ws
    """Process a single message from the WebSocket."""
    logging.debug("Received Message:")
    logging.debug(message)
    try:
        message_json = json.loads(message)
        msg_id = message_json.get("id")
        result = message_json.get("result", {}).get("result", {}).get("value")

        if msg_id == 7:  # get_username
            if result:
                logging.info(f"Username found: {result}")
                if len(result) > 2:
                    update_member_info(csv_file_path, result[0], 'username', result[1])
                    update_member_info(csv_file_path, result[0], 'full name', result[2])
                elif len(result) > 1:
                    update_member_info(csv_file_path, result[0], 'username', result[1])
                else:
                    logging.warning("Username result is too short")
                    logging.debug(result)
            else:
                logging.warning("Username not found or message format unexpected.")

        elif msg_id == 2:
            snapshot = message_json.get("result", {}).get("data")
            if snapshot:
                logging.info("Saving page source to index.html")
                with open("index.html", "w") as file:
                    file.write(snapshot)
                logging.info("Page source saved.")
            else:
                logging.warning("Failed to capture page snapshot.")

        elif msg_id == 8:  # get_social_media_urls
            if result:
                logging.info(f"Social Media URLs: {result}")
                update_social_links(csv_file_path, result)
            else:
                logging.warning("Failed to extract social media URLs.")

        elif msg_id == 9:
            if result:
                logging.info(f"User Bio: {result}")
                update_member_info(csv_file_path, result[0], 'user bio', result[1])
            else:
                logging.warning("Failed to extract user bio or user bio element not found.")

        elif msg_id == 10:
            if result:
                logging.info(f"Follower and Following Count: {result}")
                update_member_info(csv_file_path, result[0], 'followers', result[1])
                update_member_info(csv_file_path, result[0], 'following', result[2])
            else:
                logging.warning("Failed to extract follower count or follower count element not found.")

        elif msg_id == 11:
            if result:
                logging.info(f"User Join Date: {result}")
                update_member_info(csv_file_path, result[0], 'clubhouse join date', result[1])
            else:
                logging.warning("Failed to extract user join date or element not found.")

        elif msg_id == 13:
            if result:
                logging.info(f"Nominator's Name: {result}")
                if len(result) > 1:
                    update_member_info(csv_file_path, result[0], 'nominated by', result[1])
                else:
                    update_member_info(csv_file_path, result[0], 'nominated by', 'nobody')
            else:
                logging.warning("Failed to extract nominator's name or element not found.")

        elif msg_id == 14:
            if result:
                logging.info(f"Full Name: {result}")
                if len(result) > 1:
                    update_member_info(csv_file_path, result[0], 'full name', result[1])
                else:
                    update_member_info(csv_file_path, result[0], 'full name', 'NOT FOUND')
            else:
                logging.warning("Failed to extract full name or element not found.")
                update_member_info(csv_file_path, result[0], 'full name', 'NOT FOUND')

        elif msg_id == 15:
            if result:
                logging.info(f"User IDs: {result}")
                new_ids = [id for id in result if id not in done and id not in todo]
                todo.extend(new_ids)

                timing = 0.35 * 2.2
                for member in todo[:]:
                    member_id = member
                    logging.debug(f"Processing member ID: {member_id}")
                    if member_id == member_id_to_continue_from:
                        has_found_member_id = True

                    if has_found_member_id:
                        add_new_member_row(csv_file_path, member_id)
                        time.sleep(timing)
                        click_user_element(ws, member_id)
                        time.sleep(timing + 0.2)
                        get_full_name(ws, member_id)
                        time.sleep(timing)
                        get_username(ws, member_id)
                        time.sleep(timing)
                        get_user_bio(ws, member_id)
                        time.sleep(timing)
                        get_social_media_urls(ws, member_id)
                        time.sleep(timing)
                        get_follower_count(ws, member_id)
                        time.sleep(timing)
                        get_user_join_date(ws, member_id)
                        time.sleep(timing)
                        get_nominator_name(ws, member_id)
                        time.sleep(timing)
                    else:
                        time.sleep((timing * 9) + 0.2)

                    todo.remove(member)
                    done.append(member_id)
                    logging.debug(f"Member ID {member_id} processed.")

                if done:
                    time.sleep(timing)
                    scroll_to_id(ws, done[-1])
                    get_user_ids(ws)
                    time.sleep(timing)
            else:
                logging.warning("Failed to extract user IDs or element not found.")

        elif msg_id == 100:  # Page source capture upon error
            snapshot = message_json.get("result", {}).get("result", {}).get("value")
            if snapshot:
                logging.info("Saving error page source to error_page.html")
                with open("error_page.html", "w") as file:
                    file.write(snapshot)
                logging.info("Error page source saved.")
            else:
                logging.warning("Failed to capture error page snapshot.")

        else:
            logging.debug(f"Unhandled message ID: {msg_id}")

    except Exception as e:
        logging.exception("Error processing message.")
        # Attempt to capture page source upon error
        try:
            logging.info("Attempting to capture page source upon error.")
            capture_page_source(ws, "error_page.html")
        except Exception as capture_exception:
            logging.exception("Failed to capture page source upon error.")

def start_clubdeck():
    logging.info("Starting Clubdeck application.")
    try:
        parent_directory = os.path.dirname(os.getcwd())
        os.chdir(parent_directory)
        logging.debug(f"Changed directory to: {parent_directory}")

        command = "open Clubdeck.app --args --remote-debugging-port=9222"
        logging.debug(f"Command to run: {command}")

        result = subprocess.run(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        if result.returncode == 0:
            logging.info("Clubdeck started successfully.")
            logging.debug(f"Output: {result.stdout.decode()}")
        else:
            logging.error("Failed to start Clubdeck.")
            logging.error(f"Error: {result.stderr.decode()}")
            raise Exception("Clubdeck did not start as expected.")

        time.sleep(10)
        logging.info("Waited 10 seconds for Clubdeck to initialize.")
    except Exception as e:
        logging.exception("An error occurred while starting Clubdeck.")
        raise e

def click_houses_element(ws):
    logging.info("Clicking on the Houses element.")
    click_script = '''
    (function() {
        var elements = document.querySelectorAll('[aria-label="Toggle Houses list"][data-customtooltip="Houses"]');
        if(elements.length > 0) {
            elements[0].click();
        }
    })();'''
    ws.send(json.dumps({"id": 3, "method": "Runtime.evaluate", "params": {"expression": click_script}}))

def click_house_element(ws):
    logging.info(f"Clicking on the House with ID {club_id}.")
    click_script = f'''
    (function() {{
        var elements = document.querySelectorAll('a[social_club_id="{club_id}"]');
        if(elements.length > 0) {{
            console.log("Found " + elements.length + " elements with social_club_id='{club_id}'. Clicking the first one.");
            elements[0].click();
        }} else {{
            console.log("No elements found with social_club_id='{club_id}'.");
        }}
    }})();'''
    ws.send(json.dumps({"id": 4, "method": "Runtime.evaluate", "params": {"expression": click_script}}))

def click_members_list_element(ws):
    logging.info("Clicking on the Members List element.")
    click_script = '''
    (function() {
        var spans = document.querySelectorAll('span.club_details_stat');
        for (var i = 0; i < spans.length; i++) {
            var span = spans[i];
            var text = span.nextSibling.nodeValue;
            if (text && text.includes('members')) {
                span.parentNode.click();
                console.log('Clicked on members list element.');
                return;
            }
        }
        console.log('No members list element found.');
    })();'''
    ws.send(json.dumps({"id": 5, "method": "Runtime.evaluate", "params": {"expression": click_script}}))

def click_user_element(ws, user_id):
    logging.info(f"Clicking on user element with ID {user_id}.")
    click_script = f'''
    (function() {{
        var element = document.querySelector('a[user_id="{user_id}"]');
        if (element) {{
            console.log("Found element with user_id='{user_id}'. Clicking it.");
            element.click();
            return "{user_id}";
        }} else {{
            console.log("No element found with user_id='{user_id}'.");
            return -1;
        }}
    }})();'''
    ws.send(json.dumps({"id": 6, "method": "Runtime.evaluate", "params": {"expression": click_script}}))

def get_username(ws, user_id):
    logging.info(f"Getting username for user ID {user_id}.")
    js_script = f'''
    (function() {{
        var userNameReturn = [];
        userNameReturn.push("{user_id}");
        var userNameElement = document.querySelector('div.header_user_name');
        if (userNameElement) {{
            var fullText = userNameElement.textContent;
            var usernameMatch = fullText.match(/@(\\w+)/);
            if (usernameMatch && usernameMatch.length > 1) {{
                console.log(usernameMatch[1]);
                userNameReturn.push(usernameMatch[1]);
                userNameReturn.push(fullText);
                return userNameReturn;
            }} else {{
                return userNameReturn;
            }}
        }} else {{
            return ["User name element not found."];
        }}
    }})();'''
    ws.send(json.dumps({"id": 7, "method": "Runtime.evaluate", "params": {"expression": js_script, "returnByValue": True}}))

def get_social_media_urls(ws, user_id):
    logging.info(f"Getting social media URLs for user ID {user_id}.")
    js_script = f'''
    (function() {{
        var socialLinks = [];
        socialLinks.push("{user_id}");
        var links = document.querySelectorAll('div.user_social a');
        links.forEach(function(link) {{
            socialLinks.push(link.href);
        }});
        return socialLinks;
    }})();
    '''
    ws.send(json.dumps({"id": 8, "method": "Runtime.evaluate", "params": {"expression": js_script, "returnByValue": True}}))

def get_user_ids(ws):
    logging.info("Getting user IDs from the member list.")
    js_script = '''
    (function getUserIds() {
        var userAnchors = document.querySelectorAll('.user_list_content_wrapper .user_name_cell a');
        var userIds = Array.from(userAnchors).map(anchor => anchor.getAttribute('user_id'));
        return userIds;
    })();
    '''
    ws.send(json.dumps({"id": 15, "method": "Runtime.evaluate", "params": {"expression": js_script, "returnByValue": True}}))

def get_user_bio(ws, user_id):
    logging.info(f"Getting user bio for user ID {user_id}.")
    js_script = f'''
    (function() {{
        var retList = [];
        retList.push("{user_id}");
        var bioElement = document.querySelector('div.user_bio .descriptions');
        if (bioElement) {{
            retList.push(bioElement.textContent || bioElement.innerText);
            return retList;
        }} else {{
            return retList;
        }}
    }})();
    '''
    ws.send(json.dumps({"id": 9, "method": "Runtime.evaluate", "params": {"expression": js_script, "returnByValue": True}}))

def get_follower_count(ws, user_id):
    logging.info(f"Getting follower count for user ID {user_id}.")
    js_script = f'''
    (function() {{
        var stats = [];
        stats.push("{user_id}");
        var elems = document.querySelectorAll('span.user_follow_stat');
        console.log(elems);
        elems.forEach(function(stat) {{
            stats.push(stat.textContent);
        }});
        if (stats) {{
            return stats;
        }} else {{
            return stats;
        }}
    }})();
    '''
    ws.send(json.dumps({"id": 10, "method": "Runtime.evaluate", "params": {"expression": js_script, "returnByValue": True}}))

def get_user_join_date(ws, user_id):
    logging.info(f"Getting user join date for user ID {user_id}.")
    js_script = f'''
    (function() {{
        var retList = [];
        retList.push("{user_id}");
        var joinDateElement = document.querySelector('.user_joined');
        if (joinDateElement) {{
            var joinDateText = joinDateElement.textContent || joinDateElement.innerText;
            retList.push(joinDateText.split('Joined')[1].split('🎉')[0].trim());
            return retList;
        }} else {{
            return retList;
        }}
    }})();
    '''
    ws.send(json.dumps({"id": 11, "method": "Runtime.evaluate", "params": {"expression": js_script, "returnByValue": True}}))

def get_nominator_name(ws, user_id):
    logging.info(f"Getting nominator's name for user ID {user_id}.")
    js_script = f'''
    (function() {{
        var retList = [];
        retList.push("{user_id}");
        var nominatedByElement = document.querySelector('.user_joined .user_card .clubdeck_user_name a');
        if (nominatedByElement) {{
            retList.push(nominatedByElement.textContent || nominatedByElement.innerText);
            return retList;
        }} else {{
            return retList;
        }}
    }})();
    '''
    ws.send(json.dumps({"id": 13, "method": "Runtime.evaluate", "params": {"expression": js_script, "returnByValue": True}}))

def get_full_name(ws, user_id):
    logging.info(f"Getting full name for user ID {user_id}.")
    js_script = f'''
    (function() {{
        var headerNameElement = document.querySelector('div.header_user_name');
        var retList = ["{user_id}"];
        if (headerNameElement) {{
            var fullText = headerNameElement.textContent || headerNameElement.innerText;
            var matches = fullText.match(/^(.*?)(?:\\s+\\(|$)/);
            if (matches && matches[1]) {{
                retList.push(headerNameElement.textContent || headerNameElement.innerText);
            }}
        }} 
        return retList;
    }})();
    '''
    ws.send(json.dumps({"id": 14, "method": "Runtime.evaluate", "params": {"expression": js_script, "returnByValue": True}}))

def create_csv_with_headers(filename):
    logging.info(f"Creating CSV file with headers at {filename}.")
    headers = ["member_id", "full name", "username", "user bio", "twitter", "insta", "followers", "following", "clubhouse join date", "nominated by"]
    with open(filename, mode='w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        writer.writerow(headers)

def add_new_member_row(filename, member_id):
    logging.info(f"Adding new member row for member ID {member_id}.")
    with open(filename, mode='a', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        writer.writerow([member_id] + [''] * 9)

def update_member_info(filename, member_id, column_name, value):
    try:
        logging.info(f"Updating member info for member ID {member_id}, column '{column_name}' with value '{value}'.")
        df = pd.read_csv(filename, dtype={'member_id': str})

        if column_name not in df.columns:
            logging.warning(f"Column '{column_name}' does not exist in the CSV.")
            return

        # Check if the member_id exists
        if not df[df['member_id'] == member_id].empty:
            # Update existing member
            df.loc[df['member_id'] == member_id, column_name] = value
        else:
            # Add new member row if not found
            logging.info(f"Member ID {member_id} not found in the CSV. Adding new row.")
            # Create a new row with default empty values
            new_row = {col: '' for col in df.columns}
            new_row['member_id'] = member_id
            new_row[column_name] = value
            # Append the new row to the dataframe
            df = df.append(new_row, ignore_index=True)
        # Save the updated dataframe back to the CSV
        df.to_csv(filename, index=False)
        logging.info(f"Member ID {member_id}'s {column_name} updated to {value}.")
    except Exception as e:
        logging.exception(f"An error occurred while updating member info: {e}")

def update_social_links(filename, data):
    if len(data) < 2:
        logging.warning("Not enough data provided for social links.")
        return

    member_id = data[0]
    social_links = data[1:]

    for link in social_links:
        if "twitter.com" in link:
            update_member_info(filename, member_id, "twitter", link)
        elif "instagram.com" in link:
            update_member_info(filename, member_id, "insta", link)
        else:
            logging.info(f"Unknown social media link for member ID {member_id}: {link}")

def scroll_to_id(ws, user_id):
    logging.info(f"Scrolling to user ID {user_id}.")
    js_script = f'''
        var element = document.querySelector('.user_list_content_wrapper a[user_id="{user_id}"]');
        if (element) {{
            element.scrollIntoView({{ behavior: 'smooth', block: 'start' }});
        }}
    '''
    ws.send(json.dumps({"id": 16, "method": "Runtime.evaluate", "params": {"expression": js_script, "returnByValue": True}}))

def capture_page_source(ws, filename="page_source.html"):
    logging.info(f"Capturing page source to {filename}.")
    snapshot_script = "document.documentElement.outerHTML;"
    ws.send(json.dumps({"id": 100, "method": "Runtime.evaluate", "params": {"expression": snapshot_script, "returnByValue": True}}))

def on_message(ws, message):
    """Enqueue messages instead of processing them directly."""
    logging.debug("Enqueue message.")
    message_queue.put(message)

def on_open(ws):
    global has_found_member_id
    logging.info("WebSocket connection opened.")
    try:
        ws.send(json.dumps({"id": 1, "method": "Page.enable"}))
        ws.send(json.dumps({"id": 2, "method": "Network.enable"}))
        ws.send(json.dumps({"id": 6, "method": "DOM.enable"})) 
        ws.send(json.dumps({"id": 3, "method": "Overlay.enable"}))  # Enable Overlay domain
        ws.send(json.dumps({"id": 4, "method": "Runtime.enable"}))  # Enable Runtime domain
        ws.send(json.dumps({"id": 5, "method": "Log.enable"}))      # Enable Log domain
        
        # Delay to allow page initialization
        time.sleep(3)
        
        # Inject script to prevent dialogs
        logging.info("Injecting prevent_dialogs script.")
        prevent_dialogs(ws)
        
        # Trigger the dialog box
        logging.info("Triggering a test dialog.")
        trigger_dialog(ws)
        time.sleep(2) 

        time.sleep(2)
        click_house_element(ws)
        time.sleep(2)
        click_members_list_element(ws)
        time.sleep(2)
        if has_found_member_id:
            create_csv_with_headers(csv_file_path)
            time.sleep(2)
        logging.debug(f"Todo list type: {type(todo)}")
        logging.debug(f"Todo list content: {todo}")
        get_user_ids(ws)
        time.sleep(3)
    except Exception as e:
        logging.exception("An error occurred during the on_open event.")
        # Attempt to capture page source upon error
        try:
            capture_page_source(ws, "error_page_on_open.html")
        except Exception as capture_exception:
            logging.exception("Failed to capture page source upon error in on_open.")

def clear_cache():
    global ws
    logging.info("Clearing cache via DevTools Protocol.")
    try:
        # Enable the Network domain if not already enabled
        ws.send(json.dumps({"id": 1000, "method": "Network.enable"}))
        time.sleep(1)  # Wait briefly to ensure the command is processed

        # Clear the browser cache
        ws.send(json.dumps({"id": 1001, "method": "Network.clearBrowserCache"}))
        logging.info("Cache clear command sent via DevTools Protocol.")
    except Exception as e:
        logging.exception("Failed to clear cache.")
# The periodic cache clear function needs to be moved outside the main block
def periodic_cache_clear(interval):
    while True:
        time.sleep(interval)
        clear_cache()
        
if __name__ == "__main__":
    try:
        number_of_arguments = len(sys.argv)
        if number_of_arguments > 1:
            club_id = sys.argv[1]
            member_id_to_continue_from = sys.argv[2]
            has_found_member_id = False
            logging.info(f"Club ID set to {club_id}, starting from member ID {member_id_to_continue_from}.")

        start_clubdeck()

        # Set up the worker thread
        threading.Thread(target=worker, daemon=True).start()
        logging.info("Worker thread started.")

        websocket.enableTrace(False)
        response = requests.get('http://localhost:9222/json')
        data = response.json()
        ws_url = "ws://localhost:9222/devtools/page/" + data[0]['id']
        ws = websocket.WebSocketApp(ws_url, on_open=on_open, on_message=on_message)
        logging.info(f"WebSocket URL: {ws_url}")

        # Start the periodic cache clearing in a separate thread
        threading.Thread(target=periodic_cache_clear, args=(1800,), daemon=True).start()  # Clear cache every 30 minutes
        logging.info("Cache clearing thread started.")

        try:
            ws.run_forever()
        except KeyboardInterrupt:
            logging.info("WebSocket run_forever stopped by user.")
        finally:
            message_queue.put(None)
            logging.info("Main thread terminating.")

    except Exception as e:
        logging.exception("An unexpected error occurred in the main block.")


