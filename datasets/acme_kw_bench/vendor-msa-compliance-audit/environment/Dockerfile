FROM ubuntu:22.04

RUN apt-get update && apt-get install -y --no-install-recommends \
    python3 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /workspace
COPY contracts/ /workspace/contracts/
COPY playbooks/ /workspace/playbooks/
