import yt_dlp
import asyncio
import sys
from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks, Request, status
from fastapi.responses import HTMLResponse, FileResponse,JSONResponse
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from loguru import logger
import re
import os
import whisper
import subprocess
import schedule
import json
import time
from datetime import datetime
from pytube import YouTube

# import pysrt
app = FastAPI()
logger.remove()
logger.add(
    sys.stdout,
    colorize=True,
    format="<green>{time:HH:mm:ss}</green> | {level} | <level>{message}</level>",
)
security = HTTPBasic()

MAX_WHISPER_CONTENT_SIZE = 26214400


#### Client Code
@app.get("/srt/source")
async def get_file_src_srt(video_id: str, download_path: str)->FileResponse:
    file_path = os.path.join(download_path, f"{video_id}_src.srt")
    if os.path.exists(file_path):
        return FileResponse(file_path)
    else:
        error_msg = {"error": "File not ready yet. Please try again later"}
        raise HTTPException(status_code=status.HTTP_202_ACCEPTED, detail=error_msg)

@app.get("/srt/target")
async def get_file_trg_srt(youtube_id: str, download_path: str)->FileResponse:
    file_path = os.path.join(download_path, f"{youtube_id}_trg.srt")
    if os.path.exists(file_path):
        return FileResponse(file_path)
    else:
        error_msg = {"error": "File not ready yet. Please try again later"}
        raise HTTPException(status_code=status.HTTP_202_ACCEPTED, detail=error_msg)

@app.get("/plain/source")
async def get_file_src_txt(youtube_id: str, download_path: str)->FileResponse:
    file_path = os.path.join(download_path, f"{youtube_id}_src.txt")
    if os.path.exists(file_path):
        return FileResponse(file_path)
    else:
        error_msg = {"error": "File not ready yet. Please try again later"}
        raise HTTPException(status_code=status.HTTP_202_ACCEPTED, detail=error_msg)

@app.get("/plain/target")
async def get_file_trg_txt(youtube_id: str, download_path: str)->FileResponse:
    file_path = os.path.join(download_path, f"{youtube_id}_trg.txt")
    if os.path.exists(file_path):
        return FileResponse(file_path)
    else:
        error_msg = {"error": "File not ready yet. Please try again later"}
        raise HTTPException(status_code=status.HTTP_202_ACCEPTED, detail=error_msg)

@app.get("/file_processed")
async def check_file(youtube_id: str, download_path: str):
    file_path = os.path.join(download_path, f"{youtube_id}_trg.srt")
    
    if os.path.exists(file_path) and os.path.getsize(file_path) > 0:
        return JSONResponse(content={"file_exists": True}, status_code=status.HTTP_200_OK)
    else:
        return JSONResponse(content={"file_exists": False}, status_code=status.HTTP_404_NOT_FOUND)

### alkt DL 
async def download_best_audio_ytdl(video_url, download_path):
    options = {
        'format': 'bestaudio/best',
        'outtmpl': os.path.join(download_path, '%(id)s.%(ext)s'),
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],}
    with yt_dlp.YoutubeDL(options) as ydl:
        ydl.download([video_url])

async def download_best_audio(video_url, save_path):
    try:
        yt = YouTube(video_url)
        # Select the highest resolution available (itag=22) for downloading
        audio_stream = yt.streams.filter(only_audio=True).first()
        logger.info("Downloading audui:", audio_stream.title)
        audio_stream.download(output_path=save_path)
        logger.info("Download audio complete!")
    except Exception as e:
        pass
        logger.error("Error:", str(e))


def extract_video_url(video_id:str)-> str:
    return f"https://www.youtube.com/watch?v={video_id}"

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

def get_len_text(s:str)->int:
    if s is not None:
        return len(s.split())
    else:
        return 0

async def write_plain_text(output_file_path_plain: str, plain_text: str):
    try:
        with open(output_file_path_plain, "w", encoding="utf-8") as file:
            file.write(plain_text)
        logger.info("Writing to plain text completed")
    except Exception as e:
        logger.error("Failed to writeplain text file")
        pass  # Ignore the exception silently

async def get_transcript(video_id: str,download_path: str):
    file_path = os.path.join(download_path, f"{video_id}.mp3")
    logger.info(f"Getting Source Transcrpt: {video_id}")
    file_size = 0
    if os.path.exists(file_path):
        file_size = os.path.getsize(file_path)
    if 0< file_size < MAX_WHISPER_CONTENT_SIZE:
        output_file_path = os.path.join(download_path, f"{video_id}_src.srt")
        output_file_path_plain = os.path.join(download_path, f"{video_id}_src.txt")
        model = whisper.load_model("base")
        result = model.transcribe(file_path,fp16=False)
        plain_text_result = result["text"] #write to file
        await write_plain_text(output_file_path_plain,plain_text_result)
        src_len_plain = get_len_text(plain_text_result)
        logger.info(f"Source text length is: {src_len_plain}")
        srt_writer = whisper.utils.get_writer("srt", download_path)
        #VTT writer etc
        srt_writer(result, output_file_path)
        logger.info("Getting Source Transcrpt completed")

