from django.db import models
from django.contrib.auth.models import User

# Create your models here.

class Board(models.Model):
    """
    Represents a Kanban board.
    Fields:
      - title: the board's title.
      - owner: the User who created the board.
      - members: Users who have access to this board.
    """
    title   = models.CharField(max_length=255)
    owner   = models.ForeignKey(User, related_name='owned_boards', on_delete=models.CASCADE)
    members = models.ManyToManyField(User, related_name='boards', blank=True)

    def __str__(self):
        """
        Return the board's title for readability.
        """
        return self.title

class Task(models.Model):
    """
    Represents a task (card) on a Board.
    Fields:
      - board: the Board this task belongs to.
      - title: short title of the task.
      - description: optional detailed description.
      - status: workflow status (to-do, in-progress, review, done).
      - priority: priority level (low, medium, high).
      - assignee: User assigned to complete the task (optional).
      - reviewer: User assigned to review the task (optional).
      - due_date: optional due date.
      - created_by: User who created the task (automatically set).
    """
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
    created_by  = models.ForeignKey(User, related_name='created_tasks', on_delete=models.CASCADE, null=True, blank=False)

    def __str__(self):
        """
        Return a string combining title and status.
        """
        return f"{self.title} ({self.status})"

class Comment(models.Model):
    """
    Represents a comment on a Task.
    Fields:
      - task: the Task this comment belongs to.
      - created_at: timestamp when the comment was created.
      - author: User who wrote the comment.
      - content: text of the comment.
    """
    task       = models.ForeignKey(Task, related_name='comments', on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    author     = models.ForeignKey(User, related_name='comments', on_delete=models.CASCADE)
    content    = models.TextField()
    
    def __str__(self):
        """
        Return a string indicating the author and creation time.
        """
        return f"Comment by {self.author} on {self.created_at}"