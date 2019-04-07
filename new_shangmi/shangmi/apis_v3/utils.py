import json
import os
import requests
import hashlib
import uuid
from .cities import CITIES
from shangmi.utils import get_phone_area


def make(guid, mobile):
    md5 = hashlib.md5()
    mediaSource = os.environ.get("XM_mediaSource")
    md5.update((guid+mobile+mediaSource).encode("utf-8"))
    res = md5.hexdigest()
    return res.upper()

def submit_msg_to_xm(name, mobile, clint_ip, id_card):
    url = "http://crmadmin.mtarget.cn/api/unify_shuqi_test/collect"
    guid = str(uuid.uuid4().hex)
    area = get_phone_area(mobile).get("cityName")
    birth_day = "%s-%s-%s" % (id_card[6:10], id_card[10:12], id_card[12:14])
    if area not in CITIES:
        return False, "本地区暂无此活动"
    sex = "女" if int(id_card[16]) % 2 == 0 else "男"
    data = {
        "guid": guid,
        "verifyKey": make(guid, mobile),
        "appid": os.environ.get("XM_APP_ID"),
        "channel": "bn-02",
        "name": name,
        "birthday":birth_day,
        "sex": sex,
        "mobile": mobile,
        "idno":id_card,
        "ip":clint_ip,
        "city":area,
        "insurance":"泰康",
        "user_agent": 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/65.0.3325.181 Safari/537.36'
    }
    res = requests.post(url, data=json.dumps(data)).json()
    if res.get("retCode") == "0" and res.get("retMsg") == "OK":
        return True, "成功"
    else:
        return False, res.get("retMsg")