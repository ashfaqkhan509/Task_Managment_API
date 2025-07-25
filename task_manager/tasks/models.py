from django.db import models
from django.contrib.auth.models import User


class Task(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    due_date = models.DateField()
    is_completed = models.BooleanField(default=False)
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name="tasks")
    share_with = models.ManyToManyField(User, related_name="shared_tasks", blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title
