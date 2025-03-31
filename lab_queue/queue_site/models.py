# queue_site/models.py

from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone
import uuid


class User(AbstractUser):
    telegram_username = models.CharField(
        max_length=32,
        blank=True,
        null=True,
        unique=True,
        help_text="Ваш Telegram username (например, @username). Используется для отправки уведомлений."
    )
    avatar = models.ImageField(
        upload_to='avatars/',
        blank=True,
        null=True,
        default='avatars/default.jpg',
        help_text="Аватар пользователя."
    )

    def __str__(self):
        return self.username


class RegistrationToken(models.Model):
    token = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    telegram_username = models.CharField(max_length=32, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    is_used = models.BooleanField(default=False)

    def __str__(self):
        return str(self.token)


class Subject(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)

    def __str__(self):
        return self.name


class UserSubject(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='subjects')
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, related_name='users')

    class Meta:
        unique_together = ('user', 'subject')  # Пользователь не может быть привязан к одному предмету дважды

    def __str__(self):
        return f"{self.user.username} - {self.subject.name}"


class Schedule(models.Model):
    WEEK_PARITY_CHOICES = [
        ('all', 'Каждая неделя'),
        ('even', 'Чётная неделя'),
        ('odd', 'Нечётная неделя'),
    ]
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE)
    start_time = models.TimeField()
    day_of_week = models.IntegerField(choices=[
        (1, 'Понедельник'), (2, 'Вторник'), (3, 'Среда'), (4, 'Четверг'),
        (5, 'Пятница'), (6, 'Суббота'), (7, 'Воскресенье'),
    ])
    week_parity = models.CharField(max_length=4, choices=WEEK_PARITY_CHOICES, default='all')
    duration_minutes = models.PositiveIntegerField(default=90)

    def __str__(self):
        return f"{self.subject.name} - {self.get_day_of_week_display()} {self.start_time} ({self.get_week_parity_display()})"


class LabSession(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('active', 'Active'),
        ('completed', 'Completed'),
    ]
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE)
    start_time = models.DateTimeField()
    end_time = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    current_submitter = models.ForeignKey('QueueEntry', on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return f"{self.subject.name} - {self.start_time}"


class QueueEntry(models.Model):
    STATUS_CHOICES = [
        ('waiting', 'Waiting'),
        ('submitting', 'Submitting'),
        ('completed', 'Completed'),
    ]
    lab_session = models.ForeignKey(LabSession, on_delete=models.CASCADE)
    student = models.ForeignKey(User, on_delete=models.CASCADE)
    join_time = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='waiting')
    start_time = models.DateTimeField(null=True, blank=True)
    end_time = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.student.username} - {self.lab_session}"

    def get_position(self):
        """Вычисляем место в очереди"""
        return QueueEntry.objects.filter(
            lab_session=self.lab_session,
            join_time__lt=self.join_time,
            status__in=['waiting', 'submitting']
        ).count() + 1

    def get_wait_time(self):
        """Примерное время ожидания (место * 7 минут)"""
        return self.get_position() * 7


class LabWork(models.Model):
    number = models.PositiveIntegerField()
    title = models.CharField(max_length=255)

    def __str__(self):
        return f"Лабораторная {self.number}: {self.title}"


class SubjectLabWork(models.Model):
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, related_name='lab_works')
    lab_work = models.ForeignKey(LabWork, on_delete=models.CASCADE)

    class Meta:
        unique_together = ('subject', 'lab_work')

    def __str__(self):
        return f"{self.subject.name} - {self.lab_work.title}"


class UserLabProgress(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='lab_progress')
    lab_work = models.ForeignKey(LabWork, on_delete=models.CASCADE)
    is_completed = models.BooleanField(default=False)

    class Meta:
        unique_together = ('user', 'lab_work')

    def __str__(self):
        return f"{self.user.username} - {self.lab_work.title} ({'Сдано' if self.is_completed else 'Не сдано'})"