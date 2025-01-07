#!/usr/bin/bash

# Copy gunicorn.socket and gunicorn.service to systemd directories
echo "Copying gunicorn configuration files..."
if sudo cp /home/ubuntu/EcommerceApplication-Python/gunicorn/gunicorn.socket /etc/systemd/system/gunicorn.socket &&
   sudo cp /home/ubuntu/EcommerceApplication-Python/gunicorn/gunicorn.service /etc/systemd/system/gunicorn.service; then
    echo "Gunicorn configuration files copied successfully."
else
    echo "Error: Failed to copy Gunicorn configuration files." >&2
    exit 1
fi

# Reload systemd to reflect the new service configurations
echo "Reloading systemd daemon..."
if sudo systemctl daemon-reload; then
    echo "Systemd daemon reloaded successfully."
else
    echo "Error: Failed to reload systemd daemon." >&2
    exit 1
fi

# Start the Gunicorn service
echo "Starting Gunicorn service..."
if sudo systemctl start gunicorn.service; then
    echo "Gunicorn service started successfully."
else
    echo "Error: Failed to start Gunicorn service." >&2
    exit 1
fi

# Enable the Gunicorn service to start on boot
echo "Enabling Gunicorn service to start on boot..."
if sudo systemctl enable gunicorn.service; then
    echo "Gunicorn service enabled successfully."
else
    echo "Error: Failed to enable Gunicorn service." >&2
    exit 1
fi

# Check Gunicorn status
if sudo systemctl is-active --quiet gunicorn.service; then
    echo "Gunicorn service is running."
else
    echo "Error: Gunicorn service is not running." >&2
    exit 1
fi

echo "Gunicorn setup completed successfully!"
