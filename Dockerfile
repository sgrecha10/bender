FROM python:3.10.1-bullseye

ENV PYTHONUNBUFFERED=1 \
   LANG=ru_RU.UTF-8 \
   LANGUAGE=ru_RU:ru \
   LC_ALL=ru_RU.UTF-8 \
   DEBUG=true \
   TERM=xterm-256color

WORKDIR /app

COPY requirements.txt /app/requirements.txt

RUN apt-get update && \
  apt-get install -y --no-install-recommends gcc git libssl-dev g++ make && \
  cd /tmp && git clone https://github.com/edenhill/librdkafka && \
  cd librdkafka && git checkout tags/v2.0.2 && \
  ./configure && make && make install && \
  ldconfig &&\
  cd ../ && rm -rf librdkafka
RUN python -m pip install --upgrade pip
RUN pip install -r /app/requirements.txt --no-cache-dir
