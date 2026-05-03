from django.db import models
from django.contrib.auth.models import User

class Challenge(models.Model):
    LANGUAGE_CHOICES = [
        ('python', 'Python'),
        ('javascript', 'JavaScript'),
        ('java', 'Java'),
        ('cpp', 'C++'),
    ]
    DIFFICULTY_CHOICES = [
        ('easy', 'Легкий'),
        ('medium', 'Средний'),
        ('hard', 'Сложный'),
    ]

    title = models.CharField(max_length=255)
    description = models.TextField(help_text="Условие задачи, примеры ввода/вывода")
    starter_code = models.TextField(blank=True,null=True, help_text="Шаблон кода для старта")
    solution_hint = models.TextField(blank=True, help_text="Подсказка (не показывается студенту)")

    language = models.CharField(max_length=20, choices=LANGUAGE_CHOICES)
    difficulty = models.CharField(max_length=10, choices=DIFFICULTY_CHOICES)

    created_by = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL, related_name='created_challenges')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.title} ({self.language})"

class ChallengeSubmission(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='challenge_submissions')
    challenge = models.ForeignKey(Challenge, on_delete=models.CASCADE, related_name='submissions')

    code = models.TextField()
    ai_score = models.IntegerField(null=True, blank=True)
    ai_feedback = models.TextField(blank=True)
    is_passed = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.username} - {self.challenge.title} ({self.ai_score})"