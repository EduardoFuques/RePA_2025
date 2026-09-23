FROM python:3.14-slim

RUN apt-get update && apt-get upgrade -y && apt-get install -y --no-install-recommends curl && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir --retries 5 --timeout 120 --upgrade pip wheel

WORKDIR /code

COPY ./requirements.txt /code/requirements.txt

RUN pip install --no-cache-dir --retries 5 --timeout 120 --upgrade -r /code/requirements.txt

COPY ./src /code/src

# La version que reporta /docs. La pasa docker-publish.yml como build-arg con
# el tag de git; en un build local queda "dev", que es lo que corresponde.
#
# Va DESPUES de instalar las dependencias a proposito: cambia en cada
# release, y si estuviera arriba invalidaria el cache de la capa de pip en
# cada build — que es justamente la capa cara (254s medidos).
ARG APP_VERSION=dev
ENV APP_VERSION=${APP_VERSION}

# Alembic (fuente de verdad del esquema): se aplica `upgrade head` en el arranque
COPY ./alembic /code/alembic
COPY ./alembic.ini /code/alembic.ini

ENTRYPOINT ["uvicorn"]
CMD ["src.main:app", "--host", "0.0.0.0", "--port", "80"]
