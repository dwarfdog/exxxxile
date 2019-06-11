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
                    cursor.execute('SELECT sp_execute_processes()')
                    end = datetime.datetime.now()
                    #print('end ' + str(end.microsecond))
                    #print()
                    time.sleep(0.02)
