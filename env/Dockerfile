# Reference container for the execution side (Defects4J 3.0.1 + Java 11).
# NOT used for the reported runs: the host has no Docker, and runs use the WSL2 environment recorded in
# env/environment_manifest.json (deviation X-04). Provided so the execution stage can be reproduced elsewhere.
FROM ubuntu:22.04
ENV DEBIAN_FRONTEND=noninteractive TZ=America/Los_Angeles LANG=C.UTF-8
RUN apt-get update && apt-get install -y --no-install-recommends \
      openjdk-11-jdk git subversion perl cpanminus curl unzip build-essential python3 ca-certificates \
    && rm -rf /var/lib/apt/lists/*
RUN git clone --branch v3.0.1 --depth 1 https://github.com/rjust/defects4j.git /opt/defects4j \
    && cd /opt/defects4j && cpanm --installdeps . && ./init.sh
ENV PATH=/opt/defects4j/framework/bin:$PATH D4J_HOME=/opt/defects4j TRIAGE_WORK=/work
WORKDIR /project
# usage: docker run -v "$PWD":/project img python3 scripts/run_execution.py --workers 6
