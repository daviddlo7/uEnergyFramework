FROM python:3.10-slim

WORKDIR /app/src

COPY src/analytics/requirements.in .
RUN pip install -r requirements.in

COPY src/analytics/ .

EXPOSE 50051

ENV PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION=python

ENTRYPOINT ["python", "-m", "service.__main__"]
