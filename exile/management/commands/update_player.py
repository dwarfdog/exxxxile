import time, datetime
from django.core.management.base import BaseCommand, CommandError
from django.db import connection

class Command(BaseCommand):
    help = 'Closes the specified poll for voting'

    #def add_arguments(self, parser):
    #    parser.add_argument('poll_ids', nargs='+', type=int)

    def handle(self, *args, **options):
        now = datetime.datetime.now()
        h = now.timetuple().tm_hour
        print('hour=' + str(h))
        with connection.cursor() as cursor:
            cursor.execute('SELECT id FROM users WHERE privilege >= 0 AND planets > 0 AND credits_bankruptcy > 0 AND lastlogin IS NOT NULL ORDER BY id')
            res = cursor.fetchall()
            for re in res:
                print(re)
                start = datetime.datetime.now()
                print('start')
                print(start.microsecond)
                try:
                    cursor.execute('SELECT sp_update_player(%s,%s)', [re[0], h])
                except (KeyError, Exception):
                    print(KeyError)
                    print(Exception)
                    cursor.execute('select * from users_chats where userid=2 and chatid=3')
                    row = cursor.fetchone()
                    if not row:
                        cursor.execute('insert into users_chats (userid,chatid,password) values (2,3,\'\')')
                    cursor.execute('insert into chat_lines (chatid,message,login,allianceid,userid) values (3,\'ALERT : sp_update_player is down ! Les mise à jour Joueur (crédits, entretiens) sont stoppés.\',\'Watchdog\',null,2)');
                    exit()
                end = datetime.datetime.now()
                print('end')
                print(end.microsecond)
        self.stdout.write(self.style.SUCCESS('Successfully called'))