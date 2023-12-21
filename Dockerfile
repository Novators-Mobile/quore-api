FROM tiangolo/uvicorn-gunicorn-fastapi:python3.11

COPY . . 

RUN pip install --no-cache-dir --upgrade -r requirements.txt

ENV MAIL_USERNAME="BLANK"
ENV MAIL_PASSWORD="BLANK"
ENV MAIL_FROM="BLANK"
ENV MAIL_SERVER="BLANK"