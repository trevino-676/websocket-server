FROM python:3.9-alpine
LABEL mainteiner="drumbot"
WORKDIR /usr/src/app
ENV TZ=America/Mexico_City
RUN apk add --no-cache g++ make libffi-dev
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE 6789
CMD ["python", "notification_websocket_server.py"]