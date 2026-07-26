FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# The agent needs to write to /var/log/servitor — this dir is overridden by
# a bind mount in production so logs persist on the host.
RUN mkdir -p /var/log/servitor

EXPOSE 8420

CMD ["python", "main.py"]
