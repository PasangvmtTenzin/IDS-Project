# IDS Project Demonstration

This project demonstrates a simple Intrusion Detection System (IDS) setup using Docker, Docker Compose, Nginx (webserver), and Suricata (IDS). An attacker container is included to simulate basic attacks.

## Project Structure

The project is organized as follows:

```plaintext
IDS-Project/
├── docker-compose.yml          # Defines and configures all services
├── Dockerfiles/                # Contains Dockerfile definitions for each service
│   ├── app.Dockerfile          # Builds the Flask application image
│   ├── attacker.Dockerfile     # Builds the attacker simulation image
│   ├── ids.Dockerfile          # Builds the Suricata IDS image
│   └── webserver.Dockerfile    # Builds the Nginx webserver image
├── configs/                    # Configuration files for services
│   ├── database/
│   │   └── init.sql            # Schema for the PostgreSQL database
│   ├── dns/                    # BIND9 DNS server configurations
│   │   ├── Dockerfile          # Builds the BIND9 DNS server image
│   │   ├── named.conf
│   │   ├── named.conf.local
│   │   ├── named.conf.options
│   │   └── zones/
│   │       ├── csn.local.db    # Forward lookup zone for 'csn.local'
│   │       └── db.172.20       # Reverse lookup zone for 172.20.x.x
│   ├── ids/                    # Suricata specific configurations
│   │   ├── suricata.yaml       # Main Suricata engine configuration
│   │   └── local.rules         # Custom rules for Suricata (if any)
│   └── webserver/              # Nginx specific configurations
│       └── default.conf        # Nginx virtual host configuration
├── website/                    # Flask application code and static content
│   ├── app.py                  # Main Flask application file
│   ├── requirements.txt        # Python dependencies
│   ├── static/                 # Static assets (CSS, JS, images)
│   └── templates/              # HTML templates for Flask
├── attacks/                    # Scripts to simulate network attacks
│   ├── port_scan.sh            # Simulates a port scan
│   └── sql_injection.sh        # Simulates basic SQL injection attempts
├── scripts/                    # Utility and helper scripts (if any)
│   └── setup_network.sh        # (Potentially outdated, review if needed)
├── logs/                       # Mount point for service logs
│   ├── bind/                   # BIND9 DNS server logs
│   │   └── .gitkeep
│   └── suricata/               # Suricata IDS logs (eve.json, etc.)
│       └── .gitkeep
└── README.md                   # This file: project overview, setup, and usage instructions
```

## Prerequisites

*   Docker: [Install Docker](https://docs.docker.com/get-docker/)
*   Docker Compose: [Install Docker Compose](https://docs.docker.com/compose/install/) (Often included with Docker Desktop)

## Setup and Running

1.  **Clone the repository (if applicable) or create the files as listed.**
    Ensure all directories and files match the structure above. Pay special attention to the ./configs/dns/ directory and its contents.

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
    ```
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


## Troubleshooting
    If you see #!/bin/bash^M$: The ^M is the carriage return. This is the problem.
    
    1. Using a Text Editor (Recommended - e.g., VS Code, Notepad++, Sublime Text):
        Open C:\Users\HP\IDS-Project\attacks\port_scan.sh in your text editor.
        Look at the status bar at the bottom. It usually indicates the line ending type (it will likely say "CRLF").
        Click on "CRLF" (or find the relevant menu option like "Edit" -> "EOL Conversion" or "View" -> "Line Endings").
        Select "LF" (Unix/Linux style).
        Save the file.
        Do the same for sql_injection.sh.

    2. Using dos2unix (if you have Git Bash or WSL on Windows):
        Open Git Bash or a WSL terminal.
        Navigate to your project directory: cd /c/Users/HP/IDS-Project/attacks (path might vary slightly for WSL).
        Run:
        ```bash
        dos2unix port_scan.sh
        dos2unix sql_injection.sh
        Use code with caution.
        ```
        This command will convert the files in place.