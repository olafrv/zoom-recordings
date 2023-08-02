
import os
import requests
import re
import base64
from datetime import datetime
import calendar
import pickle

# Environment variables
ACCOUNT_ID = os.environ.get("ZOOM_ACCOUNT_ID")
CLIENT_ID = os.environ.get("ZOOM_CLIENT_ID")
CLIENT_SECRET = os.environ.get("ZOOM_CLIENT_SECRET")
RECORDING_YEAR = int(os.environ.get("ZOOM_RECORDING_YEAR"))
RECORDING_MONTH_FROM = int(os.environ.get("ZOOM_RECORDING_MONTH_FROM"))
RECORDING_MONTH_TO = int(os.environ.get("ZOOM_RECORDING_MONTH_TO"))
USERS_FILTER = os.environ.get("ZOOM_USERS_FILTER")

def get_first_and_last_day(year, month):
    if not 1 <= month <= 12:
        raise ValueError("Month should be between 1 and 12.")
    
    from_date = f"{year:04d}-{month:02d}-01"
    last_day = calendar.monthrange(year, month)[1]
    to_date = f"{year:04d}-{month:02d}-{last_day:02d}"
    
    return from_date, to_date


def get_access_token(account_id, client_id, client_secret):
    base_url = "https://zoom.us/oauth/token"
    data = {
        "grant_type": "account_credentials",
        "account_id": account_id
    }

    auth_string = f"{client_id}:{client_secret}"
    base64_auth_string = base64.b64encode(auth_string.encode()).decode()

    headers = {
        "Authorization": f"Basic {base64_auth_string}",
        "Content-Type": "application/x-www-form-urlencoded"
    }

    response = requests.post(base_url, data=data, headers=headers)

    if response.status_code == 200:
        access_token = response.json().get("access_token")
        return access_token
    else:
        raise Exception("Failed to get access token. Check your account credentials.")


# https://developers.zoom.us/docs/api/rest/reference/zoom-api/methods/#operation/users
def get_all_users(access_token):

    base_url = "https://api.zoom.us/v2/users"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    users_list = []
    params = { "page_size": 300 }
    
    while True:
        response = requests.get(base_url, headers=headers, params=params)
        print(response.url + ":" + str(response.status_code))

        if response.status_code == 200:
            data = response.json()
            users_list.extend(data.get("users", []))

            # https://devforum.zoom.us/t/how-to-paginate-using-next-page-token/87128
            next_page_token = data.get("next_page_token")
            if next_page_token:
                params["next_page_token"] = next_page_token
            else:
                break
        else:
            raise Exception("Failed to fetch users list. Check your access token.")

    return users_list


# https://developers.zoom.us/docs/api/rest/reference/zoom-api/methods/#operation/recordingsList
def get_all_recordings(year, month, access_token, user_id):

    base_url = f"https://api.zoom.us/v2/users/{user_id}/recordings"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    from_date, to_date = get_first_and_last_day(year, month)
    params = {
        "page_size": 300,
        "from": from_date,
        "to": to_date
    }
    recordings_list = []

    while True:
        response = requests.get(base_url, headers=headers, params=params)
        print(response.url + ":" + str(response.status_code))

        if response.status_code == 200:
            data = response.json()
            recordings_list.extend(data.get("meetings", []))

            # Check if there is another page of results
            # https://devforum.zoom.us/t/how-to-paginate-using-next-page-token/87128
            next_page_token = data.get("next_page_token")
            if next_page_token:
                params["next_page_token"] = next_page_token
            else:
                break
        else:
            raise Exception(f"Failed to fetch recordings list for user {user_id}. Check your access token.")

    return recordings_list


def download_zoom_recording(access_token, recording_name, download_url, download_dir="./downloads"):
    
    date_today = datetime.now().strftime('%Y-%m-%d')
    filename = re.sub(r'\W+', '_', f"{date_today}_{recording_name}")  # AlphaNum_
    filename = f"{download_dir}/{filename}.mp4"

    if os.path.exists(filename):
        print(f"Recording {filename} exists, skipped.")
        return True
    else:
        print(f"Recording {filename} do not exists.")
    
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    
    response = requests.get(download_url, headers=headers)
    if response.status_code == 200:
        print(filename + ", " + response.url + ":" + str(response.status_code))
        with open(filename, "wb") as f:
            f.write(response.content)
            print(f"Recording downloaded successfully as {filename}.")
    else:
        print(f"Failed to download recording. Check your access token.")


def cache_data(data, filename):
    with open(filename, "wb") as f:
        pickle.dump(data, f)


def load_cached_data(filename):
    if os.path.exists(filename):
        with open(filename, "rb") as f:
            return pickle.load(f)
    else:
        return None


if __name__ == "__main__":

    if (not ACCOUNT_ID or not CLIENT_ID or not CLIENT_SECRET
        or not RECORDING_YEAR or not RECORDING_MONTH_FROM or not RECORDING_MONTH_TO
        or not USERS_FILTER):
        raise Exception("Please set the ZOOM_* environment variables.")

    if USERS_FILTER is not None:
        if USERS_FILTER.strip() == "": 
            USERS_FILTER = None
        else:
            USERS_FILTER = USERS_FILTER.split(",")
    print(USERS_FILTER)

    access_token = get_access_token(ACCOUNT_ID, CLIENT_ID, CLIENT_SECRET)

    users_list_cached = load_cached_data("users_list_cache.pkl")
    if users_list_cached is None:
        users_list = get_all_users(access_token)
        cache_data(users_list, "users_list_cache.pkl")
    else:
        users_list = users_list_cached

    recordings_list_cached = load_cached_data("recordings_dict_cache.pkl")
    if recordings_list_cached is None:
        recordings_list = {}
        for user in users_list:
            if USERS_FILTER is None or user.get("email") in USERS_FILTER:
                user_id = user.get("id") 
                recordings_list[user_id] = []
                for month in range(RECORDING_MONTH_FROM, RECORDING_MONTH_TO):
                    recordings_list[user_id] += get_all_recordings(
                        RECORDING_YEAR, month, access_token, user_id
                    )
        
        cache_data(recordings_list, "recordings_dict_cache.pkl")
    else:
        recordings_list = recordings_list_cached

    for user_id in recordings_list:
        recordings = recordings_list[user_id]
        for recording in recordings:
            recording_name = recording["topic"]
            recording_files = recording["recording_files"]
            for file in recording_files:
                if file["recording_type"] != "audio_only":
                    recording_name += "_" + file["id"]
                    download_url = file["download_url"]
                    download_zoom_recording(access_token, recording_name, download_url)