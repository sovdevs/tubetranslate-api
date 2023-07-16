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