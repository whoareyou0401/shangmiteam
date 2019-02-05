import requests
import json
from PIL import Image
from io import BytesIO

def get_access_token():
	params = {'appid': 'wx8b50ab8fa813a49e',
			  'secret': 'b32f63c36ea123710173c4c9d4b15e8b',
			  'grant_type': 'client_credential'}
	url = 'https://api.weixin.qq.com/cgi-bin/token'
	response = requests.get(url, params=params)
	res = json.loads(response.content.decode())
	return res.get('access_token')


def get_qrcode(wx_path):
	token = get_access_token()
	url = "https://api.weixin.qq.com/cgi-bin/wxaapp/createwxaqrcode?access_token=%s" % token
	params = {
		'path': wx_path,
		'width': 330,
	}
	response = requests.post(url, data=json.dumps(params))
	return response.content

# get_qrcode('3', '1')
# img = Image.open('/home/liuda/django_project/shangmi/store3active1.png')