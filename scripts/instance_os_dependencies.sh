#!/usr/bin/env bash

# Update package list to ensure the system is up-to-date
echo "Updating package list..."
sudo apt update -y || { echo "Error: Failed to update package list"; exit 1; }

# Install python3-pip
echo "Installing python3-pip..."
sudo apt install -y python3-pip || { echo "Error: Failed to install python3-pip"; exit 1; }

# Install nginx
echo "Installing nginx..."
sudo apt install -y nginx || { echo "Error: Failed to install nginx"; exit 1; }

# Install virtualenv
echo "Installing virtualenv..."
sudo apt install -y virtualenv || { echo "Error: Failed to install virtualenv"; exit 1; }

# Verify installations
echo "Verifying installations..."

# Check python3-pip installation
if command -v pip3 > /dev/null 2>&1; then
    echo "python3-pip installed successfully."
else
    echo "Error: python3-pip installation failed." >&2
    exit 1
fi

# Check nginx installation
if command -v nginx > /dev/null 2>&1; then
    echo "nginx installed successfully."
else
    echo "Error: nginx installation failed." >&2
    exit 1
fi

# Check virtualenv installation
if command -v virtualenv > /dev/null 2>&1; then
    echo "virtualenv installed successfully."
else
    echo "Error: virtualenv installation failed." >&2
    exit 1
fi

echo "All dependencies installed successfully!"
