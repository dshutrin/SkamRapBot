import requests
import vk_api
import config
import utils
from vk_api.longpoll import VkEventType, VkLongPoll
from models import *
from threading import Thread
from time import time
import urllib


class MyLongPoll(VkLongPoll):
	def listen(self):
		while True:
			try:
				for event in self.check():
					yield event
			except Exception as e:
				print(e)


class VkBot:
	def __init__(self):
		self.vk_session = vk_api.VkApi(token=config.token)
		self.longpoll = MyLongPoll(self.vk_session)
		self.clear_key = utils.get_vk_keyboard([])
		self.back_key = utils.get_vk_keyboard([[('Назад', 'красный')]])
		self.continue_key = utils.get_vk_keyboard([
			[('Пропустить', 'синий')],
			[('Назад', 'красный')]
		])
		self.adm_menu_key = utils.get_vk_keyboard([
			[('Добавить нарушителя', 'зеленый'), ('Удалить нарушителя', 'красный')],
			[('Добавить админа', 'зеленый'), ('Удалить админа', 'красный')],
			[('Создать пост рассылки', 'синий'), ('Посмотреть пост рассылки', 'синий')],
			[('Запустить рассылку', 'синий')],
			[('Проверить пользователя/сообщество', 'зеленый')]
		])
		self.sub_adm_menu_key = utils.get_vk_keyboard([
			[('Добавить нарушителя', 'синий'), ('Удалить нарушителя', 'синий')],
			[('Проверить пользователя/сообщество', 'зеленый')]
		])
		self.user_menu_key = utils.get_vk_keyboard([
			[('Проверить пользователя/сообщество', 'зеленый')],
			[('Сообщить о нарушителе', 'синий'), ('Сообщение администрации', 'синий')],
			[('Гарант', 'зеленый')]
		])
		self.confirm_key = utils.get_vk_keyboard([
			[('Подтвердить', 'зеленый')],
			[('Назад', 'красный')]
		])
		self.last_mail_send = 0

	def sender(self, user, msg, key):
		try:
			self.vk_session.method('messages.send', {'user_id': user.vk_id, 'message': msg, 'random_id': 0, 'keyboard': key})
		except:
			pass

	def mail_send(self, user, msg):
		try:
			self.vk_session.method('messages.send', {'user_id': user.vk_id, 'message': msg, 'random_id': 0})
		except:
			pass

	def upload_photo(self, path):
		up_server = self.vk_session.method("photos.getMessagesUploadServer")
		file = requests.post(up_server['upload_url'], files={'photo': open(path, 'rb')}).json()
		saved = self.vk_session.method('photos.saveMessagesPhoto',
								  {'photo': file['photo'], 'server': file['server'], 'hash': file['hash']})[0]
		return "photo{}_{}".format(saved["owner_id"], saved["id"])

	def main(self):
		for event in self.longpoll.listen():
			if event.type == VkEventType.MESSAGE_NEW:
				if event.to_me and not event.from_chat and not event.from_me:

					user = utils.get_user_by_vk_id(event.user_id)
					msg = event.text.lower()

					if msg == 'начать':
						if user.vk_id == config.admin_id:
							self.sender(user, 'Выберите одно из предложенных действий', self.adm_menu_key)
						elif user.vk_id in [x.vk_id for x in Admin().select()]:
							self.sender(user, 'Выберите одно из предложенных действий', self.sub_adm_menu_key)
						else:
							self.sender(user, 'Выберите одно из предложенных действий', self.user_menu_key)
						user.mode = 'start'

					if user.vk_id == config.admin_id:
						"""Главный админ"""
						if user.mode == 'start':

							if msg == 'добавить нарушителя':
								self.sender(user, 'Пришлите ссылку на пользователя/сообщество чтобы добавить его в чёрный список', self.back_key)
								user.mode = 'add_black_list'

							elif msg == 'удалить нарушителя':
								self.sender(user, 'Пришлите ссылку на пользователя/сообщество чтобы удалить его из чёрного списка', self.back_key)
								user.mode = 'del_black_list'

							elif msg == 'добавить админа':
								self.sender(user, 'Пришлите ссылку на пользователя/сообщество чтобы добавить его в список админов', self.back_key)
								user.mode = 'add_admin'

							elif msg == 'удалить админа':
								self.sender(user, 'Пришлите ссылку на пользователя/сообщество чтобы удалить его из списка админов', self.back_key)
								user.mode = 'del_admin'

							elif msg == 'создать пост рассылки':
								self.sender(user, 'Пришлите текст, который будет в рассылке', self.clear_key)
								user.mode = 'create_mail_text'

							elif msg == 'посмотреть пост рассылки':
								mail = [x for x in Mail().select()][0]
								self.vk_session.method('messages.send', {'user_id': user.vk_id, 'attachment': mail.photo_path, 'message': mail.text, 'random_id': 0})

							elif msg == 'запустить рассылку':
								if len([x for x in Mail().select()]) < 1:
									self.sender(user, 'Для запуска рассылки - создайте пост.', self.adm_menu_key)
								else:
									users = [x for x in User().select()]
									if (time() - self.last_mail_send) < (len(users) / 20):
										self.sender(user, 'Предыдущая рассылка еще не завершилась!', self.adm_menu_key)
									else:
										mail = [x for x in Mail().select()][0]
										Thread(target=utils.mail_sender, args=(self.vk_session, mail, users)).start()
										self.last_mail_send = time()

							elif msg == 'проверить пользователя/сообщество':
								self.sender(user, 'Пришлите ссылку на пользователя/сообщество или перешлите его сообщение.', self.back_key)
								user.mode = 'check'

						elif user.mode == 'add_black_list':

							if msg == 'назад':
								self.sender(user, 'Выберите действие', self.adm_menu_key)
								user.mode = 'start'

							else:
								from_id = utils.get_user_id_from_forwarded_message(self.vk_session, user, event)

								if not from_id:
									self.sender(user, 'Не удалось получить id пользователя/сообщества. Пришлите ссылку/сообщение заново.', self.back_key)
								else:
									if from_id in [x.vk_id for x in BlackList().select()]:
										self.sender(user, 'Пользователь/сообщество уже находится в чёрном списке!', self.adm_menu_key)
										user.mode = 'start'
									else:
										user.temp_id = from_id
										self.sender(
											user,
											'Пришлите ссылку на пост, с доказательствами, что пользователь/сообщество - нарушитель.',
											self.continue_key
										)
										user.mode = 'add_proofs'

						elif user.mode == 'del_black_list':

							if msg == 'назад':
								self.sender(user, 'Выберите действие', self.adm_menu_key)
								user.mode = 'start'

							else:
								from_id = utils.get_user_id_from_forwarded_message(self.vk_session, user, event)

								if not from_id:
									self.sender(user, 'Не удалось получить id пользователя/группы. Пришлите ссылку/сообщение заново.', self.back_key)
								else:
									if not (from_id in [x.vk_id for x in BlackList().select()]):
										self.sender(user, f'✅Пользователь не находится в чёрном списке!\n\nОднако полностью обезопасить вашу покупку вы сможете, используя гаранта.', self.adm_menu_key)
										user.mode = 'start'
									else:
										BlackList().get(vk_id=from_id).delete_instance()
										self.sender(user, 'Пользователь удалён из чёрного списка!', self.adm_menu_key)
									user.mode = 'start'

						elif user.mode == 'add_admin':

							if msg == 'назад':
								self.sender(user, 'Выберите действие', self.adm_menu_key)
								user.mode = 'start'

							else:
								from_id = utils.get_user_id_from_forwarded_message(self.vk_session, user, event)

								if not from_id:
									self.sender(user, 'Не удалось получить id пользователя.группы. Пришлите ссылку/сообщение заново.', self.back_key)
								else:
									if from_id in [x.vk_id for x in Admin.select()]:
										self.sender(user, 'Пользователь уже является админом!', self.adm_menu_key)
										user.mode = 'start'
									else:
										Admin(vk_id=from_id).save()
										self.sender(user, 'Пользователь назначен админом.', self.adm_menu_key)
										if from_id in [x.vk_id for x in User().select()]:
											self.sender(User().get(vk_id=from_id), 'Вы назначены админом бота.', self.sub_adm_menu_key)
										user.mode = 'start'

						elif user.mode == 'del_admin':

							if msg == 'назад':
								self.sender(user, 'Выберите действие', self.adm_menu_key)
								user.mode = 'start'

							else:
								from_id = utils.get_user_id_from_forwarded_message(self.vk_session, user, event)

								if not from_id:
									self.sender(
										user,
										'Не удалось получить id пользователя.группы. Пришлите ссылку/сообщение заново.',
										self.back_key
									)
								else:
									if not(from_id in [x.vk_id for x in Admin().select()]):
										self.sender(user, 'Пользователь не является админом!', self.adm_menu_key)
										user.mode = 'start'
									else:
										Admin().get(vk_id=from_id).delete_instance()
										self.sender(user, 'Пользователь больше не является админом.', self.adm_menu_key)
										user.mode = 'start'

						elif user.mode == 'add_proofs':

							if msg == 'назад':
								self.sender(user, 'Выберите действие', self.adm_menu_key)
								user.mode = 'start'

							else:
								if msg.startswith('https://') or msg.startswith('http://'):
									BlackList(vk_id=user.temp_id, comment=msg).save()
									self.sender(user, 'Пользователь добавлен в чёрный список!', self.adm_menu_key)
									user.mode = 'start'
								elif msg == 'пропустить':
									BlackList(vk_id=user.temp_id, comment='').save()
									self.sender(user, 'Пользователь добавлен в чёрный список!', self.adm_menu_key)
									user.mode = 'start'
								else:
									self.sender(user, 'Ссылка должна начинаться с https:// либо http:// !', self.back_key)

						elif user.mode == 'create_mail_text':
							mails = [x for x in Mail().select()]
							for mail in mails:
								mail.delete_instance()
							Mail(text=event.text, photo_path='').save()
							self.sender(user, 'Текст рассылки установлен.\nПришлите фото, которое будет в сообщении рассылки.', self.continue_key)
							user.mode = 'create_mail_photo'

						elif user.mode == 'create_mail_photo':
							if msg == 'пропустить':
								mails = [x for x in Mail().select()]
								mails[0].photo_path = ''
								mails[0].save()
								for mail in mails[1:]:
									mail.delete_instance()
								self.sender(user, 'Фотография для рассылки не установлена.\nПост рассылки создан!', self.adm_menu_key)
								user.mode = 'start'
							else:
								if len(event.attachments) > 0:
									if event.attachments['attach1_type'] == 'photo':

										msg_info = self.vk_session.method('messages.getById',
																		  {'message_ids': event.message_id})
										attach_info = msg_info['items'][0]['attachments'][0]['photo']['sizes'][-1]
										img_data = requests.get(attach_info['url']).content
										with open('mail_photo.jpg', 'wb') as handler:
											handler.write(img_data)

										mails = [x for x in Mail().select()]
										mails[0].photo_path = self.upload_photo('mail_photo.jpg')
										mails[0].save()
										for mail in mails[1:]:
											mail.delete_instance()
										self.sender(user, 'Фотография для рассылки успешно установлена.', self.adm_menu_key)
										user.mode = 'start'
									else:
										self.sender(user, 'Необходимо прислать фотографию.', self.clear_key)
								else:
									self.sender(user, 'Необходимо прислать фотографию.', self.clear_key)

						elif user.mode == 'check':
							if msg == 'назад':
								self.sender(user, 'Выберите действие', self.adm_menu_key)
								user.mode = 'start'

							else:
								from_id = utils.get_user_id_from_forwarded_message(self.vk_session, user, event)

								if not from_id:
									self.sender(
										user,
										'Не удалось получить id пользователя/сообщества.\nПроверьте правильность сообщения и повторите попытку.',
										self.back_key
									)

								else:
									checked_user = [x for x in BlackList().select() if x.vk_id == from_id]

									if len(checked_user) > 0:
										answer = '❗СКАМ❗\nПользователь/сообщество находится в чёрном списке, не рекомендуем совершать с ним сделку'
										if checked_user[0].comment != '':
											answer += f'\nДоказательства: {checked_user[0].comment}'
										self.sender(
											user,
											answer,
											self.sub_adm_menu_key
										)
									else:
										self.sender(
											user,
											f'✅Пользователь/сообщество не находится в чёрном списке. Можете совершать с ним сделку.\n\nОднако полностью обезопасить вашу покупку вы сможете, используя гаранта.',
											self.adm_menu_key
										)
									user.mode = 'start'

					elif user.vk_id in [x.vk_id for x in Admin().select()]:
						"""Админы, назначенные главным админом"""
						if user.mode == 'start':
							if msg == 'добавить нарушителя':
								self.sender(user, 'Пришлите ссылку на пользователя/сообщество чтобы добавить его в чёрный список', self.back_key)
								user.mode = 'add_black_list'

							elif msg == 'удалить нарушителя':
								self.sender(user, 'Пришлите ссылку на пользователя/сообщество чтобы удалить его из чёрного списка', self.back_key)
								user.mode = 'del_black_list'

							elif msg == 'проверить пользователя/сообщество':
								self.sender(user, 'Пришлите ссылку на пользователя/сообщество или перешлите его сообщение.', self.back_key)
								user.mode = 'check'

						elif user.mode == 'add_black_list':

							if msg == 'назад':
								self.sender(user, 'Выберите действие', self.sub_adm_menu_key)
								user.mode = 'start'

							else:
								from_id = utils.get_user_id_from_forwarded_message(self.vk_session, user, event)

								if not from_id:
									self.sender(user, 'Не удалось получить id пользователя/сообщество. Пришлите ссылку/сообщение заново.', self.back_key)
								else:
									if from_id in [x.vk_id for x in BlackList().select()]:
										self.sender(user, 'Пользователь/сообщество уже находится в чёрном списке!', self.sub_adm_menu_key)
										user.mode = 'start'
									else:
										user.temp_id = from_id
										self.sender(
											user,
											'Пришлите ссылку на пост, с доказательствами, что пользователь - нарушитель.',
											self.clear_key
										)
										user.mode = 'add_proofs'

						elif user.mode == 'add_proofs':

							if msg == 'назад':
								self.sender(user, 'Выберите действие', self.sub_adm_menu_key)
								user.mode = 'start'

							else:
								if msg.startswith('https://') or msg.startswith('http://'):
									BlackList(vk_id=user.temp_id, comment=msg).save()
									self.sender(user, 'Пользователь добавлен в чёрный список!', self.sub_adm_menu_key)
									user.mode = 'start'
								elif msg == 'пропустить':
									BlackList(vk_id=user.temp_id, comment='').save()
									self.sender(user, 'Пользователь/сообщество добавлен в чёрный список!', self.sub_adm_menu_key)
									user.mode = 'start'
								else:
									self.sender(user, 'Ссылка должна начинаться с https:// либо http:// !', self.back_key)

						elif user.mode == 'del_black_list':

							if msg == 'назад':
								self.sender(user, 'Выберите действие', self.sub_adm_menu_key)
								user.mode = 'start'

							else:
								from_id = utils.get_user_id_from_forwarded_message(self.vk_session, user, event)

								if not from_id:
									self.sender(user, 'Не удалось получить id пользователя/сообщество. Пришлите ссылку/сообщение заново.', self.back_key)
								else:
									if not (from_id in [x.vk_id for x in BlackList().select()]):
										self.sender(user, f'✅Пользователь/сообщество не находится в чёрном списке!\n\nОднако полностью обезопасить вашу покупку вы сможете, используя гаранта.', self.sub_adm_menu_key)
										user.mode = 'start'
									else:
										BlackList().get(vk_id=from_id).delete_instance()
										self.sender(user, 'Пользователь/сообщество удалён из чёрного списка!', self.sub_adm_menu_key)
									user.mode = 'start'

						elif user.mode == 'check':
							if msg == 'назад':
								self.sender(user, 'Выберите действие', self.sub_adm_menu_key)
								user.mode = 'start'

							else:
								from_id = utils.get_user_id_from_forwarded_message(self.vk_session, user, event)

								if not from_id:
									self.sender(
										user,
										'Не удалось получить id пользователя/сообщества.\nПроверьте правильность сообщения и повторите попытку.',
										self.back_key
									)

								else:
									checked_user = [x for x in BlackList().select() if x.vk_id == from_id]
									if len(checked_user) > 0:
										answer = '❗СКАМ❗\nПользователь/сообщество находится в чёрном списке, не рекомендуем совершать с ним сделку'
										if checked_user[0].comment != '':
											answer += f'\nДоказательства: {checked_user[0].comment}'
										self.sender(
											user,
											answer,
											self.sub_adm_menu_key
										)
									else:
										self.sender(
											user,
											f'✅Пользователь/сообщество не находится в чёрном списке. Можете совершать с ним сделку.\n\nОднако полностью обезопасить вашу покупку вы сможете, используя гаранта.',
											self.sub_adm_menu_key
										)
									user.mode = 'start'

					else:
						"""Простые пользователи"""
						if user.mode == 'start':

							if msg == 'проверить пользователя/сообщество':
								self.sender(
									user,
									'Пришлите ссылку на пользователя/сообщество или перешлите его сообщение.',
									self.back_key
								)
								user.mode = 'check'

							elif msg == 'сообщить о нарушителе':
								self.sender(
									user,
									'Пришлите ссылку на пользователя/сообщество или перешлите его сообщение.',
									self.back_key
								)
								user.mode = 'add_report'

							elif msg == 'сообщение администрации':
								self.sender(
									user,
									'Введите текст обращения',
									self.back_key
								)
								user.mode = 'add_message'

							elif msg == 'гарант':
								self.sender(
									user,
									'''Гарант - это человек, который сохранит ваши средства в безопасности от недобросовестных продавцов. Цена гаранта - 11% от суммы сделки (минимально - 100₽).\n
Как работает гарант?\n
1) Вы создаёте сделку с продавцом и гарантом\n
2) Вы вносите деньги гаранту\n
3) Гарант добавляет Заказчика и Исполнителя в беседу\n
4) Исполнитель обсуждает ожидаемый материал с Заказчиком\n
5) Заказчик проверяет качество услуги\n
6) После чего гарант переводит деньги за заказ исполнителю\n
В случае подозрения мошенничества продавца или покупателя, гарант разбирается в ситуации и возвращает деньги тому кто прав.\n
Продолжая, вы подтверждаете вашу способность и желание оплатить заказ в течение 24-х часов.''',
									self.confirm_key
								)
								user.mode = 'confirm_guarantee'

						elif user.mode == 'check':
							if msg == 'назад':
								self.sender(user, 'Выберите действие', self.user_menu_key)
								user.mode = 'start'

							else:
								from_id = utils.get_user_id_from_forwarded_message(self.vk_session, user, event)

								if not from_id:
									self.sender(
										user,
										'Не удалось получить id пользователя/сообщества.\nПроверьте правильность сообщения и повторите попытку.',
										self.back_key
									)

								else:
									checked_user = [x for x in BlackList().select() if x.vk_id == from_id]
									if len(checked_user) > 0:
										self.sender(
											user,
											f'❗СКАМ❗\nПользователь/сообщество находится в чёрном списке, не рекомендуем совершать с ним сделку\nДоказательства: {checked_user[0].comment}',
											self.user_menu_key
										)
									else:
										self.sender(
											user,
											f'✅Пользователь/сообщество не находится в чёрном списке. Можете совершать с ним сделку.\n\nОднако полностью обезопасить вашу покупку вы сможете, используя гаранта.',
											self.user_menu_key
										)
									user.mode = 'start'

						elif user.mode == 'add_report':

							if msg == 'назад':
								self.sender(user, 'Выберите действие', self.user_menu_key)
								user.mode = 'start'

							else:

								from_id = utils.get_user_id_from_forwarded_message(self.vk_session, user, event)

								if not from_id:
									self.sender(
										user,
										'Не удалось получить id пользователя/сообщества.\nПроверьте правильность сообщения и повторите попытку.',
										self.back_key
									)

								else:
									utils.send_for_admins(self.mail_send, f'Пользователь @id{user.vk_id} хочет пожаловаться на {event.text}')
									self.sender(user, 'Ваш запрос отправлен администраторам.\nОжидайте ответа.', self.user_menu_key)
									user.mode = 'start'

						elif user.mode == 'add_message':
							if msg == 'назад':
								self.sender(user, 'Выберите действие', self.user_menu_key)
								user.mode = 'start'

							else:
								utils.send_for_admins(self.mail_send, f'Сообщение от @id{user.vk_id}: {event.text}')
								self.sender(
									user,
									'Ваш запрос отправлен администраторам.\nОжидайте ответа.',
									self.user_menu_key
								)
								user.mode = 'start'

						elif user.mode == 'confirm_guarantee':
							if msg == 'назад':
								self.sender(user, 'Выберите действие', self.user_menu_key)
								user.mode = 'start'

							elif msg == 'подтвердить':
								utils.send_for_admins(self.mail_send, f'Пользователь @id{user.vk_id} хочет заказать гаранта!')
								self.sender(user, 'Запрос отправлен администраторам.\nОжидайте ответа.', self.user_menu_key)
								user.mode = 'start'

					user.save()


if __name__ == '__main__':
	VkBot().main()
