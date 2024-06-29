FROM python:3.12-slim

WORKDIR /app

ADD https://astral.sh/uv/install.sh install.sh
RUN chmod +x install.sh
RUN install.sh && rm install.sh

COPY requirements.txt .
RUN /root/.cargo/bin/uv python -m venv .venv
RUN /app/.venv/bin/playwright install

RUN /root/.cargo/bin/uv pip install --no-cache -r requirements.txt

COPY main.py .
CMD [ "python", "main.py" ]