FROM python:3.11-slim-bookworm

COPY src /src

WORKDIR /src

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

CMD ["python","-u" ,"server.py"]