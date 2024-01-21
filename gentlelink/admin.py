from django.contrib import admin
from .models import UserSettings, Tasks, Memos, Calendars, Notifications, Assignments, TaskShares, CoupleUser

admin.site.register(UserSettings)
admin.site.register(Tasks)
admin.site.register(Memos)
admin.site.register(Calendars)
admin.site.register(Notifications)
admin.site.register(Assignments)
admin.site.register(TaskShares)
admin.site.register(CoupleUser)