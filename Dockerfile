# ── Stage 1: Build ──
FROM python:3.12-slim AS builder

RUN apt-get update && apt-get install -y --no-install-recommends \
    wget gnupg unzip curl xvfb ca-certificates \
    && wget -q -O - https://dl.google.com/linux/linux_signing_key.pub | gpg --dearmor > /usr/share/keyrings/chrome-key.gpg \
    && echo "deb [signed-by=/usr/share/keyrings/chrome-key.gpg] http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google-chrome.list \
    && apt-get update \
    && apt-get install -y --no-install-recommends google-chrome-stable \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# ── Stage 2: Runtime (slim) ──
FROM python:3.12-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    wget gnupg unzip curl xvfb ca-certificates \
    && wget -q -O - https://dl.google.com/linux/linux_signing_key.pub | gpg --dearmor > /usr/share/keyrings/chrome-key.gpg \
    && echo "deb [signed-by=/usr/share/keyrings/chrome-key.gpg] http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google-chrome.list \
    && apt-get update \
    && apt-get install -y --no-install-recommends google-chrome-stable \
    && rm -rf /var/lib/apt/lists/* \
    && rm -rf /opt/google/chrome/swiftshader /opt/google/chrome/libswiftshader* \
    && rm -rf /usr/lib/x86_64-linux-gnu/libswiftshader*

COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

WORKDIR /app
COPY . .

ENV PORT=5000 HOST=0.0.0.0
EXPOSE 5000
CMD ["python", "webapp.py"]
