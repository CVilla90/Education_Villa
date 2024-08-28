from django.contrib import admin
from .models import CustomUser, UserProfile, Diploma, Activity, ActivityQuestion

# Register your models here.


admin.site.register(CustomUser)
admin.site.register(UserProfile)
admin.site.register(Diploma)
admin.site.register(Activity)
admin.site.register(ActivityQuestion)
