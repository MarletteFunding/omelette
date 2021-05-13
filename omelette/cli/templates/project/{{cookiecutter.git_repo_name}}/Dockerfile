FROM public.ecr.aws/h1a5s9h8/python:3.8-slim-buster
RUN apt-get update && apt-get install -y git curl
RUN useradd -m -U -G staff -s /sbin/nologin etl
WORKDIR /home/etl/

ENV POETRY_HOME="/opt/poetry"

RUN curl -sSL https://raw.githubusercontent.com/python-poetry/poetry/master/get-poetry.py | python
ENV PATH="$POETRY_HOME/bin:$VENV_PATH/bin:$PATH"
ENV PYTHONPATH="$PYTHONPATH:src"

COPY pyproject.toml poetry.lock ./
RUN poetry export -f requirements.txt -o requirements.txt --without-hashes &&\
  pip install -r requirements.txt

COPY ./src ./src
COPY ./tests ./tests

RUN chown -R etl:etl /home/etl/
USER etl

CMD [ "python", "--version" ]
