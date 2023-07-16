
import yt_dlp
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
import re
import os
from datetime import datetime
app = FastAPI()




def hook(d):
    if d['status'] == 'finished':
        filename = d['filename']
        video_id = d['filename'].split('.')[0]
        print(filename) # Here you will see the PATH where was saved.
        with open('downloaded.txt', 'a') as f:
             f.write(f"{video_id} {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")


def get_info(youtube_id, download=False):
   youtube_url = f"https://www.youtube.com/watch?v={youtube_id}"
   ydl_opts = { 
        'format': 'bestaudio/best',
        'outtmpl': 'temp/%(id)s.%(ext)s',
        'download_archive': 'downloaded.txt',
        'noplaylist': True,   
        'quiet': True,
        'no_warnings': True,
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
        'progress_hooks': [hook]}
   info_file_path = f"temp/{youtube_id}.json"
   if os.path.exists(info_file_path):
       with open(info_file_path, 'r') as info_file:
           info = info_file.read()
   else:
       with yt_dlp.YoutubeDL(ydl_opts) as ydl:
          info = ydl.extract_info(youtube_url, download=True)
       with open(info_file_path, 'w') as info_file:
           info_file.write(str(info))
   return info

# accepts either id OR full URL
## POST http://127.0.0.1:8004/info query youtube_id [URL| ID]
def extract_youtube_id(youtube_input: str) -> str:
    # Regular expression pattern to match YouTube URLs
    url_pattern = r"(?:https?:\/\/(?:www\.)?)?youtu(?:\.be|be\.com)\/(?:watch\?v=|embed\/|v\/|\.be\/)([\w\-]+)"
    
    # Check if input matches URL pattern
    if re.match(url_pattern, youtube_input):
        # Extract the video ID from the URL
        youtube_id = re.findall(url_pattern, youtube_input)[0]
    else:
        # Assume the input is already a valid YouTube ID
        youtube_id = youtube_input
    
    return youtube_id

#EP1 Info Input YTID -> return HTML with buttons

@app.post("/info/", response_class=HTMLResponse)
async def get_info_from_button(youtube_id: str):
 youtube_id = extract_youtube_id(youtube_id)
 user_dir = "tt"
 print(user_dir, youtube_id)
 common_html = """
               <div>
               <h1> DO X or DO Y </h1>
               </div>
                <div>
                    <button onclick="transcribeSRT('{youtube_id}')" class="bg-green-600 text-white px-4 py-2 rounded-md transition duration-300 ease-in-out hover:bg-green-700 mr-2">Translate</button>
                    <button onclick="getSRT('{youtube_id}')" class="bg-blue-600 text-white px-4 py-2 rounded-md transition duration-300 ease-in-out hover:bg-blue-700">Get SRT</button>
                </div>
                <div id="transcribeResult"></div>
                <div id="getSRTResult"></div>
                 <script src="https://cdn.tailwindcss.com"></script>
                <script>
                    const youtube_id = '{youtube_id}';
                    const user_dir = '{user_dir}';

                function transcribeSRT() {{
                    fetch('/srt/translate/' + encodeURIComponent(youtube_id) + '?user_dir=' + encodeURIComponent(user_dir), {{ method: 'POST' }})
                    .then(response => response.text())
                    .then(data => {{
                        document.getElementById('transcribeResult').innerHTML = data;
                    }})
                    .catch(error => {{
                        console.error('Error:', error);
                    }});
                }}
                function getSRT() {{
                    fetch(`/srt/target/{youtube_id}?user_dir={user_dir}`)
                    .then(response => response.blob())
                    .then(blob => {{
                        const url = URL.createObjectURL(blob);
                        const a = document.createElement('a');
                        a.href = url;
                        a.download = `{youtube_id}.srt`;
                        a.click();
                    }})
                    .catch(error => {{
                        console.error('Error:', error);
                    }});
                }}
                </script>""".format(youtube_id=youtube_id,user_dir=user_dir)
 temp_dir = "temp"
 os.makedirs(temp_dir, exist_ok=True)
 info = get_info(youtube_id, True)
 return common_html