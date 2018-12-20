from django.contrib import admin
from .models import *
# Register your models here.

class ActiveAdmin(admin.ModelAdmin):


    list_display = ["name", "give_money", "share_give_money", "complete_num", "need_num"]

admin.site.register(Active, ActiveAdmin)
admin.site.register(ShangmiUser)
