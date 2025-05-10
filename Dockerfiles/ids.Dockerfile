FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && \
    apt-get install -y software-properties-common curl gnupg && \
    add-apt-repository -y ppa:oisf/suricata-stable && \
    apt-get update && \
    apt-get install -y suricata suricata-update tcpdump iproute2 procps && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Create suricata user and group (if not already created by package)
RUN groupadd -r suricata && useradd -r -g suricata -s /sbin/nologin -c "Suricata IDS" suricata || true

# Create necessary directories and set permissions
RUN mkdir -p /var/log/suricata /etc/suricata/rules && \
    chown -R suricata:suricata /var/log/suricata /etc/suricata

# Copy custom configuration. Rules will be part of the config mount.
COPY ./configs/ids/suricata.yaml /etc/suricata/suricata.yaml
# We will create a local.rules file in configs/ids/ and suricata.yaml will reference it.

# Download some basic rules (optional, can be done via suricata-update)
# RUN suricata-update --no-emerging-threats # Avoids ET Pro subscription issues
# Or, for a minimal set to get started, copy local.rules

# The command will be specified in docker-compose.yml
# CMD ["suricata", "-c", "/etc/suricata/suricata.yaml", "-i", "eth0"]