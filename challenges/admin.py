from django.contrib import admin

from .models import Challenge, ChallengeSubmission

@admin.register(Challenge)
class ChallengeAdmin(admin.ModelAdmin):
    list_display = ('title', 'language', 'difficulty', 'created_at')
    list_filter = ('language', 'difficulty')
    search_fields = ('title',)

@admin.register(ChallengeSubmission)
class ChallengeSubmissionAdmin(admin.ModelAdmin):
    list_display = ('user', 'challenge', 'ai_score', 'is_passed', 'created_at')
    list_filter = ('is_passed', 'challenge__language')
