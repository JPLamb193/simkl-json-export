import requests
import configparser
import json

def make_dict(entry, media_type):
    if media_type == "tv":
        id_str = entry.get('show', {}).get('ids', {}).get('tmdb')
        tmdbId = int(id_str) if id_str and id_str.isdigit() else None
        title = entry['show']['title']
        year = str(entry['show']['year'])
        media_type = "tv"
        status = entry['status']

    elif media_type == "movie":
        id_str = entry.get('movie', {}).get('ids', {}).get('tmdb')
        tmdbId = int(id_str) if id_str and id_str.isdigit() else None
        title = entry['movie']['title']
        year = str(entry['movie']['year'])
        media_type = "movie"
        status = entry['status']

    elif media_type == "anime":
        id_str = entry.get('show', {}).get('ids', {}).get('tmdb')
        tmdbId = int(id_str) if id_str and id_str.isdigit() else None
        title = entry['show']['title']
        year = str(entry['show']['year'])
        media_type = "tv"
        status = entry['status']
    
    if status == "completed":
        status = "FINISHED"
    elif status == "plantowatch":
        status = "PLANNED"
    elif status == "dropped":
        status = "DROPPED"
    elif status == "watching":
        status = "WATCHING"
    
    new_entry = {
            "content": {
                "tmdbId": tmdbId,
                "title": title,
                "release_date": year,
                "type": media_type
            },
            "status": status,
    }
    return new_entry

def make_request(url, headers=None):
    response = requests.get(url, headers=headers)
    return response.json()

config = configparser.ConfigParser()
config.read('conf.ini')
client_id = config["CONFIGS"]["client_id"]
get_pin_url = "https://api.simkl.com/oauth/pin?client_id=" + client_id
pin_request = make_request(get_pin_url)
user_code = pin_request['user_code']
verification_url = pin_request['verification_url']
code_verification_url = "https://api.simkl.com/oauth/pin/" + user_code + "?client_id=" + client_id

is_user_authenticated = False
while not is_user_authenticated:
    print(f"Go to {verification_url} and input the code: {user_code}")
    input("After confirming the code press enter...")
    code_verification_request = make_request(code_verification_url)
    if 'access_token' in code_verification_request:
        access_token = code_verification_request['access_token']
        is_user_authenticated = True

get_titles_list_url = "https://api.simkl.com/sync/all-items/"

data = make_request(get_titles_list_url, {'Authorization':'Bearer ' + access_token, 'simkl-api-key': client_id})

show_data = data['shows']
anime_data = data['anime']
movie_data = data['movies']

show_titles = []
anime_titles = []
movie_titles = []

for show in show_data:
    new_entry = make_dict(show, "tv")
    show_titles.append(new_entry)

for anime in anime_data:
    new_entry = make_dict(anime, "anime")
    anime_titles.append(new_entry)

for movie in movie_data:
    new_entry = make_dict(movie, "movie")
    movie_titles.append(new_entry)

titles = show_titles+anime_titles+movie_titles

with open("watched.json", "w", encoding="utf-8") as file:
    json.dump(titles, file, indent=4, ensure_ascii=False)
