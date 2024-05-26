from datetime import datetime
from flask import Flask, redirect, request, jsonify, session, render_template, url_for
import time, os, requests, urllib.parse
from google.oauth2 import service_account
from googleapiclient.discovery import build
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET_KEY', 'default_secret_key')

CLIENT_ID = os.getenv('SPOTIFY_CLIENT_ID')
CLIENT_SECRET = os.getenv('SPOTIFY_CLIENT_SECRET')
REDIRECT_URI = 'http://127.0.0.1:5000/callback'
AUTH_URL = 'https://accounts.spotify.com/authorize'
TOKEN_URL = 'https://accounts.spotify.com/api/token'
API_BASE_URL = 'https://api.spotify.com/v1/'

KEY_FILE = 'credentials/service_account_key.json'

if not os.path.exists(KEY_FILE):
    app.logger.error(f"Error: JSON key file '{KEY_FILE}' not found.")
    exit()

try:
    credentials = service_account.Credentials.from_service_account_file(KEY_FILE)
    service = build('sheets', 'v4', credentials=credentials)
    app.logger.info("Google Sheets service successfully built.")
except Exception as e:
    app.logger.error(f"Error initializing Google Sheets service: {e}")
    exit()

spreadsheet_id = ''

def write_to_sheet(song_name):
    sheet = service.spreadsheets()

    
    column = '' # Adjust yourself  
    
    current_data = sheet.values().get(spreadsheetId=spreadsheet_id, range=f'Sheet1!{column}:{column}').execute()
    current_values = current_data.get('values', [])
    next_row = len(current_values) + 1

   
    song_range = f'Sheet1!{column}{next_row}'
    body = {'values': [[song_name]]}  
    result = sheet.values().update(
        spreadsheetId=spreadsheet_id,
        range=song_range,
        valueInputOption='RAW',
        body=body).execute()

    print(f'Song "{song_name}" successfully written to Google Sheets at {column}{next_row}.')

def init_session():
    if 'skipped_tracks' not in session:
        session['skipped_tracks'] = []

@app.before_request
def before_request():
    init_session()

@app.route('/')
def home():
    access_token = session.get('access_token')
    return render_template('home.html', access_token=access_token)

@app.route('/login')
def login():
    scope = 'user-read-private user-read-email user-modify-playback-state user-read-recently-played user-top-read user-read-currently-playing user-read-playback-state'
    params = {
        'client_id': CLIENT_ID,
        'response_type': 'code',
        'scope': scope,
        'redirect_uri': REDIRECT_URI,
        'show_dialog': True
    }
    auth_url = f"{AUTH_URL}?{urllib.parse.urlencode(params)}"
    return redirect(auth_url)

@app.route('/data')
def data():
    if 'access_token' not in session:
        return redirect('/login')
    if datetime.now().timestamp() >= session['expires_at']:
        return redirect('/refresh-token')

    headers = {'Authorization': f"Bearer {session['access_token']}"}

    try:
        queue = requests.get(API_BASE_URL + 'me/player/queue', headers=headers)
        queue.raise_for_status()
        queue_data = queue.json()

        currently_playing = queue_data.get('currently_playing')
        queue = queue_data.get('queue', ['name'])
        song_names = [item['name'] for item in queue]

        return render_template('data.html', currently_playing=currently_playing, queue=queue,song_names= song_names)
    except requests.exceptions.RequestException as e:
        app.logger.error(f"Error fetching data: {e}")
        return jsonify({"error": f"Error fetching data: {e}"})
@app.route('/log-track', methods=['POST'])
def skip_track():
    access_token = session.get('access_token')
    if not access_token:
        return redirect('/login')

    headers = {
        'Authorization': f"Bearer {access_token}",
    }

    try:
        num_songs = 1000  # Number of songs to record

        
        current_context = requests.get(API_BASE_URL + 'me/player', headers=headers).json().get('context', {}).get('uri')

        for _ in range(num_songs):
            currently_playing = requests.get('https://api.spotify.com/v1/me/player/currently-playing', headers=headers).json()
            song_name_original = currently_playing.get('item', {}).get('name')
            artist = currently_playing.get('item',{}).get('id')
            write_to_sheet(str(song_name_original) + " ID " + str(artist))
            requests.put(API_BASE_URL + 'me/player/play', headers=headers, json={'context_uri': 'spotify:playlist:LOL'}) # Making it play an invalid playlist as a way to reset the shuffle
            time.sleep(3)  # Wait for the playlist to change (adjust as needed)

            requests.put(API_BASE_URL + 'me/player/play', headers=headers, json={'context_uri': current_context})
            time.sleep(3)  # Wait for the context to change back (adjust as needed)

     
        requests.put(API_BASE_URL + 'me/player/play', headers=headers, json={'context_uri': 'spotify:playlist:LOL'}) # Making it play an invalid playlist as a way to reset the shuffle

        return redirect('/data')
    except requests.exceptions.RequestException as e:
        error_message = f"Error skipping tracks: {e}"
        print(error_message)
        return redirect('/data')



@app.route('/callback')
def callback():
    if 'error' in request.args:
        return jsonify({"error": request.args['error']})

    if 'code' in request.args:
        req_body = {
            'code': request.args['code'],
            'grant_type': 'authorization_code',
            'redirect_uri': REDIRECT_URI,
            'client_id': CLIENT_ID,
            'client_secret': CLIENT_SECRET
        }

        response = requests.post(TOKEN_URL, data=req_body)
        token_info = response.json()

        session['access_token'] = token_info['access_token']
        session['refresh_token'] = token_info['refresh_token']
        session['expires_at'] = datetime.now().timestamp() + token_info['expires_in']

        return redirect('/data')

@app.route('/refresh-token')
def refresh_token():
    if 'refresh_token' not in session:
        return redirect('/login')
    if datetime.now().timestamp() > session['expires_at']:
        req_body = {
            'grant_type': 'refresh_token',
            'refresh_token': session['refresh_token'],
            'client_id': CLIENT_ID,
            'client_secret': CLIENT_SECRET
        }

        response = requests.post(TOKEN_URL, data=req_body)
        new_token_info = response.json()

        session['access_token'] = new_token_info['access_token']
        session['expires_at'] = datetime.now().timestamp() + new_token_info['expires_in']

        return redirect('/data')

if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True)
