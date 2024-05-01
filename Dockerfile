FROM python:3.12-slim

RUN pip install pymongo

COPY . /app

WORKDIR /app

EXPOSE 3000
EXPOSE 5000

CMD ["python", "main.py"]
