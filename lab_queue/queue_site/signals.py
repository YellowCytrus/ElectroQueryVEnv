# queue_site/signals.py

from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import UserSubject, SubjectLabWork, UserLabProgress, User


@receiver(post_save, sender=UserSubject)
def assign_lab_works_to_user(sender, instance, created, **kwargs):
    if created:  # Срабатывает только при создании новой связи UserSubject
        user = instance.user
        subject = instance.subject

        # Получаем все лабораторные работы для данного предмета
        lab_works = SubjectLabWork.objects.filter(subject=subject).values_list('lab_work', flat=True)

        # Создаём записи в UserLabProgress, если их ещё нет
        for lab_work_id in lab_works:
            UserLabProgress.objects.get_or_create(
                user=user,
                lab_work_id=lab_work_id,
                defaults={'is_completed': False}
            )


# Удаляем вызов initialize_user_lab_progress из apps.py
# Вместо этого создадим команду для инициализации
def initialize_user_lab_progress():
    # Проходим по всем связям UserSubject
    for user_subject in UserSubject.objects.all():
        user = user_subject.user
        subject = user_subject.subject

        # Получаем все лабораторные работы для данного предмета
        lab_works = SubjectLabWork.objects.filter(subject=subject).values_list('lab_work', flat=True)

        # Создаём записи в UserLabProgress, если их ещё нет
        for lab_work_id in lab_works:
            UserLabProgress.objects.get_or_create(
                user=user,
                lab_work_id=lab_work_id,
                defaults={'is_completed': False}
            )