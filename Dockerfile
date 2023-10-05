FROM alpine

ENV BaseDir=/app

RUN mkdir -p $BaseDir

WORKDIR $BaseDir

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

RUN apk add --update --no-cache python3 \
 && ln -sf python3 /usr/bin/python \
 && python3 -m ensurepip

ADD ./NewEmergmed $BaseDir/NewEmergmed
ADD ./requirements.txt $BaseDir

RUN apk add --update --no-cache pkgconfig \
 && apk add --update --no-cache --virtual build-deps gcc python3-dev musl-dev \
 && apk add --update --no-cache mariadb-dev mariadb-connector-c-dev \
 && pip3 install --no-cache --upgrade pip setuptools \
 && pip3 install -r requirements.txt \
 && pip3 cache purge \
 && apk del --rdepends --purge pkgconfig build-deps gcc python3-dev musl-dev mariadb-dev

EXPOSE 8000

WORKDIR $BaseDir/NewEmergmed

ADD entrypoint.sh .

CMD ${BaseDir}/NewEmergmed/entrypoint.sh
