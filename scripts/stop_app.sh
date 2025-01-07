#!/usr/bin/env bash

# Step 1: Stop Gunicorn service
echo "Stopping Gunicorn service..."
sudo systemctl stop gunicorn.service || { echo "Error: Failed to stop Gunicorn service"; exit 1; }

# Step 2: Stop Nginx service
echo "Stopping Nginx service..."
sudo systemctl stop nginx || { echo "Error: Failed to stop Nginx service"; exit 1; }

echo "Application stopped successfully!"
