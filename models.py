from peewee import *
from playhouse.sqliteq import SqliteQueueDatabase

db = SqliteQueueDatabase('db.sqlite3',
                         use_gevent=False,  # Use the standard library "threading" module.
                         autostart=False,  # The worker thread now must be started manually.
                         queue_max_size=64)
ALAMER = "df548f-61ac83-624ea4"


class Items(Model):
    name = TextField()
    discr = TextField(default="")
    new = BooleanField(default=True)
    photo = TextField()
    url = TextField(unique=True)
    cost = IntegerField()

    message_url = TextField(default="")
    response = BooleanField(default=False)
    surveillance = BooleanField(default=False)
    update_order = IntegerField(default=1)

    class Meta:
        database = db


class Tasks(Model):
    name = TextField()
    url = TextField()
    model = TextField()
    params = TextField()
    max_cost = IntegerField()
    mes_cost = IntegerField()
    min_cost = IntegerField()
    message_text = TextField()

    class Meta:
        database = db


db.start()
db.connect()
# db.drop_tables([Tasks,Items])
# db.create_tables([Tasks,Items])
# db.stop()