FROM python:3.12-slim

# Send stdout and stderr straight through, so docker logs shows the
# Flask output immediately instead of holding it in a buffer.
ENV PYTHONUNBUFFERED=1
# Do not litter the image with .pyc files
ENV PYTHONDONTWRITEBYTECODE=1

WORKDIR /app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY app.py ./

# Run as an unprivileged user rather than root.
# Port 5000 is above 1024, so no special privilege is needed to bind it.
RUN useradd --create-home appuser
USER appuser

EXPOSE 5000
CMD ["python", "app.py"]
