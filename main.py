import os
from dotenv import load_dotenv
import requests
import time
from colorama import Fore, Style, init

# Initialize colorama
init(autoreset=True)

# Load .env file
load_dotenv()

# Get API Key and Refresh Token from .env
api_key = os.getenv("API_KEY")
refresh_token = os.getenv("REFRESH_TOKEN")

# Define the endpoint and headers
url_check = "https://hanafuda-backend-app-520478841386.us-central1.run.app/graphql"
headers = {
    "accept": "application/graphql-response+json, application/json",
    "accept-encoding": "gzip, deflate, br, zstd",
    "accept-language": "en-US,en;q=0.9",
    "content-length": "243",
    "content-type": "application/json",
    "origin": "https://hanafuda.hana.network",
    "referer": "https://hanafuda.hana.network/",
    "sec-ch-ua": '"Brave";v="131", "Chromium";v="131", "Not_A Brand";v="24"',
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": '"Windows"',
    "sec-fetch-dest": "empty",
    "sec-fetch-mode": "cors",
    "sec-fetch-site": "cross-site",
    "sec-gpc": "1",
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
}

# Payload for checking grow actions
payload_check = {
    "operationName": "GetGardenForCurrentUser",
    "query": """
    query GetGardenForCurrentUser {
        getGardenForCurrentUser {
            id
            inviteCode
            gardenDepositCount
            gardenStatus {
                id
                growActionCount
                gardenRewardActionCount
            }
        }
    }
    """
}

# Payload for grow actions
payload_grow = {
    "operationName": "ExecuteGrowAction",
    "query": """
    mutation ExecuteGrowAction($withAll: Boolean) {
        executeGrowAction(withAll: $withAll) {
            baseValue
            leveragedValue
            totalValue
            multiplyRate
        }
    }
    """,
    "variables": {"withAll": False},
}

# Payload for fetching total points
payload_user_status = {
    "operationName": "CurrentUserStatus",
    "query": """
    query CurrentUserStatus {
        currentUser {
            totalPoint
        }
    }
    """
}

# Function to refresh ID token using refresh token
def refresh_id_token(refresh_token, api_key):
    url = f"https://securetoken.googleapis.com/v1/token?key={api_key}"
    payload = {
        "grant_type": "refresh_token",
        "refresh_token": refresh_token
    }
    response = requests.post(url, data=payload)
    
    if response.status_code == 200:
        data = response.json()
        return data.get('id_token')
    else:
        print(Fore.RED + "Error refreshing ID token:", response.status_code, response.text)
        return None

# Get Total Points
def get_total_points():
    response = requests.post(url_check, headers=headers, json=payload_user_status)
    if response.status_code == 200:
        data = response.json()
        return data["data"]["currentUser"]["totalPoint"]
    else:
        print(Fore.RED + "Failed to fetch Total Points:", response.status_code)
        return None

# Start Program
print(Fore.YELLOW + "Program dimulai . . .")
print(Style.BRIGHT + Fore.CYAN + "-"*38)

while True:
    # Refresh ID token
    new_id_token = refresh_id_token(refresh_token, api_key)
    if new_id_token:
        headers["authorization"] = f"Bearer {new_id_token}"
        response_check = requests.post(url_check, headers=headers, json=payload_check)

        if response_check.status_code == 200:
            data_check = response_check.json()
            garden_status = data_check["data"]["getGardenForCurrentUser"]["gardenStatus"]
            grow_action_count = garden_status["growActionCount"]

            if grow_action_count > 0:
                print(Fore.YELLOW + f"Grow = {Fore.GREEN + str(grow_action_count)}, executing grow action...")

                # Execute grow actions
                for i in range(grow_action_count):
                    response_grow = requests.post(url_check, headers=headers, json=payload_grow)
                    if response_grow.status_code == 200:
                        grow_data = response_grow.json()
                        grow_result = grow_data["data"]["executeGrowAction"]
                        
                        # Fetch updated Total Points after each grow execution
                        total_points = get_total_points()
                        
                        print(Fore.YELLOW + f"Execution {i+1}/{grow_action_count}:")
                        print(Fore.YELLOW + f"  Average Point: {Fore.GREEN + str(grow_result['baseValue'])}")
                        print(Fore.YELLOW + f"  Hasil Point: {Fore.GREEN + str(grow_result['totalValue'])}")
                        print(Fore.YELLOW + f"  Multiply Rate: {Fore.GREEN + str(grow_result['multiplyRate'])}")
                        print(Fore.YELLOW + f"  Updated Total Points: {Fore.CYAN + str(total_points)}")
                        print(Style.BRIGHT + Fore.CYAN + "-"*38)
                    else:
                        print(Fore.RED + f"Grow action failed for iteration {i+1}: {response_grow.status_code}")
            else:
                print(Fore.YELLOW + "No grow actions available. Retrying in 5 minutes...")
                time.sleep(300)
        else:
            print(Fore.RED + f"Failed to check garden status: {response_check.status_code}")
    else:
        print(Fore.RED + "Failed to refresh ID token.")

    time.sleep(300)  # Retry every 5 minutes
