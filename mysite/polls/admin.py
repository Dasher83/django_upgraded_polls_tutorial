from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import Choice, Question, User


# Register your models here.


class ChoiceInLine(admin.TabularInline):
    model = Choice
    extra = 3


class QuestionAdmin(admin.ModelAdmin):
    fieldsets = [
        (None, {"fields": ["question_text"]}),
        ("Date information", {"fields": ["pub_date"], "classes": ["collapse"]}),
    ]
    inlines = [ChoiceInLine]
    list_display = ("question_text", "pub_date", "was_published_recently", "created_by")
    list_filter = ["pub_date"]
    search_fields = ["question_text"]

    def save_model(self, request, obj, form, change):
        obj.created_by = request.user
        obj.save()


admin.site.register(User, UserAdmin)
admin.site.register(Question, QuestionAdmin)
