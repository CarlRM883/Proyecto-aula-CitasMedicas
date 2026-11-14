FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY sistema_real ./sistema_real
CMD ["uvicorn", "sistema_real.main:app", "--host", "0.0.0.0", "--port", "8000"]
