FROM python:3.9-slim-buster

WORKDIR /app

COPY ./website/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY ./website /app

EXPOSE 5000
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "2", "--log-level", "debug", "app:app"]