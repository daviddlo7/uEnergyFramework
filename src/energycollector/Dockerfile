FROM python:3.10-slim

WORKDIR /app/src

COPY src/energycollector/requirements.in .
RUN pip install -r requirements.in

COPY src/energycollector/ .

COPY src/analytics/analytics_pb2.py /app/src/
COPY src/analytics/analytics_pb2_grpc.py /app/src/

COPY Files /app/Files

EXPOSE 50051

ENV PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION=python

ENTRYPOINT ["python", "-m", "service.__main__"]
