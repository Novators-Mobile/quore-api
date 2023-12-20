FROM tiangolo/uvicorn-gunicorn-fastapi:python3.11

COPY . . 

RUN pip install --no-cache-dir --upgrade -r requirements.txt

ENV MAIL_USERNAME="BLANK"
ENV MAIL_PASSWORD="BLANK"
ENV MAIL_FROM="BLANK"
ENV MAIL_SERVER="BLANK"
ENV JWT_ACCESS_SECRET=${{ secrets.JWT_ACCESS_SECRET }}
ENV JWT_REFRESH_SECRET=${{ secrets.JWT_REFRESH_SECRET }}
ENV JWT_ALGORITHM=${{ secrets.JWT_ALGORITHM }}
ENV DB_SERVER=${{ secrets.DB_SERVER }}