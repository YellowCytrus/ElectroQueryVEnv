from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone

class User(AbstractUser):
    telegram_id = models.CharField(max_length=255, blank=True, null=True)

    def __str__(self):
        return self.username

class Subject(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)

    def __str__(self):
        return self.name

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
    end_time = models.DateTimeField(null=True, blank=True)  # Время окончания
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