import vk_api
import config
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
		self.adm_menu_key = utils.get_vk_keyboard([
			[('Добавить нарушителя', 'синий')],
			[('Удалить нарушителя', 'синий')]
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
						if user.vk_id != config.admin_id:
							self.sender(user.vk_id, 'Выберите одно из предложенных действий', self.menu_key)
						else:
							self.sender(user.vk_id, 'Выберите одно из предложенных действий', self.adm_menu_key)
						user.mode = 'start'

					if user.vk_id == config.admin_id:
						"""Главный админ"""
						pass

					elif user.vk_id in [x.vk_id for x in Admin().select()]:
						"""Админы, назначенные главным админом"""
						pass

					else:
						"""Простые пользователи"""
						pass


if __name__ == '__main__':
	VkBot().main()
