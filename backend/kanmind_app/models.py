from django.db import models
from django.contrib.auth.models import User

# Create your models here.

class Board(models.Model):
    title   = models.CharField(max_length=255)
    owner   = models.ForeignKey(User, related_name='owned_boards', on_delete=models.CASCADE)
    members = models.ManyToManyField(User, related_name='boards', blank=True)

    def __str__(self):
        return self.title

class Task(models.Model):
    STATUS_CHOICES = [
        ('to-do', 'To Do'),
        ('in-progress', 'In Progress'),
        ('review', 'Review'),
        ('done', 'Done'),
    ]
    PRIORITY_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
    ]

    board       = models.ForeignKey(Board, related_name='tasks', on_delete=models.CASCADE)
    title       = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    status      = models.CharField(max_length=20, choices=STATUS_CHOICES)
    priority    = models.CharField(max_length=10, choices=PRIORITY_CHOICES)
    assignee    = models.ForeignKey(User, related_name='assigned_tasks', on_delete=models.SET_NULL, null=True, blank=True)
    reviewer    = models.ForeignKey(User, related_name='review_tasks', on_delete=models.SET_NULL, null=True, blank=True)
    due_date    = models.DateField(null=True, blank=True)
    created_by  = models.ForeignKey(User, related_name='created_tasks', on_delete=models.CASCADE, null=False, blank=False)

    def __str__(self):
        return f"{self.title} ({self.status})"

class Comment(models.Model):
    task       = models.ForeignKey(Task, related_name='comments', on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    author     = models.ForeignKey(User, related_name='comments', on_delete=models.CASCADE)
    content    = models.TextField()
    
    def __str__(self):
        return f"Comment by {self.author} on {self.created_at}"