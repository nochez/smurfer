FROM python:3.9.9-slim

WORKDIR /usr/src/app

COPY requirements.txt ./
RUN apt-get update
RUN apt-get install autoconf automake build-essential libtool python3-dev jq -y
RUN pip install --upgrade pip setuptools wheel

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD [ "python", "./main.py"  ]
