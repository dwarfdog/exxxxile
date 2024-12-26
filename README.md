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

pip3.7 install django psycopg2-binary django-precise-bbcode

3/ INSTALL EXXXXILE

git clone https://github.com/badj62/exxxxile.git

cd exxxxile

cp pyxile/settings.py.example pyxile/settings.py

4/ CREATE A DATABASE IN POSTGRESQL AND A USER OWNING IT

5/ EDIT clean_dump.sql TO REPLACE ALL OWNER 'exxxxile' BY YOUR DB USER

6/ IMPORT THE SQL DUMP

psql -d [db_name] -f clean_dump.sql

7/ SET CONFIG

Edit pyxile/settings.py.example to set correct values (secret key, db access, etc.)

8/ RUNSERVER (FOR DEV) OR WSGI

python3.7 manage.py runserver

9/ INFINITE LOOP RUN COMMANDS (nohup, screen OR ADD A PYTHON SCHEDULER MODULE):

python3.7 manage.py sp_process_all

python3.7 manage.py update_player

python3.7 manage.py sp_battle

python3.7 manage.py sp_events

