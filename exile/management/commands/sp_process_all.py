import time, datetime
from django.core.management.base import BaseCommand, CommandError
from django.db import connection

class Command(BaseCommand):
    help = 'Closes the specified poll for voting'

    #def add_arguments(self, parser):
    #    parser.add_argument('poll_ids', nargs='+', type=int)

    def handle(self, *args, **options):
        with connection.cursor() as cursor:
            while True:
                print('loop '+str(datetime.datetime.now()))
                for i in range(5000):
                    start = datetime.datetime.now()
                    #print('start ' + str(start.microsecond))
                    try:
                        cursor.execute('SELECT sp_execute_processes()')
                    except (KeyError, Exception):
                        print(KeyError)
                        print(Exception)
                        cursor.execute('select * from users_chats where userid=2 and chatid=3')
                        row = cursor.fetchone()
                        if not row:
                            cursor.execute('insert into users_chats (userid,chatid,password) values (2,3,\'\')')
                        cursor.execute('insert into chat_lines (chatid,message,login,allianceid,userid) values (3,\'ALERT : sp_execute_processes is down ! Les processes sont stoppés.\',\'Watchdog\',null,2)');
                        exit()
                    end = datetime.datetime.now()
                    #print('end ' + str(end.microsecond))
                    #print()
                    time.sleep(0.02)
