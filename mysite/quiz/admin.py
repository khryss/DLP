from django.contrib import admin

from .models import Quiz, Question, Option


class OptionInline(admin.StackedInline):
    model = Option
    extra = 3


class QuestionAdmin(admin.ModelAdmin):
    readonly_fields = ('quiz_name',)
    fieldsets = [
        (None,      {'fields': ['quiz_name', 'text']}),
    ]
    inlines = [OptionInline]


class QuestionInline(admin.StackedInline):
    model = Question
    extra = 3
    show_change_link = True


class QuizAdmin(admin.ModelAdmin):
    list_display = ('name',)
    inlines = [QuestionInline]


admin.site.register(Quiz, QuizAdmin)
admin.site.register(Question, QuestionAdmin)
