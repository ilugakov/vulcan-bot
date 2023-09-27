FROM python:3.11-alpine

ENV PYTHONUNBUFFERED=1

WORKDIR /app
RUN mkdir -p ./creds
COPY . .
RUN pip install -r requirements.txt

RUN apk add --no-cache tzdata
ENV TZ=Europe/Warsaw

WORKDIR /app/src
CMD ["python", "app.py"]