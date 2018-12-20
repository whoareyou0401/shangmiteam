from django.contrib import admin
from .models import *
# Register your models here.

class UserAdmin(admin.ModelAdmin):

    list_display = ["nick_name", "source", "create_time"]
    search_fields = ["nick_name", "source"]
    list_filter = ["source"]

class ActiveAdmin(admin.ModelAdmin):

    list_display = ["name", "give_money", "share_give_money", "complete_num", "need_num"]


class StoreAdmin(admin.ModelAdmin):
    def boss_name(self, obj):
        return obj.boss.nick_name
    boss_name.short_description = "店长"
    search_fields = ["boss", "name", "address"]
    list_display = ["name", "address", "is_active", "boss_name"]
    list_filter = ["is_active"]

admin.site.register(Active, ActiveAdmin)
admin.site.register(Store, StoreAdmin)
admin.site.register(ShangmiUser, UserAdmin)
