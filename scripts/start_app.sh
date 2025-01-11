#!/usr/bin/bash 

# Modify the settings.py file to update allowed hosts dynamically
sed -i 's/\[]/\["18.188.42.21"]/' /home/ubuntu/EcommerceApplication-Python/EcommerceApplication/settings.py

if [ ! -d /mnt/ebs/gunicorn ]; then
    echo "Creating /mnt/ebs/gunicorn directory..."
    sudo mkdir -p /mnt/ebs/gunicorn
    sudo chown www-data:www-data /mnt/ebs/gunicorn
    sudo chmod 775 /mnt/ebs/gunicorn
else
    echo "/mnt/ebs/gunicorn already exists."
fi


# Apply database migrations
python manage.py migrate 

# Make migrations if needed
python manage.py makemigrations     

# Collect static files (no input to auto-approve)
python manage.py collectstatic --noinput

# Restart Gunicorn service (gracefully)
echo "Restarting Gunicorn..."
sudo systemctl restart gunicorn

# Wait until Gunicorn is up and running before restarting Nginx
echo "Waiting for Gunicorn to start..."
sleep 5

# Restart Nginx service
echo "Restarting Nginx..."
sudo systemctl restart nginx

# Check if Gunicorn and Nginx are active (optional but recommended)
if ! systemctl is-active --quiet gunicorn; then
  echo "Gunicorn failed to start!"
  exit 1
fi

if ! systemctl is-active --quiet nginx; then
  echo "Nginx failed to restart!"
  exit 1
fi

echo "Application started successfully!"
