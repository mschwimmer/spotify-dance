import pandas as pd
from config import get_config
import user_functions
from flask import Flask, url_for, session, request, redirect, jsonify
from flask import render_template
from spotipy.oauth2 import SpotifyOAuth
import time
import os

app = Flask(__name__)
app.config.from_object(get_config())
data_folder = os.path.join(app.root_path, 'data')


@app.route('/')
def index():
    session.clear()
    print("Displaying index page")
    return render_template("index.html")


@app.route('/login')
def login():
    session.clear()
    print("Logging in")
    sp_oath = create_spotify_oath()
    auth_url = sp_oath.get_authorize_url()
    print(f"auth_url: {auth_url}")
    return redirect(auth_url)


@app.route('/authorize')
def authorize():
    sp_oath = create_spotify_oath()
    session.clear()
    # Storing authorization code from oath
    code = request.args.get('code')
    # Using auth code to get access token
    token_info = sp_oath.get_access_token(code)
    # Apparently future versions of library will return the straight up string, not a dict
    # So, handle either way
    if isinstance(token_info, str):
        session["token_info"]['access_token'] = token_info
    elif isinstance(token_info, dict):
        session["token_info"] = token_info
    else:
        raise TypeError("Unexpected type for token_info")
    return redirect(url_for('welcome', _external=True))


@app.route('/welcome')
def welcome():
    session['token_info'], authorized = get_token()
    session.modified = True
    if not authorized:
        return redirect('/')

    access_token = session['token_info']['access_token']
    session['user_data'] = user_functions.get_user_data(access_token)

    return render_template("welcome.html", user_data=session['user_data'])


@app.route('/get-user-song-data')
def get_user_song_data():
    print("Gathering user's song data!")
    access_token = session['token_info']['access_token']
    song_df = user_functions.get_user_songs(access_token)
    dance_df = song_df.sort_values('danceability', ascending=False).iloc[0:30]
    dance_song_dict = dance_df[
        ['track_name', 'album', 'artist', 'plist_name', 'danceability', 'uri']].to_dict(
        orient='records')

    # TODO figure out how to parse in js
    return jsonify(dance_song_dict)


@app.route('/display-dance-songs')
def display_dance_songs():

    return render_template("display-dance-songs.html")


@app.route('/create-dance-playlist', methods=['POST'])
def create_dance_playlist():
    access_token = session['token_info']['access_token']
    if 'user_data' not in session:
        session['user_data'] = user_functions.get_user_data(access_token)
    user_name = session['user_data']['display_name'].lower().replace(' ', '_')
    file_path = os.path.join(data_folder, f"{user_name}_song_data.csv")

    # Get user's dance songs
    if os.path.exists(file_path):
        # User's dance song data file already exists, load from file and send to page
        song_df = pd.read_csv(file_path)
    else:
        # User's dance songs must be gathered and stored as file
        song_df = user_functions.get_user_songs(access_token)
        # TODO use some sort of basic database for storing user's data
        #  because vercel is serverless, so you can't save anything
        # song_df.to_csv(file_path, index=False)

    dance_df = song_df.sort_values('danceability', ascending=False).iloc[0:30]

    playlist_name = request.form['playlist_name']
    # If you're ever modifying the session, need to set this
    session.modified = True
    session['created_playlist'] = False

    # Check if user already has playlist with same name
    playlist_data = user_functions.get_user_playlists(access_token)

    if playlist_name not in [item['name'] for item in playlist_data['items']]:
        # Collect list of top 30 dance track URIs
        track_uris = dance_df['uri'].to_list()
        # Create new playlist for user
        playlist_response = user_functions.create_playlist(access_token, session['user_data']['id'], playlist_name)
        # Add 30 dance tracks to new playlist
        add_tracks_response = user_functions.add_tracks_to_playlist(access_token, playlist_response['id'], track_uris)
        session['new_playlist_link'] = playlist_response['external_urls']['spotify']
        session['created_playlist'] = True
        print(f"Created new playlist {playlist_response['external_urls']['spotify']}")
    else:
        print(f"Did not create new playlist")

    print("Redirecting to result page")
    print(f"Session keys BEFORE redirect: {session.keys()}")
    return redirect(url_for('playlist_result'))


@app.route('/playlist-result')
def playlist_result():
    # created_playlist = session.get('created_playlist', False)
    print(f"Session keys AFTER redirect: {session.keys()}")
    return render_template("playlist-result.html")


def get_token():
    token_valid = False
    token_info = session.get("token_info", {})

    # Checking if the session already has a token stored
    if not session.get("token_info", False):
        token_valid = False
        return token_info, token_valid

    # Checking if token is expired
    now = int(time.time())
    is_token_expired = session.get('token_info').get('expires_at') - now < 60

    # Refreshing token if expired
    if is_token_expired:
        print("Token is expired, generating new one!")
        sp_oath = create_spotify_oath()
        token_info = sp_oath.refresh_access_token(session.get('token_info').get('refresh_token'))

    token_valid = True
    return token_info, token_valid


def create_spotify_oath():
    spotify_redirect_uri = app.config['SPOTIFY_REDIRECT_URI']
    print(f"Redirect URI: {spotify_redirect_uri}")
    print(f"Whatever url_for produces for authorize: {url_for('authorize', _external=True)}")

    return SpotifyOAuth(
        client_id=app.config['SPOTIFY_CLIENT_ID'],
        client_secret=app.config['SPOTIFY_CLIENT_SECRET'],
        redirect_uri=url_for('authorize', _external=True),
        scope="user-top-read playlist-modify-public playlist-modify-private"
    )


if __name__ == '__main__':
    app.run()