async def get_translation(video_id: str,download_path: str, target_language:str="en"):
    file_path = os.path.join(download_path, f"{video_id}.mp3")
    logger.info(f"Getting Target EN Transcrpt: {video_id}")
    file_size = 0
    if os.path.exists(file_path):
        file_size = os.path.getsize(file_path)
    if 0< file_size < MAX_WHISPER_CONTENT_SIZE:
        output_file_path = os.path.join(download_path, f"{video_id}_trg.srt")
        output_file_path_plain = os.path.join(download_path, f"{video_id}_trg.txt")
        model = whisper.load_model("small")
        result = model.transcribe(file_path,fp16=False, task="translate")
        plain_text_result = result["text"]
        await write_plain_text(output_file_path_plain,plain_text_result)
        trg_len_plain = get_len_text(plain_text_result)
        logger.info(f"Target text length is: {trg_len_plain}")
        srt_writer = whisper.utils.get_writer("srt", download_path)
        srt_writer(result, output_file_path)
        logger.info("Getting Target Transcript completed")



async def download_video(video_id: str, download_path: str) -> int:
    """Dummy function for downloading the video (replace with actual implementation)"""
    video_url = extract_video_url(video_id)
    file_path = os.path.join(download_path, f"{video_id}.mp3")
    file_size = 0
    try: 
        os.path.exists(file_path)
        file_size = os.path.getsize(file_path)
        logger.info(f"File exists. File size: {file_size}")
        return file_size
    except FileNotFoundError:
        logger.info(f"Downloading video from: {video_url} to {download_path}")
        await download_best_audio_ytdl(video_url, download_path)
        file_size = os.path.getsize(file_path)
        logger.info(f"File size: {file_size}")
        logger.info("Downloading video completed")
        return file_size

async def split_video(video_id: str, download_path: str):
    file_path = os.path.join(download_path, f"{video_id}.mp3")
    file_size = 0
    if os.path.exists(file_path):
        file_size = os.path.getsize(file_path)
        good_file_size = MAX_WHISPER_CONTENT_SIZE- file_size
        logger.info(f"Split Video says this is a  GOOD file size: {good_file_size }")
    if good_file_size <0:
        logger.info(f"Splitting video: {video_id}")
        await asyncio.sleep(5)  # Pretend this is video splitting that takes time
        logger.info("Splitting video completed")
    else:
        logger.info(f"No need to split video: {video_id}")
        await asyncio.sleep(5)
    
async def get_pure_info(video_id: str, download_path: str):
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
        }],}
    video_url = extract_video_url(video_id)
    file_path = os.path.join(download_path, f"{video_id}.json")
    if os.path.exists(file_path):
       with open(file_path, 'r') as info_file:
           info = json.load(info_file)
           logger.info("Json file exists - loaded")
    else:
       with yt_dlp.YoutubeDL(ydl_opts) as ydl:
          info = ydl.extract_info(video_url, download=False)
       with open(file_path, 'w') as info_file:
           json.dump(info, info_file)
           logger.info("Created Json file - loaded")
    return info


async def check_and_create_tempdir(temp_dir: str = "temp"):
    """Dummy function for checking and creating tempdir"""
    os.makedirs(temp_dir, exist_ok=True)
    logger.info(f"Checking and creating tempdir: {temp_dir}")
    await asyncio.sleep(3)  # Use this to pretend this is simple IO operations
    logger.info("Tempdir created")


async def process_all_background_tasks(background_tasks: BackgroundTasks,youtube_id:str,user_dir:str):
    """Dummy function for processing all background tasks"""

    background_tasks.add_task(check_and_create_tempdir, user_dir)
    background_tasks.add_task(download_video, youtube_id,user_dir)
    background_tasks.add_task(split_video, youtube_id,user_dir)
    background_tasks.add_task(get_transcript, youtube_id,user_dir)
    background_tasks.add_task(get_translation, youtube_id,user_dir)
    # extras summarize translation -> from plain txt


# Start HERE 
@app.post("/process/", response_class=HTMLResponse)
async def process_all(background_tasks: BackgroundTasks, youtube_id: str):
    youtube_id = extract_youtube_id(youtube_id)
    video_url = extract_video_url(youtube_id)
    user_dir = './temp/tt'
    src_language= "unknown"
    video_duration = "unknown"
    info = None
    info = await get_pure_info(youtube_id, user_dir)
    if info:
        src_language = info['language']
        video_duration = str(info.get('duration', "0")) + " seconds"
        video_title = info['title'].upper()
        first_thumb = info['thumbnails'][0].get('url')
        tags = info['tags']
        html_tags = " ".join([f'<span style="color: {"red" if i % 2 == 0 else "blue"}; text-transform: uppercase;">{tag.upper()}</span>' for i, tag in enumerate(tags)])
    
    await process_all_background_tasks(background_tasks,youtube_id,user_dir) #add source language here
    

    common_html = (
        f"""
        <p>DEBUG Youtube ID: {youtube_id}, User Directory: {user_dir}</p>
        <p>Spoken language: {src_language}, Duration: {video_duration}</p>
        <h2> {video_title} </h2>
        <img src="{first_thumb}" alt="thumbnail" width="300" height="200">
        <div>{html_tags}</div>
        <div>
            <button onclick="getSourceTranscript('{youtube_id, user_dir}')" class="bg-blue-600 text-white px-4 py-2 rounded-md transition duration-300 ease-in-out hover:bg-green-700 mr-2">Source SRT </button>
            <button onclick="getTargetTranscript('{youtube_id, user_dir}')" class="bg-purple-600 text-white px-4 py-2 rounded-md transition duration-300 ease-in-out hover:bg-blue-700">Target (EN) SRT</button>
        </div>
            <div id="srcResult"></div>
            <div id="trgResult"></div>
         <script src="https://cdn.tailwindcss.com"></script>
        <script>
                    const youtube_id = '{youtube_id}';
                    const user_dir = '{user_dir}';

                function getSourceTranscript() {{
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
        """
    )
    return common_html