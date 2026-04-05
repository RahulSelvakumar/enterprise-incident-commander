FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the entire project root into the container
COPY . .

# Run Uvicorn directly out of the server directory module
CMD ["uvicorn", "server.app:app", "--host", "0.0.0.0", "--port", "7860"]