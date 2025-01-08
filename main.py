import dropbox
import os
import time
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
from flask import Flask

app = Flask(__name__)

# Dropbox Authentication
def authenticate_dropbox():
    dbx = dropbox.Dropbox('sl.CEFUOPjY-8DoZ8no8NPOMkuyD0FMoaDQt2cKdTLZtyI5J6wNgwSaaEk81-ORVg5Lq7-E1J9cahkrV07v1P3ATCAMIzIBLRhKQk4msryUt7a_VM5LDgNJ5EPfsDRK4cIrJYSr8u6ZjvpC')
    return dbx

# YouTube Authentication
def authenticate_youtube():
    CLIENT_ID = '151031036566-me353e9satmc8ueg668gc7qh7erti1f0.apps.googleusercontent.com'
    CLIENT_SECRET = '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'
    SCOPES = ['https://www.googleapis.com/auth/youtube.force-ssl']

    creds = None

    # If there is no valid refresh token, start OAuth flow
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_config(
                {
                    "installed": {
                        "client_id": CLIENT_ID,
                        "client_secret": CLIENT_SECRET,
                        "redirect_uris": ["http://localhost:5000"]
                    }
                },
                SCOPES
            )
            creds = flow.run_local_server(port=0)

        # Save credentials for the next run
        with open('token.json', 'w') as token:
            token.write(creds.to_json())

    youtube = build('youtube', 'v3', credentials=creds)
    return youtube

# Upload Video to YouTube Live Stream
def upload_video_to_youtube(youtube, video_file_path):
    request = youtube.liveBroadcasts().insert(
        part="snippet,status",
        body={
            "snippet": {
                "title": "My Live Stream",
                "scheduledStartTime": "2025-01-09T00:00:00Z"
            },
            "status": {
                "privacyStatus": "public"
            }
        }
    )
    response = request.execute()

    # Get stream details
    stream_request = youtube.liveStreams().insert(
        part="snippet,cdn",
        body={
            "snippet": {
                "title": "Live Stream Video"
            },
            "cdn": {
                "format": "1080p",
                "ingestionType": "rtmp"
            }
        }
    )
    stream_response = stream_request.execute()
    stream_url = stream_response['cdn']['ingestionInfo']['ingestionAddress']
    stream_key = '1e55-pkp9-vs6r-yc67-07q1'  # Your Stream Key
    stream_link = f"{stream_url}/{stream_key}"

    print(f"Stream Link: {stream_link}")
    return stream_link

# Download Video from Dropbox and Play on YouTube
def play_video_from_dropbox(dbx, youtube):
    folder_path = '/Apps/Youtube_live_streaming'
    video_files = dbx.files_list_folder(folder_path).entries

    for video_file in video_files:
        video_file_path = f"/{video_file.name}"
        download_video(dbx, video_file_path)

        # Upload to YouTube live stream
        upload_video_to_youtube(youtube, video_file_path)
        time.sleep(10)  # Delay between videos

def download_video(dbx, video_file_path):
    # Create a directory for downloading videos if it doesn't exist
    if not os.path.exists("downloads"):
        os.makedirs("downloads")

    with open(f"downloads/{video_file_path}", "wb") as f:
        metadata, res = dbx.files_download(path=video_file_path)
        f.write(res.content)

@app.route('/')
def index():
    dbx = authenticate_dropbox()
    youtube = authenticate_youtube()
    play_video_from_dropbox(dbx, youtube)
    return "Streaming videos from Dropbox to YouTube!"

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
