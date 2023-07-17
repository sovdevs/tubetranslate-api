import yt_dlp
from fastapi import FastAPI,HTTPException
from fastapi.responses import HTMLResponse
import re
import os
import whisper

from datetime import datetime
# import pysrt
app = FastAPI()

MAX_WHISPER_CONTENT_SIZE = 26214400

deployment_version = os.environ.get('DEPLOYMENT_VERSION')
if deployment_version == 'dev':
    # Perform actions specific to the development version
    print("Running in development version")
    import constants
elif deployment_version == 'prod':
    # Perform actions specific to the production version
    APIKEY = os.environ.get('APIKEY')
    print("Running in production version")
    
else:
    # Handle cases where the variable is not set or has an unexpected value
    print("Unknown or undefined deployment version")

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

#EP2 transcribe returns button with API to dwnload SRT FILE
@app.post("/srt/transcribe", response_class=HTMLResponse)
async def transcribe_to_srt(youtube_id: str):
 youtube_id = extract_youtube_id(youtube_id)
 user_dir = "tt"
 print(user_dir, youtube_id)
 input_file_path = f"temp/{youtube_id}.mp3"
 output_dir = "./temp/"
 if not os.path.exists(output_dir):
    os.makedirs(output_dir)
 output_file_path = os.path.join("temp", f"{youtube_id}_src.srt")
 try:
     file_size = os.path.getsize(input_file_path)
     # By default, the Whisper API only supports files that are less than 25 MB.
     max_file_size = MAX_WHISPER_CONTENT_SIZE
     msg = ""
     if file_size > max_file_size:
        msg = "File size exceeds the content size limit. Skipping transcription."
        return """
          <div>
          <ul class="p-4 mb-4 bg-red-100">
              <li>File size: {file_size}</li>
              <li>{msg}</li>
          </ul>
          </div>
          """.format(file_size=file_size, msg=msg)
     else:
        print('Processing ' + output_file_path + '...')
        model = whisper.load_model("small") # small seems good enough for EN 
        result = model.transcribe(input_file_path,fp16=False) #taking too long
        if deployment_version == 'dev':
            from whisper.utils import write_srt
            with open(output_file_path, "w", encoding="utf-8") as srt_file:
                write_srt(result["segments"], file=srt_file)
        else:
            srt_writer = whisper.utils.get_writer("srt", output_dir)
            srt_writer(result, output_file_path)
    
        msg = f"srt written to {output_file_path}"
        return """
              <div>
              <ul class="p-4 mb-4 bg-green-100">
                  <li>File size: {file_size}</li>
                  <li>{msg}</li>
              </ul>
                   <button onclick="getSRT('{youtube_id}')" class="bg-purple-600 text-white px-4 py-2 rounded-md transition duration-300 ease-in-out hover:bg-blue-700">DL SRT file</button>
              </div>   <script src="https://cdn.tailwindcss.com"></script>
                <script>
                    const youtube_id = '{youtube_id}';
                    const user_dir = '{user_dir}';

                function transcribeSRT() {{
                    fetch('/srt/transcribe/' + encodeURIComponent(youtube_id) + '?user_dir=' + encodeURIComponent(user_dir), {{ method: 'POST' }})
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
                </script>
        """.format(file_size=file_size, msg=msg,youtube_id=youtube_id, user_dir=user_dir)

 except FileNotFoundError:
     raise HTTPException(status_code=404, detail="Output file not found.")
  
  


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
                    <button onclick="transcribeSRT('{youtube_id}')" class="bg-red-600 text-white px-4 py-2 rounded-md transition duration-300 ease-in-out hover:bg-green-700 mr-2">Transcribe/button>
                    <button onclick="summarizeSRT('{youtube_id}')" class="bg-green-600 text-white px-4 py-2 rounded-md transition duration-300 ease-in-out hover:bg-blue-700">Summarize</button>
                    <button onclick="translateSRT('{youtube_id}')" class="bg-blue-600 text-white px-4 py-2 rounded-md transition duration-300 ease-in-out hover:bg-blue-700">Translate</button>
                </div>
                <div id="transcribeResult"></div>
                <div id="getSRTResult"></div>
                 <script src="https://cdn.tailwindcss.com"></script>
                <script>
                    const youtube_id = '{youtube_id}';
                    const user_dir = '{user_dir}';

                function transcribeSRT() {{
                    fetch('/srt/transcribe/' + encodeURIComponent(youtube_id) + '?user_dir=' + encodeURIComponent(user_dir), {{ method: 'POST' }})
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