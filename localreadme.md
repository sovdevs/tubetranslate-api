/Users/derzessionar/prog/chatgpt/py/tubetranslate-app/.venv/bin/python3 -m uvicorn main:app --port 8004 --reload

# DEplouying

https://www.koyeb.com/docs/deploy/fastapi


git push -u origin main 

# deploys to 
https://tubetranslate-api-sovdevs.koyeb.app/info

https://www.koyeb.com/docs/deploy/fastapi

# fgaster transcriber SOON when can write SRT
https://github.com/sanchit-gandhi/whisper-jax


# OPEN AI SRT 

https://wandb.ai/wandb_fc/gentle-intros/reports/How-to-Transcribe-Your-Audio-to-Text-for-Free-with-SRTs-VTTs---VmlldzozNDczNTI0#saving-a-whisper-transcription-as-an-srt/vtt-file

Zoesugar 2m17 secs and timeout 
kNXVFB5eQfo exceeds size
https://gist.github.com/markshust/e9d772664492c5cb76a6fde032abc090

# 16 JULY

issues with import writer to write transcript to SRT file 

ALT is to do a batch sweep of files, creare transcripts, translate and throw a callback for pickup

Wait for faster version whisper-jax
which will anyway allow for write

temporary fix...

Looka at using a different venv

linux/amd64
docker buildx build --platform linux/amd64
ffmpeg-6.0.tar.gz   

RUN apt-get update && apt-get install -y ffmpeg
apt-get update && apt-get install -y ffmpeg
# MON 17

try docker container with ppmpeg
https://fastapi.tiangolo.com/deployment/docker/
deplpy thayt way

https://community.koyeb.com/t/file-not-found-when-copy-in-docker-file/544

## install package
pipenv install pytube 

# 20 JULY
Issue with this is that well too big these files and local site cannot process them

What about Netlify?

cron endpoint being tested

/info endpoint => info2 endpoint just download the file and set up some sort of callback or return html first


# RUN from 20 JULY
pipenv shell
export DEPLOYMENT_VERSION=dev
uvicorn main:app --port 8004 --reload 
(tubetranslate-api) √ tubetranslate-api % uvicorn main:app --port 8004 --reload 

# Open Insomnia or docs
export DEPLOYMENT_VERSION=dev


Instead of this return a callback to download actual file
which will be 2 buttons getSRT getVTT

No deliver as is to get correct HTML to 
Then consider callback

+randomcode+iD.transcript_src.mp3

downloaded shithead pSEwy1-WZJk tt

Improvements
dies not ewaut for file to finish ✅ <p>Task completed: &#x2705;</p>
first call returns information including how long to suspend button


## STRT UP
pipenv shell
(tubetranslate-api) √ tubetranslate-api % pipenv install loguru
# RUN
uvicorn main:app --port 8004 --reload

# venv 
python3.11 -m venv .venv2 
source .venv2/bin/activate
(.venv) √ tubetranslate-api % /Users/derzessionar/prog/chatgpt/py/tubetranslate-api/.venv2/bin/python3.11 -m uvicorn main:app --port 8004 --reload

# troubelshooter

AttributeError: module 'whisper' has no attribute 'load_model'
