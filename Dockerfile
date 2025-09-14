FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV PORT=8080
# Use $PORT so we match whatever Cloud Run sets
CMD ["bash","-lc","exec gunicorn -b 0.0.0.0:${PORT} main:app"]
