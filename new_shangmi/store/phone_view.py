import requests

def test(phone):
    url = "http://mobsec-dianhua.baidu.com/dianhua_api/open/location?tel=%s" % phone
    res = requests.get(url).json().get("response")
    data = res.get(phone).get("detail")
    city = data.get("area")[0].get("city")
    province = data.get("province")
    print(province, city)


if __name__ == "__main__":
    test("15200563362")