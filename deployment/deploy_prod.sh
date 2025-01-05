#!/bin/sh

ssh root@3.16.168.145 <<EOF
  cd EcommerceApplication-Python
  git pull 
  source env/bin/activate
  ./manage.py migrate
  sudo systemctl restart nginx
  sudo service gunicorn restart
  sudo service nginx restart
  exit
EOF