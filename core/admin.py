from django.contrib import admin
from rangefilter.filters import DateTimeRangeFilter

from core.models import *


# Register your models here.

class EngageTasksAdmin(admin.ModelAdmin):
    list_display = ["target_name", "created", "status", "system_no"]
    list_filter = [("created", DateTimeRangeFilter), "status", "system_no"]
    search_fields = ['target_name']
    using = 'monitor'

    def get_queryset(self, request):
        # Tell Django to look for objects on the 'other' database.
        return super(EngageTasksAdmin, self).get_queryset(request).using(self.using)

    def save_model(self, request, obj, form, change):
        obj.save(using=self.using)


admin.site.register(User)
admin.site.register(EmailOTP)
admin.site.register(EngageTask, EngageTasksAdmin)
