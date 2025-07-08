FROM pytorch/pytorch:2.0.1-cuda11.7-cudnn8-runtime

WORKDIR /app

# Install OpenCV runtime dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
      libgl1-mesa-glx \
      libglib2.0-0 && \
    rm -rf /var/lib/apt/lists/*
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install --no-cache-dir awscli

COPY src/ ./src/
RUN gdown https://drive.google.com/uc?id=1U3-PyvElqLbZUD_NsVgwRtK4s1HIh5n6 -O /app/model.pt

ENTRYPOINT [ "bash", "-lc" ]
CMD ["python", "-u", "src/infer_in_image.py"]
