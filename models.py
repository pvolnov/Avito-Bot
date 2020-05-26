from peewee import *
from playhouse.postgres_ext import PostgresqlExtDatabase, ArrayField

from config import bdname, bduser, bdpassword, bdport, bdhost

db = PostgresqlExtDatabase(bdname, user=bduser, password=bdpassword,
                           host=bdhost, port=bdport)


class Items(Model):
    item_id = IntegerField()
    url = TextField(default="")
    name = TextField(default="")
    cost = IntegerField()
    discr = TextField(default="")
    image = TextField(default="")
    address = TextField(default="")
    author_id = BigIntegerField(default=-1)
    scam = BooleanField(default=False)
    status = IntegerField(default=0)

    class Meta:
        database = db


class Authors(Model):
    author_id = BigIntegerField(unique=True)
    name = TextField()
    status = IntegerField(default=1)
    comment = TextField(default="")

    class Meta:
        database = db


class Users(Model):
    tel_id = BigIntegerField(unique=True)
    name = TextField()
    status = IntegerField(default=1)
    bought = ArrayField(default=[])
    writen = ArrayField(default=[])

    class Meta:
        database = db


# db.drop_tables([IkeaItems, Tasks])
# db.drop_tables([Items, Authors, Users])
# db.create_tables([Items, Authors, Users])
