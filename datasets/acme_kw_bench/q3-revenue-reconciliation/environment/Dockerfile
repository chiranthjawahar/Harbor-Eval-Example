# ANTI-PATTERN IN v1_flawed: Unpinned base image tag (:latest)
FROM ubuntu:latest

RUN apt-get update && apt-get install -y --no-install-recommends \
    python3 \
    python3-pip \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /workspace
COPY data/ /workspace/data/
COPY docs/ /workspace/docs/
