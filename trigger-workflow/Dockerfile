# 1. Base Image: Alpine (approx. 50MB total)
FROM python:3.11-alpine

# 2. Env Vars: faster startup, no .pyc files, logs show immediately
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# 3. Work Directory
WORKDIR /app

# 4. Install Deps: copy requirements first to cache dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 5. Copy Code
COPY . .

# 6. Security: Create a non-root user and switch to it
RUN adduser -D appuser
USER appuser

# 7. Run
ENTRYPOINT ["python", "main.py"]