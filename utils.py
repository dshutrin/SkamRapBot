from models import *
from json import dumps


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
			mode='start'
		).save()
		return User().get(vk_id=user_vk_id)
