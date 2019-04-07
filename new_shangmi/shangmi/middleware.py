import datetime

from django.conf import settings
from django.http import JsonResponse
from django.utils.deprecation import MiddlewareMixin
from .tasks import send_my_mail
from .models import ErrorLog

class MyExceptionMiddleWare(MiddlewareMixin):

    def process_exception(self, request, exception):
        if settings.DEBUG == True:
            path = request.path
            error_msg = str(exception)
            now = datetime.datetime.now()
            msg = "路径{path}出现了{error_msg}".format(
                path=path,
                error_msg=error_msg
            )
            # 去数据库搜索 今天是不是已经发送过邮件了
            if not ErrorLog.objects.filter(
                    api_path=path,
                    msg=msg,
                date=now.date()
            ).exists():
                recipient_list = [user[1] for user in settings.ADMINS]
                # 保存错误信息
                ErrorLog.objects.create(api_path=path, msg=msg)
                send_my_mail.delay(msg,recipient_list)

            #发送邮件这个事
        res = {
            "code": 10,
            "msg": str(exception),
            "data":""
        }

        return JsonResponse(res)