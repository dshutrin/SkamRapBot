import vk_api

import config
import models
from models import *
from json import dumps
from time import sleep


def get_vk_keyboard(buts):  # функция создания клавиатур
	nb = []
	for i in range(len(buts)):
		nb.append([])
		for k in range(len(buts[i])):
			color = {'зеленый': 'positive', 'красный': 'negative', 'синий': 'primary', 'белый': 'secondary'}[buts[i][k][1]]
			nb[i].append({
				"action": {"type": "text", "payload": "{\"button\": \"" + "1" + "\"}", "label": f"{buts[i][k][0]}"},
				"color": f"{color}"
			})
	return str(dumps({'one_time': False, 'buttons': nb}, ensure_ascii=False).encode('utf-8').decode('utf-8'))


def get_user_by_vk_id(user_vk_id):
	try:
		user = User().get(vk_id=user_vk_id)
		return user
	except Exception:
		User(
			vk_id=user_vk_id,
			mode='start',
			temp_id=-10
		).save()
		return User().get(vk_id=user_vk_id)


def get_user_id_from_forwarded_message(vk_session: vk_api.VkApi, user: models.User, event):

	msg = event.text.lower()
	msg_info = vk_session.method('messages.getById', {'message_ids': event.message_id})

	try:
		count = len(msg_info['items'][0]['fwd_messages'])

		if count > 0:
			return [x['from_id'] for x in msg_info['items'][0]['fwd_messages'] if x['from_id'] != user.vk_id][0]
		elif msg.startswith('https://vk.com/'):
			screen_name = msg.replace('https://vk.com/', '').strip()
			info = vk_session.method('utils.resolveScreenName', {'screen_name': screen_name})
			print(info)
			obj_id = info['object_id']

			return obj_id
		else:
			return None

	except Exception as error:
		print(error)
		return None


def mail_sender(vk_session, mail, users):
	for user in users:
		vk_session.method('messages.send', {'user_id': user.vk_id, 'message': mail.text, 'attachment': mail.photo_path, 'random_id': 0})
		print(f'Рассылка отправлена пользователю @id{user.vk_id}')
		sleep(0.05)


def send_for_admins(func, msg):
	users = [x.vk_id for x in User().select()]
	admins = [x for x in Admin().select()] + [User().get(vk_id=config.admin_id)]
	admins = [x for x in admins if x.vk_id in users]
	for admin in admins:
		func(admin, msg)
