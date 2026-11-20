FROM python:3.13-slim

WORKDIR /srv
COPY server.py personas.py ./
RUN useradd --system --no-create-home mockuser
USER mockuser

EXPOSE 8700

HEALTHCHECK --interval=15s --timeout=3s --start-period=5s \
    CMD ["python", "-c", "import urllib.request,sys; sys.exit(0 if urllib.request.urlopen('http://127.0.0.1:8700/healthz', timeout=2).status == 200 else 1)"]

CMD ["python", "server.py"]
