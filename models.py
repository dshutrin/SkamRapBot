from peewee import *


db = SqliteDatabase('data.db')


class User(Model):
	class Meta:
		database = db
		db_table = 'Users'
	vk_id = IntegerField()
	mode = CharField(max_length=50)
	temp_id = IntegerField(default=-10)


class BlackList(Model):
	class Meta:
		database = db
		db_table = 'BlackList'
	vk_id = IntegerField()
	comment = TextField()


class Admin(Model):
	class Meta:
		database = db
		db_table = 'Admins'
	vk_id = IntegerField()


class Mail(Model):
	class Meta:
		database = db
	text = TextField()
	photo_path = TextField()


if __name__ == '__main__':
	db.create_tables([BlackList, User, Admin, Mail])
