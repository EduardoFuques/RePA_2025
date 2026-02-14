FROM python:3.10-slim

RUN apt-get update && apt-get install -y --no-install-recommends curl && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir --upgrade pip

WORKDIR /code

COPY ./requirements.txt /code/requirements.txt

RUN pip install --no-cache-dir --upgrade -r /code/requirements.txt

COPY ./src /code/src

ENTRYPOINT ["uvicorn"]
CMD ["src.main:app", "--reload", "--host", "0.0.0.0", "--port", "80"]
