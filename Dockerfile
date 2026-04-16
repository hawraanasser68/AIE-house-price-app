# Use Python 3.11
FROM python:3.11-slim

# Set working directory to the root folder where the code is
WORKDIR /app/root

# Copy requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the entire project
COPY . .

# Expose ports for FastAPI and Streamlit
EXPOSE 8000 8501

# Command to run both services
# Railway will expose the service on $PORT, so Streamlit must use that port.
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port 8000 & streamlit run streamlit_app.py --server.port $PORT --server.address 0.0.0.0 & wait"]