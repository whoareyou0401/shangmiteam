# -*- coding: utf-8 -*-
import hashlib
import logging
import json
import random
import requests
import urllib
import pyDes

import base64
import time
# from .my_test import get_name1
import re
import random, unittest
from datetime import datetime, timedelta, date
import pymysql
conn = pymysql.connect(
    host="127.0.0.1",
    user="root",
    password="liuda6015?",
    database="shangmi",
    charset="utf8")


area_count = {}
def test(phone):
    url = "http://mobsec-dianhua.baidu.com/dianhua_api/open/location?tel=%s" % phone
    res = requests.get(url).json().get("response")
    data = res.get(phone).get("detail")
    city = data.get("area")[0].get("city")
    province = data.get("province")
    print(province, city)
    return province, city
# 保险的工具函数

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
        "customer_ip": "106.37.99.239",
        "user_agent": 'Mozilla/5.0 (iPhone; CPU iPhone OS 11_0 like Mac OS X) AppleWebKit/604.1.38 (KHTML, like Gecko) Version/11.0 Mobile/15A372 Safari/604.1',
    }
    if not id_no:
        data.pop('id_no')
    # url = 'http://47.92.104.74:9099/insurance/enhanced'
    url = 'https://www.heiniubao.com/insurance/enhanced'
    params = urllib.parse.urlencode(data)
    url = "{}?{}".format(url, params)
    r = requests.get(url)
    return json.loads(r.content.decode())

def fetch(cursor):
    desc = cursor.description  # 获取字段的描述，默认获取数据库字段名称，重新定义时通过AS关键重新命名即可
    data_dict = [dict(zip([col[0] for col in desc], row)) for row in cursor.fetchall()]
    return data_dict[0]

def make_money():
    cursor = conn.cursor()
    # city, province
    sql = """
        SELECT `name`, idcard, phone
        FROM baoxian_data_1
        WHERE is_used=0 
        ORDER BY rand()
        LIMIT 1
    """
    cursor.execute(sql)
    res = fetch(cursor)
    birth = ''
    sex = ''
    code = ''
    name = res.get("name")
    phone = res.get("phone")
    idcard = res.get("idcard")
    area = test(phone)
    res["province"] = area[0]
    res["city"] = area[1]
    if res.get("province") in area_count:
        tmp = area_count[res.get("province")]
        area_count[res.get("province")] = tmp + 1
    else:
        area_count[res.get("province")] = 1
    print(area_count)
    citys = ["重庆", "北京", "昭通", "南宁",
             "舟山", "上海", "南京", "吕梁",
             "成都", "开封"]
    if area_count[res.get("province")] > 30 or res.get("city") in citys :
        # 如果本次 次数过高 再调用一次
        # make_money()
        return None
    res_msg = submit_one(name, phone, birth, sex, idcard, code)
    print(res_msg)
    if res_msg.get("error_code") in ["80", "0"]:
        update_sql = """
          update baoxian_data_1 set is_ok=1, use_time="{now}", is_used=1 WHERE phone="{phone}"
        """.format(
            now=datetime.now(),
            phone=phone
        )
        cursor.execute(update_sql)
        conn.commit()
    else:
        update_sql = """
                  update baoxian_data_1 set 
                  is_ok=0, 
                  use_time="{now}", 
                  is_used=1,
                  fail_msg="{msg}"
                  WHERE phone="{phone}"
                """.format(
            now=datetime.now(),
            msg=res_msg.get("error_msg"),
            phone=phone
        )
        cursor.execute(update_sql)
        conn.commit()
    if res_msg.get("error_code") in ["36", "28"]:
        if res.get("city") not in citys:
            citys.append(res.get("city"))
            print(citys)
    return True

def main():
    i = 0
    while i<130:
        res = make_money()
        if res:
            random_time = random.randint(10, 300)

            time.sleep(random_time)
        else:
            continue
        i += 1

if __name__ == "__main__":
    main()
    # birth = ''
    # sex = ''
    # code = ''
    # name = "孙旸"
    # phone = "15871377722"
    # idcard = "451030197712025295"
    # res = submit_one(name, phone, birth, sex, idcard, code)
    # print(res)
