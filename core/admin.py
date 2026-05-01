from django.contrib import admin
from .models import Roadmap, Node, UserProgress, Submission

@admin.register(Node)
class NodeAdmin(admin.ModelAdmin):
    list_display = ('title', 'roadmap', 'parent', 'node_type', 'order')
    list_filter = ('node_type',)
    search_fields = ('title', 'description')
    ordering = ('roadmap', 'order')

@admin.register(Roadmap)
class RoadmapAdmin(admin.ModelAdmin):
    list_display = ('title', 'description_short')

    def description_short(self, obj):
        return obj.description[:50] + "..."
    description_short.short_description = "Описание"

@admin.register(UserProgress)
class UserProgressAdmin(admin.ModelAdmin):
    list_display = ('user', 'node', 'is_completed', 'score', 'completed_at')
    list_filter = ('is_completed', 'user')
    readonly_fields = ('completed_at',)

@admin.register(Submission)
class SubmissionAdmin(admin.ModelAdmin):
    list_display = ('user', 'node', 'ai_score', 'is_passed', 'created_at')
    readonly_fields = ('created_at',)