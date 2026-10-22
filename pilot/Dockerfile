FROM python:3.12-slim-bookworm

RUN apt-get update && apt-get install -y --no-install-recommends chromium chromium-driver \
    && rm -rf /var/lib/apt/lists/*
WORKDIR /app
RUN pip install --no-cache-dir selenium==4.39.0
COPY sbsolver_parser.py browser_runtime.py ./
COPY pilot ./pilot
ENV CHROMIUM_BINARY=/usr/bin/chromium CHROMEDRIVER_BINARY=/usr/bin/chromedriver
ENTRYPOINT ["python", "-m", "pilot.probe"]
