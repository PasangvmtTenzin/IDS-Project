#!/bin/bash

echo "--------------------------------------------------------------------"
echo "Network Setup Script for IDS-Project"
echo "--------------------------------------------------------------------"
echo ""
echo "INFO: Docker Compose will handle the creation of the 'ids_net' bridge network."
echo "This script is primarily for informational purposes or future extensions."
echo ""

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
  echo "ERROR: Docker does not seem to be running. Please start Docker and try again."
  exit 1
fi

# Check if Docker Compose is installed
if ! command -v docker-compose &> /dev/null; then
  echo "ERROR: docker-compose could not be found. Please install Docker Compose."
  exit 1
fi

echo "INFO: The 'ids_net' network will be created automatically when you run 'docker-compose up'."
echo "You can inspect it after startup with 'docker network inspect ids-project_ids_net'."
echo ""
echo "INFO: Suricata in the 'ids' container is configured to listen on 'eth0',"
echo "which will be its interface on the 'ids_net' network."
echo ""
echo "INFO: Ensure your host firewall is not blocking traffic on port 8080 if you want to access the webserver from your browser."
echo ""
echo "To start the environment: docker-compose up -d --build"
echo "To stop the environment: docker-compose down"
echo ""
echo "--------------------------------------------------------------------"