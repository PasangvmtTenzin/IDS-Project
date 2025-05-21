FROM ubuntu:22.04

LABEL maintainer="Your Name <you@example.com>"

# Install BIND9 and utilities
RUN apt-get update && \
    apt-get install -y bind9 bind9utils bind9-doc dnsutils vim && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Create necessary directories for BIND's runtime data and logs
# BIND runs as user 'bind' (or '_named' on some systems, 'bind' on Debian/Ubuntu)
RUN mkdir -p /var/cache/bind /var/lib/bind /var/log/bind && \
    chown -R bind:bind /var/cache/bind /var/lib/bind /var/log/bind && \
    chmod -R 775 /var/cache/bind /var/lib/bind /var/log/bind

# Copy BIND configuration files from the host into the image
COPY named.conf /etc/bind/named.conf
COPY named.conf.options /etc/bind/named.conf.options
COPY named.conf.local /etc/bind/named.conf.local
COPY zones/ /etc/bind/zones/

# Ensure correct ownership and permissions for zone files
RUN chown -R bind:bind /etc/bind/zones && \
    find /etc/bind/zones -type f -exec chmod 644 {} \; && \
    find /etc/bind/zones -type d -exec chmod 755 {} \;

# Validate configuration (optional, but good practice)
# RUN named-checkconf /etc/bind/named.conf
# RUN named-checkzone csn.local /etc/bind/zones/csn.local.db
# RUN named-checkzone 20.172.in-addr.arpa /etc/bind/zones/db.172.20

EXPOSE 53/udp
EXPOSE 53/tcp

# Start BIND in the foreground, running as user 'bind'
# The -g option runs named in the foreground.
# The -u bind option specifies the user to run as.
# The sh -c allows us to run checks before exec
CMD ["sh", "-c", "named-checkconf /etc/bind/named.conf && named-checkconf -z /etc/bind/named.conf && exec named -g -c /etc/bind/named.conf -u bind"]