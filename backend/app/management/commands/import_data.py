from django.core.management.base import BaseCommand, CommandParser
from app.models import Ingredient


class Command(BaseCommand):
    """
    Класс для импорта данных из csv файлов.
    Пока реализовано только для модели Ingredient
    """
    help = 'Importing data from csv files to table'

    def handle(self, *args, **options):
        filename = options.get('filename', None)
        tablename = options.get('tablename', None)
        if filename and tablename:
            # Пока сделаем по простому
            if tablename[0] == 'ingredient':
                f = open(filename[0], 'r')
                for line in f:
                    values = line.split(',')
                    data = {
                        'name': values[0],
                        'measurement_unit': values[1].replace('\n', '')
                    }
                    Ingredient.objects.get_or_create(
                        **data
                    )
                f.close()
                print('done')

    def add_arguments(self, parser: CommandParser) -> None:
        parser.add_argument(
            '-f',
            '--filename',
            default=False,
            help='path to *.csv file',
            type=str,
            nargs=1,
        )
        parser.add_argument(
            '-t',
            '--tablename',
            default=False,
            help='table name',
            type=str,
            nargs=1,
        )
