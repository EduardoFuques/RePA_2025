FROM python:3.13-slim

RUN apt-get update && apt-get upgrade -y && apt-get install -y --no-install-recommends curl && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir --retries 5 --timeout 120 --upgrade pip wheel

WORKDIR /code

COPY ./requirements.txt /code/requirements.txt

RUN pip install --no-cache-dir --retries 5 --timeout 120 --upgrade -r /code/requirements.txt

COPY ./src /code/src

# Alembic (fuente de verdad del esquema): se aplica `upgrade head` en el arranque
COPY ./alembic /code/alembic
COPY ./alembic.ini /code/alembic.ini

ENTRYPOINT ["uvicorn"]
CMD ["src.main:app", "--host", "0.0.0.0", "--port", "80"]
