import requests
import configparser
import json

def make_dict(entry, media_type):
    if media_type in ["tv", "anime"]:
        source = entry.get('show', {})
        output_type = "tv"
    else:  # movie
        source = entry.get('movie', {})
        output_type = "movie"

    id_str = source.get('ids', {}).get('tmdb')
    tmdbId = int(id_str) if id_str and id_str.isdigit() else None

    # Status mapping
    status_map = {
        "completed": "FINISHED",
        "plantowatch": "PLANNED",
        "dropped": "DROPPED",
        "watching": "WATCHING"
    }
    status = status_map.get(entry.get('status'), entry.get('status'))

    return {
        "content": {
            "tmdbId": tmdbId,
            "title": source.get('title'),
            "release_date": str(source.get('year', '')),
            "type": output_type
        },
        "status": status
    }

def make_request(url, headers=None):
    response = requests.get(url, headers=headers)
    return response.json()

config = configparser.ConfigParser()
files_read = config.read('conf.ini')

if not files_read:
    print("Error: conf.ini file not found. Please create it with your Simkl API credentials. Follow readme for instructions.")
    exit(1)

try:
    client_id = config["CONFIGS"]["client_id"]
    if not client_id:
        raise ValueError("client_id is empty")
except KeyError:
    print("Error: conf.ini is missing [CONFIGS] section or client_id key.")
    print("Expected format:")
    print("[CONFIGS]")
    print("client_id = YOUR_CLIENT_ID_HERE")
    exit(1)
except ValueError as e:
    print(f"Error: {e}")
    exit(1)

get_pin_url = "https://api.simkl.com/oauth/pin?client_id=" + client_id
try:
    pin_request = make_request(get_pin_url)
    user_code = pin_request['user_code']
    verification_url = pin_request['verification_url']
except (requests.RequestException, KeyError) as e:
    print(f"Error getting PIN from Simkl API: {e}")
    exit(1)
code_verification_url = "https://api.simkl.com/oauth/pin/" + user_code + "?client_id=" + client_id

is_user_authenticated = False
max_attempts = 10
attempts = 0

while not is_user_authenticated and attempts < max_attempts:
    print(f"Go to {verification_url} and input the code: {user_code}")
    input("After confirming the code press enter...")

    try:
        code_verification_request = make_request(code_verification_url)
        if 'access_token' in code_verification_request:
            access_token = code_verification_request['access_token']
            is_user_authenticated = True
        else:
            print("Not authenticated yet. Make sure you've entered the code on the website.")
    except requests.RequestException as e:
        print(f"Network error: {e}. Retrying...")

    attempts += 1

if not is_user_authenticated:
    print("Failed to authenticate after multiple attempts. Please try running the script again.")
    exit(1)

get_titles_list_url = "https://api.simkl.com/sync/all-items/"
try:
    data = make_request(get_titles_list_url, {
        'Authorization': 'Bearer ' + access_token,
        'simkl-api-key': client_id
    })
except requests.RequestException as e:
    print(f"Error fetching watchlist data: {e}")
    exit(1)

show_data = data.get('shows', [])
anime_data = data.get('anime', [])
movie_data = data.get('movies', [])

titles = (
    [make_dict(s, "tv") for s in show_data] +
    [make_dict(a, "anime") for a in anime_data] +
    [make_dict(m, "movie") for m in movie_data]
)

with open("watched.json", "w", encoding="utf-8") as file:
    json.dump(titles, file, indent=4, ensure_ascii=False)
