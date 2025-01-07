#!/usr/bin/bash

echo "Pull Finished"

# Reload systemd to reflect any changes in services
sudo systemctl daemon-reload

# Check if Gunicorn is running
if ! systemctl is-active --quiet gunicorn; then
  echo "Gunicorn is not running, starting Gunicorn..."
  sudo systemctl start gunicorn
else
  echo "Gunicorn is already running."
fi

# Gracefully reload Nginx
echo "Reloading Nginx..."
sudo systemctl reload nginx

# Check Nginx status
if ! systemctl is-active --quiet nginx; then
  echo "Nginx failed to reload!"
  exit 1
fi

echo "After install completed successfully!"
