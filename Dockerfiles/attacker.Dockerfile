# Use the official Kali Linux rolling image
FROM kalilinux/kali-rolling

# Set DEBIAN_FRONTEND to noninteractive to prevent apt-get from prompting
ENV DEBIAN_FRONTEND=noninteractive

# Update package lists and install necessary tools
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    nmap \
    curl \
    bash \
    net-tools \
    iputils-ping \ 
    # For ping, traceroute etc.
    iproute2 \     
    # For 'ip' command, preferred over ifconfig
    python3 \
    python3-pip \
    git \          
    # Good to have for an attacker shell
    # You can add other common Kali tools here if needed, e.g.:
    # dnsutils (for dig, nslookup)
    # procps (for ps, top etc. - usually present but good to be sure)
    # sudo (if you plan to create a non-root user later)
    # nano or vim (a text editor)
    && apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Install sqlmap using pip
# The --break-system-packages flag is needed on newer Debian/Kali
# systems if pip is installing to system-wide locations.
RUN pip3 install sqlmap --break-system-packages

# Create work directory for attacks
WORKDIR /attacks
# Ensure this directory exists in your build context (next to your Dockerfile)
# For example, create an empty 'attacks' directory: mkdir attacks
COPY ./attacks /attacks

# Default command to keep container running for exec
# You will typically use 'docker exec -it <container_name> bash' to get a shell
CMD ["tail", "-f", "/dev/null"]