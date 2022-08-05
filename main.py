import time

import vk_api
import config
import models
import utils
from vk_api.longpoll import VkEventType, VkLongPoll
from models import *


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
		self.complete_key = utils.get_vk_keyboard([[('Подтвердить', 'зеленый')], [('Назад', 'красный')]])
		self.menu_key = utils.get_vk_keyboard([
			[('Проверить продавца', 'зеленый')],
			[('Сообщить о продавце', 'синий'), ('Написать администрации', 'синий')],
			[('Гарант', 'зеленый')]
		])

	def sender(self, user_id, msg, key):
		self.vk_session.method('messages.send', {'user_id': user_id, 'message': msg, 'random_id': 0, 'keyboard': key})

	def main(self):
		for event in self.longpoll.listen():
			if event.type == VkEventType.MESSAGE_NEW:
				if event.to_me and not event.from_chat and not event.from_me:

					user = utils.get_user_by_vk_id(event.user_id)
					msg = event.text.lower()

					if msg == 'начать':
						self.sender(user.vk_id, 'Выберите одно из предложенных действий', self.menu_key)
						user.mode = 'start'

					else:
						if user.mode == 'start':
							if msg == 'проверить продавца':
								self.sender(user.vk_id, 'Пришлите ссылку на продавца либо перешлите его сообщение', self.back_key)
								user.mode = 'check'

							elif msg == 'сообщить о продавце':
								self.sender(config.admin_id, f'Пользователь @id{user.vk_id} хочет пожаловаться на продавца!', self.clear_key)
								self.sender(user.vk_id, 'Администратор скоро свяжется с вами!', self.menu_key)

							elif msg == 'написать администрации':
								self.sender(user.vk_id, 'Введите текст обращения', self.back_key)
								user.mode = 'input_msg_for_admins'

							elif msg == 'гарант':
								self.sender(
									user.vk_id,
									'Нажимая кнопку "Подтвердить" - вы подтверждаете, что хотите создать сделку.',
									self.complete_key
								)
								user.mode = 'confirm_guarantee'

						elif user.mode == 'check':
							if msg == 'назад':
								self.sender(user.vk_id, 'Выберите одно из предложенных действий', self.menu_key)

							else:

								msg_info = self.vk_session.method('messages.getById', {'message_ids': event.message_id})
								from_id = None

								try:
									count = len(msg_info['items'][0]['fwd_messages'])

									if count > 0:
										from_id = [x['from_id'] for x in msg_info['items'][0]['fwd_messages'] if x['from_id'] != user.vk_id][0]
									elif msg.startswith('https://vk.com/'):
										screen_name = msg.replace('https://vk.com/', '').strip()
										from_id = self.vk_session.method('users.get', {'user_ids': [screen_name]})[0]['id']
									else:
										self.sender(
											user.vk_id,
											'Не удалось получить id пользователя!\nПришлите ссылку на продавца либо перешлите его сообщение',
											self.back_key
										)
										from_id = None

									if from_id:
										q = [x for x in BlackList().select() if x.vk_id == from_id]
										if len(q) > 0:
											self.sender(
												user.vk_id,
												'Пользователь находится в чёрном списке, настоятельно не рекомендуем совершать сделки с ним!',
												self.menu_key
											)
										else:
											self.sender(
												user.vk_id,
												'Пользователь не находится в чёрном списке, можете совершать с ним сделку!\nНе смотря на то, \
												что пользователь не находится в чёрном списке, рекомендуем быть бдительным!'.replace('\t', ''),
												self.menu_key
											)

								except Exception as e:
									print(e)
									self.sender(
										user.vk_id,
										'Не удалось получить id пользователя!\nПришлите ссылку на продавца либо перешлите его сообщение',
										self.back_key
									)
							user.mode = 'start'

						elif user.mode == 'input_msg_for_admins':
							if msg == 'назад':
								self.sender(user.vk_id, 'Выберите одно из предложенных действий', self.menu_key)
								user.mode = 'start'

							else:
								self.sender(config.admin_id, f'Сообщение для администрации от @id{user.vk_id}: {event.text}', self.clear_key)
								self.sender(user.vk_id, 'Ваше сообщение отправлено администратору.\nС вами свяжутся.', self.menu_key)
								user.mode = 'start'

						elif user.mode == 'confirm_guarantee':
							if msg == 'назад':
								self.sender(user.vk_id, 'Выберите одно из предложенных действий', self.menu_key)
								user.mode = 'start'

							elif msg == 'подтвердить':
								self.sender(config.admin_id, f'Пользователь @id{user.vk_id} хочет заключить сделку.', self.clear_key)
								self.sender(user.vk_id, 'Ожидайте сообщения от администратора.', self.menu_key)
								user.mode = 'start'

					user.save()


if __name__ == '__main__':
	VkBot().main()
