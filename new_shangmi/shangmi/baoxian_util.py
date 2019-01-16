# -*- coding: utf-8 -*-
import hashlib
import logging
import json

import requests
import urllib
import pyDes

import base64


def gen_sign(orig_id, orig_name, orig_phone, channel):
    target_string = orig_id + orig_name + orig_phone + channel + 'baoxian-$@'
    logging.info('target_string is {}'.format(target_string))
    md5 = hashlib.md5()
    md5.update(target_string.encode())
    hash_string = md5.hexdigest()
    return hash_string


def encrypt(data):
    key = '69b94dbd'
    # 外部传入的参数的解密对象
    des_obj = pyDes.des(key, pyDes.ECB, "\0\0\0\0\0\0\0\0", pad=None, padmode=pyDes.PAD_PKCS5)
    new = des_obj.encrypt(data.encode())

    return base64.encodebytes(new)


def submit_one(name, phone, birth, sex, id_no, code):
    channel = 'shangmi'
    sign = gen_sign(id_no, name, phone, channel)
    custom = {}
    custom = json.dumps(custom)
    data = {
        "subchannel": 'shangmiapi1',
        "name": encrypt(name),
        "phone": encrypt(phone),
        "sign": sign,
        "birth": encrypt(birth),
        "sex": encrypt(sex),
        "channel": channel,
        "custom": encrypt(custom),
        "code": code,
        "id_no": encrypt(id_no),
        # 客户IP 和UserAgent
        "customer_ip": '106.37.99.239',
        "user_agent": 'Mozilla/5.0 (iPhone; CPU iPhone OS 11_0 like Mac OS X) AppleWebKit/604.1.38 (KHTML, like Gecko) Version/11.0 Mobile/15A372 Safari/604.1',
    }
    if not id_no:
        data.pop('id_no')
    url = 'http://47.92.104.74:9099/insurance/enhanced'
    params = urllib.parse.urlencode(data)
    url = "{}?{}".format(url, params)
    r = requests.get(url)
    return json.loads(r.content.decode())


