from django.db import models
from django.contrib.auth.models import User

# Create your models here.

class UserProfile(models.Model):
    """
    Model representing additional profile information for a User.
    Links one-to-one with Django's built-in User model.
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    bio = models.TextField(blank=True, null=True)
    location = models.CharField(max_length=100, blank=True, null=True)

    def __str__(self):
        """
        Return the related User's username for readability.
        """
        return self.user.username