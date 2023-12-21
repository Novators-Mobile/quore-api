FROM tiangolo/uvicorn-gunicorn-fastapi:python3.11

COPY . . 

RUN pip install --no-cache-dir --upgrade -r requirements.txt

ENV MAIL_USERNAME="BLANK"
ENV MAIL_PASSWORD="BLANK"
ENV MAIL_FROM="BLANK"
ENV MAIL_SERVER="BLANK"
ENV JWT_ACCESS_SECRET = jwt_access_secret
ENV JWT_REFRESH_SECRET = jwt_refresh_secret
ENV JWT_ALGORITHM = jwt_algorithm
ENV DB_SERVER = db_server