from django.contrib import admin

from .models import Board, Task, Comment

# Register your models here.

@admin.register(Board)
class BoardAdmin(admin.ModelAdmin):
    list_display = ('id', 'title', 'owner')
    search_fields = ('title', 'owner__username', 'owner__email')
    list_filter = ('owner',)
    raw_id_fields = ('members',)
    filter_horizontal = ('members',)

@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ('id', 'title', 'board', 'status', 'priority', 'assignee', 'reviewer', 'due_date')
    search_fields = ('title', 'board__title', 'assignee__username', 'reviewer__username')
    list_filter = ('status', 'priority', 'board')
    raw_id_fields = ('board', 'assignee', 'reviewer')

@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ('id', 'task', 'author', 'created_at')
    search_fields = ('task__title', 'author__username', 'content')
    list_filter = ('created_at',)
    raw_id_fields = ('task', 'author')