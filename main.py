from datetime import datetime
from flask import Flask, redirect, request, jsonify, session, render_template, url_for
import time, os, requests, urllib.parse
from google.oauth2 import service_account
from googleapiclient.discovery import build




app = Flask(__name__)
app.secret_key = 'iamthegoat'

CLIENT_ID = 'dedb959380874dafba962a1519eefd39'
CLIENT_SECRET = 'f7a36fba12ce4b8d992e98524aa3cd30'
REDIRECT_URI = 'http://127.0.0.1:5000/callback'
AUTH_URL = 'https://accounts.spotify.com/authorize'
TOKEN_URL = 'https://accounts.spotify.com/api/token'
API_BASE_URL = 'https://api.spotify.com/v1/'

KEY_FILE = 'credentials/service_account_key.json'


if not os.path.exists(KEY_FILE):
    print(f"Error: JSON key file '{KEY_FILE}' not found.")
    exit()


try:
    credentials = service_account.Credentials.from_service_account_file(KEY_FILE)
    print("Credentials successfully initialized.")
except Exception as e:
    print("Error initializing credentials:", e)
    exit()


try:
    service = build('sheets', 'v4', credentials=credentials)
    print("Google Sheets service successfully built.")
except Exception as e:
    print("Error building Google Sheets service:", e)
    exit()

spreadsheet_id = '1lIrXggee3Bo_-ngMOoyct154T5W1wTbp8r3pDQkH5U8'


def write_to_sheet(values, trial_number):
    
    sheet = service.spreadsheets()

    result = sheet.values().get(spreadsheetId=spreadsheet_id,
                                 range='Sheet1!1:1').execute()

    if 'values' in result and len(result['values']) > 0:
        num_columns = len(result['values'][0])
    else:
        num_columns = 0

    new_column = chr(65 + num_columns)  

    
    range_ = f'Sheet1!{new_column}1:{new_column}'

    
    trial_header = [['Trial {}'.format(trial_number)]]
    body = {'values': trial_header}
    sheet.values().update(
        spreadsheetId=spreadsheet_id,
        range=range_,
        valueInputOption='RAW',
        body=body).execute()

    
    body = {'values': values}
    result = sheet.values().update(
        spreadsheetId=spreadsheet_id,
        range=f'Sheet1!{new_column}2:{new_column}',
        valueInputOption='RAW',
        body=body).execute()

    print('Data successfully written to Google Sheets.')




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

    headers = {
        'Authorization': f"Bearer {session['access_token']}"
    }

    try:
        queue = requests.get(API_BASE_URL + 'me/player/queue', headers=headers)
        queue.raise_for_status()
        queue_data = queue.json()

        
        currently_playing = queue_data.get('currently_playing')

        
        queue = queue_data.get('queue', [])

        return render_template('data.html', currently_playing=currently_playing, queue=queue)
    except requests.exceptions.RequestException as e:
        app.logger.error(f"Error fetching data: {e}")

        return jsonify({"error": f"Error fetching data: {e}"})

@app.route('/skip-track', methods=['POST'])
def skip_track():
    access_token = session.get('access_token')
    if not access_token:
        return redirect('/login')

    headers = {
        'Authorization': f"Bearer {access_token}",
    }

    try:
        num_tracks_to_skip = 100  
        num_columns_to_update = 5  

        
        current_context = requests.get(API_BASE_URL + 'me/player', headers=headers).json().get('context', {}).get('uri')

        for _ in range(num_columns_to_update):
            skipped_tracks = []  

            
            for _ in range(num_tracks_to_skip):
                
                currently_playing = requests.get('https://api.spotify.com/v1/me/player/currently-playing', headers=headers).json()
                song_name = currently_playing.get('item', {}).get('name')

                
                response = requests.post('https://api.spotify.com/v1/me/player/next', headers=headers)
                response.raise_for_status()
                time.sleep(1)

                
                skipped_tracks.append(song_name)

            
            trial_number = len(session.get('skipped_tracks_lists', [])) + 1
            
            
            write_to_sheet([[track] for track in skipped_tracks], trial_number)

            
            skipped_tracks_lists = session.get('skipped_tracks_lists', [])
            skipped_tracks_lists.append(skipped_tracks)
            session['skipped_tracks_lists'] = skipped_tracks_lists

            
            requests.put(API_BASE_URL + 'me/player/play', headers=headers, json={'context_uri': 'spotify:playlist:6IooKuW8C7Sb8IyxP2S2uT'})


            
            time.sleep(1)  

            
            requests.put(API_BASE_URL + 'me/player/play', headers=headers, json={'context_uri': current_context})

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
