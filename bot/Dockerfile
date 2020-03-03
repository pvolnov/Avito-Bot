FROM ubuntu:18.04
MAINTAINER Andrey Maksimov 'maksimov.andrei@gmail.com'

RUN apt-get update && apt-get install -y build-essential git libjpeg-dev
RUN apt-get install -y vim

# get wget
RUN apt-get install wget

# install python 3.7
RUN apt-get install -y software-properties-common
RUN add-apt-repository -y ppa:fkrull/deadsnakes
RUN apt-get -y update
RUN apt-get -y install python3.7

RUN wget https://bootstrap.pypa.io/get-pip.py
RUN python3.7 get-pip.py
COPY . /app
WORKDIR /app
RUN python3.7 -m pip install -r requirements.txt
ENTRYPOINT ['python']
CMD ['bot.py']