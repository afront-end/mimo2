from django.db import models
from django.contrib.auth.models import User

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')    
    avatar = models.ImageField(upload_to='avatars/', null=True, blank=True, verbose_name="Аватар")
    bio = models.TextField(max_length=500, blank=True, verbose_name="О себе")
    points = models.IntegerField(default=0, verbose_name="Баллы опыта")

    def __str__(self):
        return f"Профиль {self.user.username}"
    

class Roadmap(models.Model):
    title = models.CharField(max_length=200, verbose_name="Название")
    description = models.TextField(verbose_name="Описание")

    def __str__(self):
        return self.title


class Node(models.Model):
    NODE_TYPE_CHOICES = [
        ('stack', 'Stack'),
        ('topic', 'Topic'),
        ('subtopic', 'Subtopic')
    ]

    roadmap = models.ForeignKey(Roadmap,on_delete=models.CASCADE,related_name='nodes')

    parent = models.ForeignKey('self',on_delete=models.CASCADE,null=True,blank=True,related_name='children')

    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    content = models.TextField(help_text="Обучающий текст",null=True,blank=True)

    node_type = models.CharField(max_length=20,choices=NODE_TYPE_CHOICES)

    order = models.IntegerField(default=0)

    class Meta:
        ordering = ['parent__id', 'order']

    def __str__(self):
        return f"{self.roadmap.title} -> {self.title}"

    # 🔹 уровень вложенности (для контроля структуры)
    def get_level(self):
        level = 0
        node = self
        while node.parent:
            level += 1
            node = node.parent
        return level

    # 🔹 проверка доступа
    def is_accessible_by(self, user):
        # 1. корневые ноды (стэки)
        if not self.parent:
            # проверяем, есть ли предыдущий стек
            previous_nodes = Node.objects.filter(
                roadmap=self.roadmap,
                parent__isnull=True,
                order__lt=self.order
            )

            for node in previous_nodes:
                if not UserProgress.objects.filter(
                    user=user,
                    node=node,
                    is_completed=True
                ).exists():
                    return False

            return True

        # 2. вложенные темы
        return UserProgress.objects.filter(
            user=user,
            node=self.parent,
            is_completed=True
        ).exists()


class UserProgress(models.Model):
    user = models.ForeignKey(User,on_delete=models.CASCADE,related_name='progress')

    node = models.ForeignKey(Node,on_delete=models.CASCADE,related_name='progress')

    is_completed = models.BooleanField(default=False)
    score = models.FloatField(default=0.0)
    completed_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('user', 'node')

    def __str__(self):
        status = "Пройден" if self.is_completed else "В процессе"
        return f"{self.user.username} - {self.node.title} [{status}]"


class Submission(models.Model):
    user = models.ForeignKey(User,on_delete=models.CASCADE,related_name='submissions')
    node = models.ForeignKey(Node,on_delete=models.CASCADE,related_name='submissions')

    answer_text = models.TextField()
    code_answer = models.TextField(blank=True, null=True)

    ai_score = models.IntegerField(null=True, blank=True)
    ai_feedback = models.TextField(blank=True)

    is_passed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} -> {self.node.title} ({self.ai_score})"