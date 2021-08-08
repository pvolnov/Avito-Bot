from peewee import *
from playhouse.sqliteq import SqliteQueueDatabase

db = SqliteQueueDatabase('db.sqlite3',
                         use_gevent=False,  # Use the standard library "threading" module.
                         autostart=False,  # The worker thread now must be started manually.
                         queue_max_size=64)
ALAMER = "df548f-61ac83-624ea4"


class Items(Model):
    item_id = IntegerField()
    cost = IntegerField()

    class Meta:
        database = db


db.start()
db.connect()
# db.drop_tables([Items])
# db.create_tables([Items])
# db.stop()