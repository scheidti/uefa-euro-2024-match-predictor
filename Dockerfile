FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
RUN python -m playwright install 
RUN python -m playwright install-deps

COPY main.py .
CMD [ "python", "main.py" ]