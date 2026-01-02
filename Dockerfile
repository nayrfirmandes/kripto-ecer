FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY prisma ./prisma
COPY bot ./bot
COPY run_bot.py .
COPY .env .env

# Generate Prisma Python client
RUN prisma generate --schema=prisma/schema.prisma

EXPOSE 8080

CMD ["python", "run_bot.py"]
