FROM python:3.12-slim-bookworm

RUN apt-get update && apt-get install -y --no-install-recommends chromium chromium-driver \
    && rm -rf /var/lib/apt/lists/*
WORKDIR /app
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
COPY app.py browser_runtime.py sbsolver_parser.py sbsolver_import.py oed_parser.py ./
ENV CHROMIUM_BINARY=/usr/bin/chromium \
    CHROMEDRIVER_BINARY=/usr/bin/chromedriver \
    HOOS_HEADLESS=1 \
    PYTHONUNBUFFERED=1
EXPOSE 10000
CMD ["sh", "-c", "exec streamlit run app.py --server.address=0.0.0.0 --server.port=${PORT:-10000} --server.headless=true"]
