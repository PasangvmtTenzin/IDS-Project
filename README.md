# IDS Project Demonstration

This project demonstrates a simple Intrusion Detection System (IDS) setup using Docker, Docker Compose, Nginx (webserver), and Suricata (IDS). An attacker container is included to simulate basic attacks.

## Project Structure

The project is organized as follows:

```plaintext
IDS-Project/
├── docker-compose.yml          # Defines and configures all services (webserver, ids, attacker)
├── Dockerfiles/                # Contains Dockerfile definitions for each service
│   ├── webserver.Dockerfile    # Builds the Nginx webserver image
│   ├── ids.Dockerfile          # Builds the Suricata IDS image
│   └── attacker.Dockerfile     # Builds the attacker simulation image
├── configs/                    # Configuration files for services
│   ├── ids/                    # Suricata specific configurations
│   │   ├── suricata.yaml       # Main Suricata engine configuration
│   │   └── local.rules         # Custom rules for Suricata to detect specific threats
│   ├── webserver/              # Nginx specific configurations
│   │   └── default.conf        # Nginx virtual host configuration for the webserver
│   └── database/               # Placeholder for database related files (not actively used)
│       └── init.sql            # Example SQL schema (not used by core functionality)
├── website/                    # Static content for the webserver
│   └── index.html              # Simple HTML page served by Nginx
├── attacks/                    # Scripts to simulate network attacks
│   ├── port_scan.sh          # Simulates a port scan using nmap and ping
│   └── sql_injection.sh      # Simulates basic SQL injection attempts via curl
├── scripts/                    # Utility and helper scripts
│   └── setup_network.sh      # Informational script describing the Docker network setup
├── logs/                       # Mount point for Suricata logs (generated during runtime)
│   └── .gitkeep                # Ensures the 'logs' directory is tracked by Git
└── README.md                   # This file: project overview, setup, and usage instructions

```

## Prerequisites

*   Docker: [Install Docker](https://docs.docker.com/get-docker/)
*   Docker Compose: [Install Docker Compose](https://docs.docker.com/compose/install/) (Often included with Docker Desktop)

## Setup and Running

1.  **Clone the repository (if applicable) or create the files as listed.**

2.  **Make attack scripts executable:**
    ```bash
    chmod +x attacks/port_scan.sh
    chmod +x attacks/sql_injection.sh
    chmod +x scripts/setup_network.sh
    ```

3.  **Build and start the containers:**
    Open a terminal in the `IDS-Project` directory and run:
    ```bash
    docker-compose up -d --build
    ```
    The `-d` flag runs the containers in detached mode. `--build` forces a rebuild of the images.

4.  **Verify containers are running:**
    ```bash
    docker-compose ps
    ```
    You should see `ids-webserver`, `ids-suricata`, and `ids-attacker` running.

# Testing the Setup

1.  **Access the Webserver:**
    Open your browser and go to `http://localhost:8080`. You should see the "Welcome to the Simple Web Server!" page.
    This traffic should be logged by Suricata (e.g., the "HTTP Traffic to Webserver" rule).

2.  **Run a Port Scan from the Attacker:**
    Get into Attacker shell:
    ```
    docker exec -it ìds-attacker /bin/bash
    ``
    Execute the port scan script inside the attacker container:
    ```bash
    docker-compose exec attacker bash /attacks/port_scan.sh
        OR
    ./port_scan.sh
    ```
    This will run `nmap` against the `webserver` container.

3.  **Simulate an SQL Injection Attack:**
    Execute the SQL injection script inside the attacker container:
    ```bash
    docker-compose exec attacker bash /attacks/sql_injection.sh
        OR
    ./sql_injection.sh
    ```
    This will use `curl` to send HTTP requests with SQL injection patterns to the webserver.

4.  **Check IDS Logs:**
    Suricata logs events to the `./logs/` directory on your host machine. The most detailed log is `eve.json`.
    You can monitor it in real-time:
    ```bash
    tail -f logs/eve.json
    ```
    Or, if you prefer, view the logs from the `ids` container:
    ```bash
    docker-compose logs -f ids
    ```
    Look for alerts corresponding to "ICMP Ping Detected", "Potential Nmap Scan Activity", "SQL Injection Attempt", etc. Each event in `eve.json` is a JSON object. You can use tools like `jq` to parse it:
    ```bash
    # Example: Show only alert messages
    tail -f logs/eve.json | jq -r 'select(.event_type=="alert") | .alert.signature'
    ```

5.  **Interactive Attacker Shell (Optional):**
    If you want to run commands manually from the attacker container:
    ```bash
    docker-compose exec attacker bash
    ```
    Inside this shell, you can run commands like:
    ```bash
    ping webserver
    curl webserver
    nmap -sT webserver
    # (navigate to /attacks and run scripts manually if preferred)
    ```

## Stopping the Environment

To stop and remove the containers, networks, and volumes (if defined as anonymous):
```bash
docker-compose down


---

With all these files in place, you should have a working IDS demonstration environment!
Remember to:
1.  Create all directories.
2.  Place the files in their respective locations.
3.  Make the `.sh` scripts executable (`chmod +x *.sh` in the relevant directories).
4.  Run `docker-compose up -d --build`.
