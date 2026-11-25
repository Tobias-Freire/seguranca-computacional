FROM debian:12-slim

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        openssh-client sshpass netcat-openbsd ca-certificates hydra \
        python3 python3-paramiko python3-yaml \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /attack
CMD ["sleep", "infinity"]
