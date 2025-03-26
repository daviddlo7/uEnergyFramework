FROM python:3.9-slim

WORKDIR /app/src/energycollector

COPY requirements.in .
RUN pip install -r requirements.in

COPY . .

EXPOSE 50051 8000

ENV PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION=python

ENTRYPOINT ["python", "-m", "service.__main__"]