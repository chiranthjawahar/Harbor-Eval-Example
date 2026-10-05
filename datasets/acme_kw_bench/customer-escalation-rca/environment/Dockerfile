FROM ubuntu:22.04

RUN apt-get update && apt-get install -y --no-install-recommends \
    python3 \
    sqlite3 \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /workspace
COPY data/seed_support.sql /tmp/seed_support.sql
RUN mkdir -p /workspace/data && sqlite3 /workspace/data/support_tickets.db < /tmp/seed_support.sql && rm /tmp/seed_support.sql
COPY postmortems/ /workspace/postmortems/
