import time
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
from youtubesearchpython import VideosSearch
from concurrent.futures import ThreadPoolExecutor
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# Google API constants
YOUTUBE_CLIENT_SECRETS_FILE = 'client_secret_172408008935-nbl374a8i4imhq518il9hahtmd1fl0ec.apps.googleusercontent.com.json'
YOUTUBE_API_SERVICE_NAME = "youtube"
YOUTUBE_API_VERSION = "v3"
YOUTUBE_SCOPES = ["https://www.googleapis.com/auth/youtube.force-ssl"]

st = time.time()

def get_youtube_client():
    """ Creates and returns a YouTube client. """
    flow = InstalledAppFlow.from_client_secrets_file(YOUTUBE_CLIENT_SECRETS_FILE, YOUTUBE_SCOPES)
    credentials = flow.run_local_server(port=8080)
    return build(YOUTUBE_API_SERVICE_NAME, YOUTUBE_API_VERSION, credentials=credentials)

def get_youtube_link(track):
    track_name = track['track']['name']
    artist_names = ', '.join(artist['name'] for artist in track['track']['artists'])
    query = f"{track_name} {artist_names}"

    try:
        videos_search = VideosSearch(query, limit=1)
        results = videos_search.result()["result"]
        if results:
            return results[0]["id"]
        else:
            print(f"No YouTube results for {track_name} by {artist_names}")
            return None
    except Exception as e:
        print(f"Error searching YouTube for {track_name} by {artist_names}: {e}")
        return None

def create_playlist(youtube, playlist_name):
    try:
        request = youtube.playlists().insert(part="snippet", body={"snippet": {"title": playlist_name, "description": "Generated Playlist"}})
        response = request.execute()
        return response["id"]
    except HttpError as e:
        print("Error creating playlist:", e)
        return None

def add_video_to_playlist(youtube, playlist_id, video_id):
    try:
        body = {
            "snippet": {
                "playlistId": playlist_id,
                "resourceId": {"kind": "youtube#video", "videoId": video_id}
            }
        }
        youtube.playlistItems().insert(part="snippet", body=body).execute()
    except HttpError as e:
        print("Error adding video to playlist:", e)

def get_spotify_tracks(sp, playlist_id):
    tracks = []
    results = sp.playlist_tracks(playlist_id)
    while results:
        tracks.extend(results['items'])
        results = sp.next(results)
    return tracks

def process_playlist(sp, youtube, spotify_playlist_id):
    playlist_info = sp.playlist(spotify_playlist_id)
    youtube_playlist_id = create_playlist(youtube, playlist_info['name'])
    tracks = get_spotify_tracks(sp, spotify_playlist_id)

    with ThreadPoolExecutor() as executor:
        video_ids = list(executor.map(get_youtube_link, tracks))

    index_width = 6  # Adjust as needed
    video_id_width = 11  # Adjust based on expected length of video IDs

    print(f"\nYoutube playlist name: {playlist_info['name']}\n")
    for index, video_id in enumerate(filter(None, video_ids), start=1):
        add_video_to_playlist(youtube, youtube_playlist_id, video_id)
        print(f"- {index:<{index_width}} Video ID: {video_id:<{video_id_width}} added to the playlist successfully")

def passed_time():
    elapsed = time.time() - st
    print(f'\nRuntime:{time.strftime("%H:%M:%S", time.gmtime(elapsed))}')
     
def main():
    client_credentials_manager = SpotifyClientCredentials(client_id='a04614d3530b4d44b45fa7da39c576c0', client_secret='082376f38e3645238d96a72a3f317757')
    sp = spotipy.Spotify(client_credentials_manager=client_credentials_manager)

    youtube = get_youtube_client()

    spotify_playlist_url = input("Enter the Spotify playlist URL: ")
    spotify_playlist_id = spotify_playlist_url.split("/")[-1].split("?")[0]

    process_playlist(sp, youtube, spotify_playlist_id)
    passed_time()

if __name__ == "__main__":
    main()