#!/usr/bin/bash

# Reload systemd to ensure changes are recognized
echo "Reloading systemd daemon..."
sudo systemctl daemon-reload || { echo "Error: Failed to reload systemd"; exit 1; }

# Remove default site configuration (if exists)
echo "Removing default site configuration..."
sudo rm -f /etc/nginx/sites-enabled/default || { echo "Error: Failed to remove default site configuration"; exit 1; }

# Copy the custom Nginx configuration for the application
echo "Copying custom nginx configuration..."
- sudo rm -rf /etc/nginx/sites-enabled/EcommerceApplication
sudo cp /home/ubuntu/EcommerceApplication-Python/nginx/nginx.conf /etc/nginx/sites-available/EcommerceApplication || { echo "Error: Failed to copy nginx.conf"; exit 1; }
echo "successfully copied nignx"

# Create a symbolic link to enable the site
echo "Creating symbolic link for the site..."
sudo ln -s /etc/nginx/sites-available/EcommerceApplication /etc/nginx/sites-enabled/ || { echo "Error: Failed to create symlink"; exit 1; }

# Adding user to the www-data group (this might be necessary for permissions)
echo "Adding ubuntu user to www-data group..."
sudo gpasswd -a www-data ubuntu || { echo "Error: Failed to add user to www-data group"; exit 1; }

# Test Nginx configuration for syntax errors
echo "Testing Nginx configuration..."
sudo nginx -t || { echo "Error: Nginx configuration test failed"; exit 1; }

# Restart Nginx to apply changes
echo "Restarting Nginx..."
sudo systemctl restart nginx || { echo "Error: Failed to restart nginx"; exit 1; }

echo "Nginx configuration updated and restarted successfully!"
