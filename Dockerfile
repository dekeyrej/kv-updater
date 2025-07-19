#Builder stage
FROM python:3.12-slim AS builder
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
COPY requirements.txt .
RUN . /opt/venv/bin/activate
RUN pip install -r requirements.txt
#Operational stage
FROM python:3.12-slim
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH" \
    PYTHONUNBUFFERED=1 
WORKDIR /code
COPY config.py .
COPY kv-updater.py .
EXPOSE 10255
ENV APP=kv-updater.py
CMD ["sh", "-c", "python /code/${APP}"]