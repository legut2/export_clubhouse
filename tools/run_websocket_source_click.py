import json
import websocket
import requests
import time
import os
import subprocess
import csv
import pandas as pd

club_id = ""

def start_clubdeck():
    parent_directory = os.path.dirname(os.getcwd())
    os.chdir(parent_directory)
    command = "open Clubdeck.app --args --remote-debugging-port=9222"
    result = subprocess.run(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if result.returncode == 0:
        print("Command executed successfully.")
        print("Output:", result.stdout.decode())
    else:
        print("Command failed.")
        print("Error:", result.stderr.decode())
    time.sleep(10)

def click_houses_element(ws):
    # JavaScript to click the specified element
    click_script = '''
    (function() {
        var elements = document.querySelectorAll('[aria-label="Toggle Houses list"][data-customtooltip="Houses"]');
        if(elements.length > 0) {
            elements[0].click();
        }
    })();'''
    # Sending the command to evaluate the JavaScript
    ws.send(json.dumps({"id": 3, "method": "Runtime.evaluate", "params": {"expression": click_script}}))

def click_house_element(ws):
    # JavaScript to click the <a> element with a specific 'social_club_id'
    click_script = '''
    (function() {
        var elements = document.querySelectorAll('a[social_club_id="{club_id}"]');
        if(elements.length > 0) {
            console.log("Found " + elements.length + " elements with social_club_id='{club_id}'. Clicking the first one.");
            elements[0].click(); // Click the first matching <a> element
        } else {
            console.log("No elements found with social_club_id='{club_id}'.");
        }
    })();'''
    # Sending the command to evaluate the JavaScript
    ws.send(json.dumps({"id": 4, "method": "Runtime.evaluate", "params": {"expression": click_script}}))

def click_members_list_element(ws):
    # JavaScript to click the <a> element containing a <span> with class 'club_details_stat'
    click_script = '''
    (function() {
        var spans = document.querySelectorAll('span.club_details_stat');
        for (var i = 0; i < spans.length; i++) {
            var span = spans[i];
            var text = span.nextSibling.nodeValue;
            if (text && text.includes('members')) {
                span.parentNode.click(); // Click the parent <a> element of the <span>
                console.log('Clicked on members list element.');
                return;
            }
        }
        console.log('No members list element found.');
    })();'''
    # Sending the command to evaluate the JavaScript
    ws.send(json.dumps({"id": 5, "method": "Runtime.evaluate", "params": {"expression": click_script}}))

def click_user_element(ws, user_id):
    # JavaScript to click the <a> element with a specific 'user_id'
    click_script = f'''
    (function() {{
        var element = document.querySelector('a[user_id="{user_id}"]');
        if (element) {{
            console.log("Found element with user_id='{user_id}'. Clicking it.");
            element.click(); // Click the element
            return {user_id};
        }} else {{
            console.log("No element found with user_id='{user_id}'.");
            return -1;
        }}
    }})();'''
    # Sending the command to evaluate the JavaScript
    ws.send(json.dumps({"id": 6, "method": "Runtime.evaluate", "params": {"expression": click_script}}))

def get_username(ws, user_id):
    # Use f-string for dynamic JavaScript code generation with user_id
    js_script = f'''
    (function() {{
        var userNameReturn = [];
        userNameReturn.push({user_id}); // No need to convert user_id to string; JS will interpret it correctly
        var userNameElement = document.querySelector('div.header_user_name');
        if (userNameElement) {{
            var fullText = userNameElement.textContent; // Get the full text content of the element
            var usernameMatch = fullText.match(/@(\\w+)/); // Regular expression to find @username
            if (usernameMatch && usernameMatch.length > 1) {{
                console.log(usernameMatch[1]); // Log the username
                userNameReturn.push(usernameMatch[1]);
                userNameReturn.push(fullText);
                return userNameReturn; // Return the user_id and username
            }} else {{
                return userNameReturn; // Username pattern not found
            }}
        }} else {{
            return ["User name element not found."]; // Element not found
        }}
    }})();'''
    # Sending the command to evaluate the JavaScript
    ws.send(json.dumps({"id": 7, "method": "Runtime.evaluate", "params": {"expression": js_script, "returnByValue": True}}))


def get_social_media_urls(ws, user_id):
    js_script = f'''
    (function() {{
        var socialLinks = [];
        socialLinks.push({user_id});
        var links = document.querySelectorAll('div.user_social a');
        links.forEach(function(link) {{
            socialLinks.push(link.href);
        }});
        return socialLinks;
    }})();
    '''
    # Sending the command to evaluate the JavaScript
    ws.send(json.dumps({"id": 8, "method": "Runtime.evaluate", "params": {"expression": js_script, "returnByValue": True}}))

def get_user_ids(ws):
    js_script = f'''
    (function getUserIds() {{
        // Find all anchor tags within the div with the class 'user_list_content_wrapper'
        var userAnchors = document.querySelectorAll('.user_list_content_wrapper .user_name_cell a');

        // Map over the NodeList to extract the user_id attribute values
        var userIds = Array.from(userAnchors).map(anchor => anchor.getAttribute('user_id'));

        return userIds;
    }})();
    '''
    # Sending the command to evaluate the JavaScript
    ws.send(json.dumps({"id": 15, "method": "Runtime.evaluate", "params": {"expression": js_script, "returnByValue": True}}))


# function getUserIds() {
#   // Find all anchor tags within the div with the class 'user_list_content_wrapper'
#   var userAnchors = document.querySelectorAll('.user_list_content_wrapper .user_name_cell a');

#   // Map over the NodeList to extract the user_id attribute values
#   var userIds = Array.from(userAnchors).map(anchor => anchor.getAttribute('user_id'));

#   return userIds;
# }

# // Example usage:
# console.log(getUserIds());


def get_user_bio(ws, user_id):
    # JavaScript to extract the user bio from the 'div.user_bio .descriptions' element
    js_script = f'''
    (function() {{
        var retList = [];
        retList.push({user_id});
        var bioElement = document.querySelector('div.user_bio .descriptions');
        if (bioElement) {{
            retList.push(bioElement.textContent || bioElement.innerText);
            return retList; // Get the text content of the bio element
        }} else {{
            return retList; // Handle cases where the bio element doesn't exist
        }}
    }})();
    '''
    # Sending the command to evaluate the JavaScript
    ws.send(json.dumps({"id": 9, "method": "Runtime.evaluate", "params": {"expression": js_script, "returnByValue": True}}))

def get_follower_count(ws, user_id):
    # JavaScript to extract the follower count from the 'span.user_follow_stat' element
    
    js_script = f'''
    (function() {{
        var stats = [];
        stats.push({user_id});
        var elems = document.querySelectorAll('span.user_follow_stat');
        console.log(elems);
        elems.forEach(function(stat) {{{{
            stats.push(stat.textContent);
        }}}});
        if (stats) {{
            return stats; // Returns the text content, e.g., "2.4k"
        }} else {{
            return stats; // In case the element is not found
        }}
    }})();
    '''
    # Sending the command to evaluate the JavaScript
    ws.send(json.dumps({"id": 10, "method": "Runtime.evaluate", "params": {"expression": js_script, "returnByValue": True}}))

def get_user_join_date(ws, user_id):
    # JavaScript to extract the user's join date from the '.user_joined' element
    js_script = f'''
    (function() {{
        var retList = [];
        retList.push({user_id});
        var joinDateElement = document.querySelector('.user_joined');
        if (joinDateElement) {{
            var joinDateText = joinDateElement.textContent || joinDateElement.innerText;
            retList.push(joinDateText.split('Joined')[1].split('🎉')[0].trim());
            return retList; // Isolating the join date
        }} else {{
            return retList; // Element not found handling
        }}
    }})();
    '''
    # Sending the command to evaluate the JavaScript
    ws.send(json.dumps({"id": 11, "method": "Runtime.evaluate", "params": {"expression": js_script, "returnByValue": True}}))

def get_nominator_name(ws, user_id):
    # JavaScript to extract the nominator's name from the specific nested structure
    js_script = f'''
    (function() {{
        var retList = [];
        retList.push({user_id});
        var nominatedByElement = document.querySelector('.user_joined .user_card .clubdeck_user_name a');
        if (nominatedByElement) {{
            retList.push(nominatedByElement.textContent || nominatedByElement.innerText);
            return retList; // Extracting the nominator's name
        }} else {{
            return retList; // Element not found handling
        }}
    }})();
    '''
    # Sending the command to evaluate the JavaScript
    ws.send(json.dumps({"id": 13, "method": "Runtime.evaluate", "params": {"expression": js_script, "returnByValue": True}}))

def get_full_name(ws, user_id):
    # JavaScript to extract the full name from the '.header_user_name' element
    js_script = f'''
    (function() {{
        var headerNameElement = document.querySelector('.header_user_name');
        if (headerNameElement) {{
            var retList = [];
            retList.push({user_id});
            var fullText = headerNameElement.textContent || headerNameElement.innerText;
            var matches = fullText.match(/^(.*?)\\s+\\(/);
            if (matches && matches.length > 1) {{
                retList.push(matches[1].trim());
                return retList; // Returns the full name, trimmed
            }} else {{
                return retList; // In case the pattern doesn't match
            }}
        }} else {{
            return 'Header user name element not found.'; // Element not found handling
        }}
    }})();
    '''
    # Sending the command to evaluate the JavaScript
    ws.send(json.dumps({"id": 14, "method": "Runtime.evaluate", "params": {"expression": js_script, "returnByValue": True}}))


def save_username_to_csv(username):
    with open('./clbdckscrpr/usernames.csv', mode='a', newline='') as file:
        writer = csv.writer(file)
        writer.writerow([username])
    print(f"Username '{username}' saved to CSV.")

def create_csv_with_headers(filename):
    headers = ["member_id", "full name", "username", "user bio", "twitter", "insta", "followers", "following", "clubhouse join date", "nominated by"]
    with open(filename, mode='w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        writer.writerow(headers)

def add_new_member_row(filename, member_id):
    with open(filename, mode='a', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        # Assuming member_id is the only data for the new member initially
        writer.writerow([member_id] + [''] * 9)  # 9 empty fields for the rest of the columns

def update_member_info(filename, member_id, column_name, value):
    """
    Updates a member's information in a specified column in the CSV file.
    
    :param filename: Name of the CSV file.
    :param member_id: The unique identifier for the member.
    :param column_name: The name of the column to update.
    :param value: The new value to be set for the specified column.
    """
    # Load the CSV into a DataFrame
    try:
        df = pd.read_csv(filename)
    except FileNotFoundError:
        print(f"File '{filename}' not found.")
        return

    # Check if column_name exists in the DataFrame
    if column_name not in df.columns:
        print(f"Column '{column_name}' does not exist in the CSV.")
        return

    # Check if member_id exists in the DataFrame
    if not df[df['member_id'] == member_id].empty:
        df.loc[df['member_id'] == member_id, column_name] = value
        # Write the updated DataFrame back to the CSV
        df.to_csv(filename, index=False)
        print(f"Member ID {member_id}'s {column_name} updated to {value}.")
    else:
        print(f"Member ID {member_id} not found in the CSV.")

def update_member_full_name(filename, data_list):
    # data_list is expected to be in the format: [member_id, full name]
    if not data_list or len(data_list) < 2:
        print("Data list is not in the expected format.")
        return

    member_id, full_name = data_list[0], data_list[1]
    # Load the CSV into a DataFrame
    df = pd.read_csv(filename)

    # Find the row with the given member_id and update the full name
    df.loc[df['member_id'] == member_id, 'full name'] = full_name

    # Write the updated DataFrame back to the CSV
    df.to_csv(filename, index=False)

def update_social_links(filename, data):
    """
    Updates the social media links for a member in the CSV file based on provided data.

    :param filename: The name of the CSV file to update.
    :param data: A list containing the member_id followed by any number of social media links.
    """
    if len(data) < 2:
        print("Not enough data provided.")
        return

    member_id = data[0]
    social_links = data[1:]

    for link in social_links:
        if "twitter.com" in link:
            update_member_info(filename, member_id, "twitter", link)
        elif "instagram.com" in link:
            update_member_info(filename, member_id, "insta", link)
        else:
            print(f"Unknown social media link for member ID {member_id}: {link}")

todo = []
done = []

def on_message(ws, message):
    print("Received Message: ")
    message_json = json.loads(message)
    if message_json.get("id") == 7:  # Assuming ID 7 is used for get_username
        result = message_json.get("result", {}).get("result", {}).get("value")
        if result:
            print(f"Username found: {result}")
            update_member_info('./clbdckscrpr/data.csv', result[0], 'username', result[1])
        else:
            print("Username not found or message format unexpected.")
    elif message_json.get("id") == 2:
        # Handle other messages, e.g., saving page snapshot
        snapshot = message_json.get("result", {}).get("data")
        if snapshot:
            print("Saving page source to index.html")
            with open("index.html", "w") as file:
                file.write(snapshot)
            print("Page source saved.")
        else:
            print("Failed to capture page snapshot.")
    elif message_json.get("id") == 8:  # Assuming 8 is the unique ID for the get_social_media_urls call
        result = message_json.get("result", {}).get("result", {}).get("value", [])
        if result:
            print("Social Media URLs:", result)
            update_social_links('./clbdckscrpr/data.csv', result)
            # Here you can save the result (the URLs) to a CSV file or handle as needed
        else:
            print("Failed to extract social media URLs.")
    elif message_json.get("id") == 9:
        result = message_json.get("result", {}).get("result", {}).get("value", "")
        if result:
            print("User Bio:", result)
            update_member_info('./clbdckscrpr/data.csv', result[0], 'user bio', result[1])
            # Here you can further process the bio text, e.g., save to a file or display
        else:
            print("Failed to extract user bio or user bio element not found.")
    elif message_json.get("id") == 10:
        result = message_json.get("result", {}).get("result", {}).get("value", "")
        if result:
            print("Follower Count:", result)
            update_member_info('./clbdckscrpr/data.csv', result[0], 'followers', result[1])
            update_member_info('./clbdckscrpr/data.csv', result[0], 'following', result[2])
            # Here you can further process the follower count, e.g., save to a file or display
        else:
            print("Failed to extract follower count or follower count element not found.")
    elif message_json.get("id") == 11:
        result = message_json.get("result", {}).get("result", {}).get("value", "")
        if result:
            print("User Join Date:", result)
            update_member_info('./clbdckscrpr/data.csv', result[0], 'clubhouse join date', result[1])
            # Further process the join date here, e.g., saving to a database or displaying
        else:
            print("Failed to extract user join date or element not found.")
    elif message_json.get("id") == 13:
        result = message_json.get("result", {}).get("result", {}).get("value", "")
        if result:
            print("Nominator's Name:", result)
            update_member_info('./clbdckscrpr/data.csv', result[0], 'nominated by', result[1])
            # Here, you might save the result to a database, use it in further processing, or display it
        else:
            print("Failed to extract nominator's name or element not found.")
    elif message_json.get("id") == 14:
        result = message_json.get("result", {}).get("result", {}).get("value", "")
        if result:
            print("Full Name:", result)
            # update_member_full_name('data.csv', result)
            update_member_info('./clbdckscrpr/data.csv', result[0], 'full name', result[1])
            # Further process the full name here, e.g., saving to a database or displaying
        else:
            print("Failed to extract full name or element not found.")
    elif message_json.get("id") == 15:
        result = message_json.get("result", {}).get("result", {}).get("value", "")
        if result:
            print("User Ids:", result)
            print(type(result))
            todo.extend(result)

            for member in todo:
                print(member)
                member_id = member
                add_new_member_row('./clbdckscrpr/data.csv', member_id)
                time.sleep(0.2)
                click_user_element(ws,member_id)
                time.sleep(0.2)
                get_full_name(ws,member_id)
                time.sleep(0.2)
                get_username(ws,member_id)
                time.sleep(0.2)
                get_user_bio(ws,member_id)
                time.sleep(0.2)
                get_social_media_urls(ws,member_id)
                time.sleep(0.2)
                get_follower_count(ws,member_id)
                time.sleep(0.2)
                get_user_join_date(ws,member_id)
                time.sleep(0.2)
                get_nominator_name(ws,member_id)
        else:
            print("Failed to extract user ids or element not found.")
        pass

def on_open(ws):
    print("Connection Opened")
    ws.send(json.dumps({"id": 1, "method": "Page.enable"}))
    ws.send(json.dumps({"id": 2, "method": "Page.captureSnapshot", "params": {"format": "mhtml"}}))
    # Added a delay to ensure the page loads before clicking
    # time.sleep(3)  # Adjust as necessary
    # click_houses_element(ws)  # Call the function to click on houses icon
    # time.sleep(3)
    # ws.send(json.dumps({"id": 2, "method": "Page.captureSnapshot", "params": {"format": "mhtml"}}))
    time.sleep(2)
    click_house_element(ws) # Call the function to click on ssgl house specifically
    time.sleep(2)
    click_members_list_element(ws)
    time.sleep(2)
    # setup headers of csv
    create_csv_with_headers('./clbdckscrpr/data.csv')

    # get user ids
    get_user_ids(ws)
    time.sleep(30)
    # main loop - consider moving to on_message
    print("test")
    print(todo)
    print("loooooooooop start")
    

if __name__ == "__main__":
    start_clubdeck()
    websocket.enableTrace(True)
    response = requests.get('http://localhost:9222/json')
    data = response.json()
    ws = websocket.WebSocketApp("ws://localhost:9222/devtools/page/"+data[0]['id'],
                                on_open=on_open,
                                on_message=on_message)

    ws.run_forever()