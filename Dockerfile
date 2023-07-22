FROM python:3.11

WORKDIR /code

COPY ./requirements.txt /code/requirements.txt
RUN apt-get update && apt-get install -y ffmpeg
RUN pip install --no-cache-dir --upgrade -r /code/requirements.txt
RUN mkdir temp
RUN mkdir temp/tt
EXPOSE 8004

COPY ./main.py /code/
# Run the app
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8004"]
