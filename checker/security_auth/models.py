from django.db import models
from django.contrib.auth.models import User

class SecurityQuestion(models.Model):
    # Link the question to a specific user
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    question = models.CharField(max_length=255)
    # The answer is a CharField, but we will store it as a hash.
    answer_hash = models.CharField(max_length=128)

    def __str__(self):
        return f"Security Question for {self.user.username}"
        