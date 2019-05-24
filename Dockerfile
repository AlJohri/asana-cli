FROM python:3

ADD . /asana/
ADD asana_cli/ /asana/asana_cli/
RUN cd asana && make install

WORKDIR /asana
ENTRYPOINT [ "pipenv", "run", "asana" ]
#CMD [ "pipenv", "run", "asana" ]
