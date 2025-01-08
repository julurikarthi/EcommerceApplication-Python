#!/usr/bin/bash

set -e  # Exit immediately if a command exits with a non-zero status
set -u  # Treat unset variables as an error and exit immediately

# Variables
APP_DIR="/home/ubuntu/EcommerceApplication-Python/EcommerceApplication"
SETTINGS_FILE="$APP_DIR/settings.py"
GUNICORN_SOCKET_DIR="/run/gunicorn"
GUNICORN_SERVICE="gunicorn"
NGINX_SERVICE="nginx"
ALLOWED_HOST="3.16.168.145"

# Update allowed hosts in settings.py
echo "Updating ALLOWED_HOSTS in settings.py..."
sed -i "s/\[]/\[\"$ALLOWED_HOST\"]/" "$SETTINGS_FILE"

# Apply database migrations
echo "Applying database migrations..."
python "$APP_DIR/manage.py" migrate

# Make migrations if needed
echo "Checking for database migrations..."
python "$APP_DIR/manage.py" makemigrations

# Collect static files (no input to auto-approve)
echo "Collecting static files..."
python "$APP_DIR/manage.py" collectstatic --noinput

# Ensure the Gunicorn socket directory exists
if [ ! -d "$GUNICORN_SOCKET_DIR" ]; then
  echo "Creating Gunicorn socket directory..."
  sudo mkdir -p "$GUNICORN_SOCKET_DIR"
  sudo chown www-data:www-data "$GUNICORN_SOCKET_DIR"
  sudo chmod 775 "$GUNICORN_SOCKET_DIR"
else
  echo "Gunicorn socket directory already exists."
fi

# Restart Gunicorn service
echo "Restarting Gunicorn service..."
sudo systemctl restart "$GUNICORN_SERVICE"

# Wait until Gunicorn is up and running
echo "Waiting for Gunicorn to start..."
sleep 5

# Check if Gunicorn is active
if ! systemctl is-active --quiet "$GUNICORN_SERVICE"; then
  echo "Gunicorn failed to start!"
  exit 1
fi

# Restart Nginx service
echo "Restarting Nginx service..."
sudo systemctl restart "$NGINX_SERVICE"

# Check if Nginx is active
if ! systemctl is-active --quiet "$NGINX_SERVICE"; then
  echo "Nginx failed to restart!"
  exit 1
fi

echo "Application started successfully!"
