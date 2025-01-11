#!/bin/sh

ssh root@18.188.42.21 <<EOF
  cd EcommerceApplication-Python
  git pull 
  source env/bin/activate
  ./manage.py migrate
  sudo systemctl restart nginx
  sudo service gunicorn restart
  sudo service nginx restart
  exit
EOF