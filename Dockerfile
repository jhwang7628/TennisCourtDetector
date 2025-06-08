FROM pytorch/pytorch:2.0.1-cuda11.7-cudnn8-runtime

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 4) Copy your inference code
COPY src/ ./src/

# 5) Default entrypoint: adjust path/args to match your code
ENTRYPOINT ["python", "-u", "src/infer.py"]
