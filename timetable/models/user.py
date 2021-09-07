from django.db import models
from .choices import timezone_choices
from .course import School
from django.contrib.auth.models import AbstractUser
from courseshare import settings

# Create your models here.

def get_default_user_timezone():
    return settings.DEFAULT_TIMEZONE

class User(AbstractUser):
    description = models.TextField(blank=True)
    school = models.ForeignKey(School, null=True, on_delete=models.CASCADE, related_name='users')
    timezone = models.CharField(max_length=50, choices=timezone_choices, default=get_default_user_timezone)

    def get_ongoing_timetables(self):
        return [i for i in self.timetables.all() if i.term.is_ongoing()]
