import requests
from lxml import etree

def check_id(idcard):
    if len(idcard) == 18 or len(idcard) == 15:
        pass
    else:
        return None
    url = "http://qq.ip138.com/idsearch/index.asp?action=idcard&userid=%s"%str(idcard)
    headers = {
        "user-agent": "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/68.0.3440.106 Safari/537.36"
    }
    res = requests.get(url)
    html = etree.HTML(res.content)
    data = html.xpath("//td[@class='tdc2']")
    if len(data) == 3:
        sex = data[0].text
        birthday = data[1].text
        place = data[2].text
        return sex, birthday, place
    else:
        return None
def send_msg():
    sid = "ACf4ec43f682f284e5d557dbb60320ce7a"
    token = "39248f374ef72659fa20d3ee90d34e55"
    from twilio.rest import Client

    # Your Account SID from twilio.com/console
    # account_sid = "ACc06d56b8bc5396f76736c3fc3346983a"
    # Your Auth Token from twilio.com/console
    # auth_token = "your_auth_token"

    client = Client(sid, token)
    # UQf0PXK00cNC/RmdZh6QQXkgS7g1ZSK28tQyOX6P
    # (541) 233-0839 15412330839
    message = client.messages.create(
        to="13366026441",
        from_="15412330839",
        body="Hello from Python!")

    print(message.sid)


if __name__ == "__main__":
    send_msg()