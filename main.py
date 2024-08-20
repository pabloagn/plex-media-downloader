import os
import tomli
from plexapi.server import PlexServer
from plexapi.myplex import MyPlexAccount
import requests
import sys

def load_config(config_file='config.toml'):
    """
    Load configuration from a TOML file using tomli.
    """
    config_path = os.path.join("config", config_file)
    if not os.path.exists(config_path):
        raise FileNotFoundError(f"Configuration file '{config_path}' not found.")
    
    with open(config_path, 'rb') as f:
        config = tomli.load(f)
    
    try:
        plex_url = config['credentials']['plex_url']
        plex_token = config['credentials']['plex_token']
        input_dir = config['directories']['input_dir']
        output_dir = config['directories']['output_dir']
    except KeyError as e:
        raise KeyError(f"Missing required configuration key: {e}")
    
    return plex_url, plex_token, input_dir, output_dir

def get_raw_response(url, token):
    headers = {'X-Plex-Token': token}
    response = requests.get(url, headers=headers)
    return response.text

def download_playlist(plex, playlist_name, output_dir):
    try:
        playlist = plex.playlist(playlist_name)
    except Exception as e:
        print(f"Error finding playlist '{playlist_name}': {e}")
        return

    playlist_dir = os.path.join(output_dir, playlist_name)
    os.makedirs(playlist_dir, exist_ok=True)
    
    for track in playlist.items():
        try:
            filename = f"{track.title}.{track.media[0].parts[0].container}"
            filepath = os.path.join(playlist_dir, filename)
            
            part = track.media[0].parts[0]
            download_url = part._server.url(f'{part.key}?download=1', includeToken=True)
            
            response = requests.get(download_url)
            response.raise_for_status()
            with open(filepath, 'wb') as f:
                f.write(response.content)
            
            print(f"Downloaded: {filename}")
        except Exception as e:
            print(f"Error downloading track '{track.title}': {e}")

def main():
    try:
        plex_url, plex_token, input_dir, output_dir = load_config()
        
        print(f"Connecting to Plex server at {plex_url}")
        
        raw_response = get_raw_response(plex_url, plex_token)
        print("Raw server response:")
        print(raw_response)
        
        try:
            account = MyPlexAccount(token=plex_token)
            plex = account.resource(plex_url).connect()
            print("Successfully connected to Plex server using MyPlexAccount")
        except Exception as e:
            print(f"Failed to connect using MyPlexAccount: {e}")
            plex = PlexServer(plex_url, plex_token)
            print("Successfully connected to Plex server using direct connection")
        
        playlists_file = os.path.join(input_dir, 'playlists.txt')
        with open(playlists_file, 'r') as f:
            playlists = f.read().splitlines()
        
        for playlist in playlists:
            print(f"Downloading playlist: {playlist}")
            download_playlist(plex, playlist, output_dir)
            print(f"Finished downloading playlist: {playlist}")
        
    except Exception as e:
        print(f"An error occurred: {e}", file=sys.stderr)
        if isinstance(e, requests.exceptions.RequestException):
            print(f"Response content: {e.response.content}", file=sys.stderr)

if __name__ == "__main__":
    main()