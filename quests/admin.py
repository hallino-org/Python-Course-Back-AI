from django.contrib import admin
from .models import Quest, QuestTag, UserQuestProgress, QuestEvent

@admin.register(QuestTag)
class QuestTagAdmin(admin.ModelAdmin):
    list_display = ('name', 'tracking_type', 'is_active', 'created_at')
    list_filter = ('tracking_type', 'is_active')
    search_fields = ('name', 'description')
    ordering = ('name',)

class QuestInline(admin.TabularInline):
    model = Quest.tags.through
    extra = 1

@admin.register(Quest)
class QuestAdmin(admin.ModelAdmin):
    list_display = ('title', 'quest_type', 'xp_reward', 'is_active', 'start_date', 'end_date')
    list_filter = ('quest_type', 'is_active', 'repeatable')
    search_fields = ('title', 'description')
    filter_horizontal = ('tags', 'prerequisites')
    readonly_fields = ('created_at', 'updated_at')
    fieldsets = (
        (None, {
            'fields': ('title', 'description', 'quest_type', 'tags', 'prerequisites')
        }),
        ('Requirements', {
            'fields': ('xp_reward', 'required_value', 'repeatable')
        }),
        ('Schedule', {
            'fields': ('is_active', 'start_date', 'end_date')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

@admin.register(UserQuestProgress)
class UserQuestProgressAdmin(admin.ModelAdmin):
    list_display = ('user', 'quest', 'current_value', 'is_completed', 'completed_at')
    list_filter = ('is_completed', 'quest__quest_type')
    search_fields = ('user__username', 'quest__title')
    readonly_fields = ('created_at', 'last_updated')
    ordering = ('-last_updated',)

@admin.register(QuestEvent)
class QuestEventAdmin(admin.ModelAdmin):
    list_display = ('user', 'tag', 'value', 'created_at')
    list_filter = ('tag__tracking_type', 'tag')
    search_fields = ('user__username', 'tag__name')
    readonly_fields = ('created_at',)
    ordering = ('-created_at',)
