FROM apache/airflow:2.10.0

COPY docker_requirements.txt .
RUN pip install --no-cache-dir -r docker_requirements.txt