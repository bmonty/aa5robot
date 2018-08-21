FROM python:3-alpine

WORKDIR /usr/src/app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY aa5robot.py .
COPY command/ .

CMD [ "python", "./aa5robot.py" ]
