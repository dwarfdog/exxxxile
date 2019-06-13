# exxxxile
rewrite exile.fr in python/django

1/ INSTALL PYTHON3.7 (at least)
apt-get install build-essential checkinstall

apt-get install libreadline-gplv2-dev libncursesw5-dev libssl-dev libsqlite3-dev tk-dev libgdbm-dev libc6-dev libbz2-dev libffi-dev zlib1g-dev

cd /usr/src/

wget https://www.python.org/ftp/python/3.7.3/Python-3.7.3.tgz

tar xzf Python-3.7.3.tgz

cd Python-3.7.3

./configure --enable-optimizations

make altinstall

python3.7 --version

pip3.7 -V

pip3.7 list

2/ INSTALL DJANGO AND OTHERS

pip3.7 install django psycopg2-binary django-precise-bbcode bfa

3/ INSTALL EXXXXILE

git clone https://github.com/badj62/exxxxile.git

cd exxxxile

cp pyxile/settings.py.example pyxile/settings.py

Edit settings.py.example to set correct values (secret key, db access, etc.)
