
#!/usr/bin/bash

sudo systemctl daemon-reload
sudo rm -f /etc/nginx/sites-enabled/default

sudo cp /home/ubuntu/EcommerceApplication-Python/nginx/nginx.conf /etc/nginx/sites-available/EcommerceApplication
sudo ln -s /etc/nginx/sites-available/EcommerceApplication /etc/nginx/sites-enabled/
#sudo ln -s /etc/nginx/sites-available/EcommerceApplication /etc/nginx/sites-enabled
#sudo nginx -t
sudo gpasswd -a www-data ubuntu
sudo systemctl restart nginx

