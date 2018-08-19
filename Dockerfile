FROM python:3-alpine

WORKDIR /usr/src/app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY aa5robot.py .

CMD [ "python", "-u", "./aa5robot.py" ]
