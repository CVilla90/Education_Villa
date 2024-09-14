from django.contrib import admin
from .models import CustomUser, UserProfile, Diploma, Activity, ActivityQuestion, Question

# Register other models
admin.site.register(CustomUser)
admin.site.register(UserProfile)
admin.site.register(Diploma)
admin.site.register(Activity)
admin.site.register(ActivityQuestion)

# Register the Question model with QuillField
@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    pass