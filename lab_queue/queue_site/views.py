from django.contrib import messages
from django.contrib.auth.decorators import login_required
from datetime import datetime, timedelta

from django.http import Http404
from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm, logger
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status

from .forms import CustomUserCreationForm
from .models import User, Subject, LabSession, QueueEntry, Schedule
from .serializers import UserSerializer, SubjectSerializer, LabSessionSerializer, QueueEntrySerializer
from django.utils import timezone


def register_view(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('home')
    else:
        form = CustomUserCreationForm()
    return render(request, 'queue_site/register.html', {'form': form})


def login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect('home')
    else:
        form = AuthenticationForm()
    return render(request, 'queue_site/login.html', {'form': form})


def logout_view(request):
    logout(request)
    return redirect('home')


def home_view(request):
    create_sessions()
    subjects = Subject.objects.all()
    sessions = LabSession.objects.filter(status__in=['pending', 'active'])
    queue_entries = QueueEntry.objects.filter(lab_session__in=sessions, student=request.user) if request.user.is_authenticated else []
    return render(request, 'queue_site/home.html', {
        'subjects': subjects,
        'sessions': sessions,
        'user_queues': queue_entries
    })


@login_required
def join_queue(request, subject_id):
    if request.method == 'POST':
        subject = Subject.objects.get(id=subject_id)
        session = LabSession.objects.filter(subject=subject, start_time__date=timezone.now().date()).first()

        if not session:
            schedule = Schedule.objects.filter(subject=subject).first()
            if schedule:
                start_dt = datetime.combine(timezone.now().date(), schedule.start_time)
                end_dt = start_dt + timedelta(minutes=schedule.duration_minutes)
                session = LabSession.objects.create(
                    subject=subject,
                    start_time=start_dt,
                    end_time=end_dt,
                    status='pending'
                )
            else:
                messages.error(request, "Для этого предмета нет расписания.")
                return redirect('home')

        # Проверяем, не в очереди ли уже пользователь
        if QueueEntry.objects.filter(lab_session=session, student=request.user,
                                     status__in=['waiting', 'submitting']).exists():
            messages.error(request, "Вы уже в очереди на этот предмет!")
        else:
            entry = QueueEntry.objects.create(lab_session=session, student=request.user)
            if not session.current_submitter and session.status == 'active':
                entry.status = 'submitting'
                entry.start_time = timezone.now()
                entry.save()
                session.current_submitter = entry
                session.save()
            messages.success(request, "Вы встали в конец очереди!")
        return redirect('home')
    return redirect('home')


from django.utils import timezone
from datetime import datetime, timedelta
from .models import Schedule


def check_current_events(schedule_id):
    """Проверяет активность расписания и рассчитывает следующую дату"""
    try:
        schedule = Schedule.objects.get(id=schedule_id)
    except Schedule.DoesNotExist:
        print("Schedule не найден")
        return False, None

    now = timezone.localtime(timezone.now())
    print(f"Сейчас: {now}")

    # Определяем чётность недели
    current_week_parity = 'odd' if now.isocalendar()[1] % 2 == 1 else 'even'
    print(f"Текущая неделя: {current_week_parity}")

    # Рассчитываем следующий день занятия (всегда на будущее)
    days_ahead = (schedule.day_of_week - now.isoweekday() + 7) % 7
    next_date = now + timedelta(days=days_ahead)

    # Если сегодня день занятия, но время уже прошло — переносим на следующую неделю
    if days_ahead == 0 and now.time() > schedule.start_time:
        next_date += timedelta(weeks=1)

    # Проверка чётности недели
    if schedule.week_parity != 'all':
        next_week_parity = 'odd' if next_date.isocalendar()[1] % 2 == 1 else 'even'
        if schedule.week_parity != next_week_parity:
            next_date += timedelta(weeks=1)

    next_event = timezone.make_aware(
        datetime.combine(next_date.date(), schedule.start_time)
    )
    print(f"Следующее событие: {next_event}")

    # Определяем, идёт ли сейчас занятие
    start_datetime = timezone.make_aware(
        datetime.combine(now.date(), schedule.start_time)
    )
    end_datetime = start_datetime + timedelta(minutes=schedule.duration_minutes)
    is_active = start_datetime <= now <= end_datetime

    return is_active, next_event



@login_required
def queue_detail(request, session_id):
    try:
        session = LabSession.objects.select_related('subject').get(id=session_id)
        queue_entries = QueueEntry.objects.filter(
            lab_session=session
        ).select_related('student').order_by('join_time')

        # Получаем расписание для предмета
        schedule = Schedule.objects.filter(
            subject=session.subject
        ).first()

        if schedule:
            is_active, next_event_date = check_current_events(schedule.id)
        else:
            is_active = session.start_time <= timezone.now() <= (session.end_time or timezone.now())
            next_event_date = None

        user_entry = queue_entries.filter(student=request.user).first()
        is_first = user_entry and user_entry.get_position() == 1

        if request.method == 'POST' and user_entry:
            user_entry.delete()
            messages.success(request, "Вы вышли из очереди!")
            # Обновляем current_submitter, если пользователь был первым
            if is_first and session.status == 'active':
                next_entry = queue_entries.filter(status='waiting').order_by('join_time').first()
                if next_entry:
                    next_entry.status = 'submitting'
                    next_entry.start_time = timezone.now()
                    next_entry.save()
                    session.current_submitter = next_entry
                else:
                    session.current_submitter = None
                session.save()
            return redirect('queue_detail', session_id=session_id)

        return render(request, 'queue_site/queue_detail.html', {
            'session': session,
            'queue_entries': queue_entries,
            'user_entry': user_entry,
            'is_first': is_first,
            'is_active': is_active,
            'next_event_date': next_event_date,
            'schedule': schedule,  # <-- добавляем schedule
            'now': timezone.now()
        })


    except LabSession.DoesNotExist:
        raise Http404("Сессия не найдена")
    except Exception as e:
        logger.error(f"Ошибка в queue_detail: {str(e)}")
        raise



@login_required
def complete_submission(request, entry_id):
    if request.method == 'POST':
        entry = QueueEntry.objects.get(id=entry_id, student=request.user)
        if entry.status == 'submitting':
            entry.status = 'completed'
            entry.end_time = timezone.now()
            entry.save()
            session = entry.lab_session
            next_entry = QueueEntry.objects.filter(lab_session=session, status='waiting').order_by('join_time').first()
            if next_entry:
                next_entry.status = 'submitting'
                next_entry.start_time = timezone.now()
                next_entry.save()
                session.current_submitter = next_entry
            else:
                session.current_submitter = None
                if not QueueEntry.objects.filter(lab_session=session, status__in=['waiting', 'submitting']).exists():
                    session.status = 'completed'
            session.save()
            messages.success(request, "Вы отметили, что защитили лабу!")
        return redirect('home')
    return redirect('home')


def create_sessions():
    now = timezone.now()
    current_day = now.weekday()
    week_number = now.isocalendar()[1]
    is_even_week = week_number % 2 == 0

    # Удаляем завершённые сессии
    completed_sessions = LabSession.objects.filter(end_time__lte=now, status='active')
    for session in completed_sessions:
        session.delete()

    # Создаём новые сессии
    schedules = Schedule.objects.filter(day_of_week=current_day)
    for schedule in schedules:
        if (schedule.week_parity == 'all' or
            (schedule.week_parity == 'even' and is_even_week) or
            (schedule.week_parity == 'odd' and not is_even_week)):
            # Указываем время в локальном поясе
            local_start_dt = timezone.make_aware(
                datetime.combine(now.date(), schedule.start_time),
                timezone.get_current_timezone()
            )
            local_end_dt = local_start_dt + timedelta(minutes=schedule.duration_minutes)

            # Удаляем старую сессию
            LabSession.objects.filter(
                subject=schedule.subject,
                start_time__date=now.date()
            ).delete()

            # Создаём новую сессию
            new_session = LabSession.objects.create(
                subject=schedule.subject,
                start_time=local_start_dt,
                end_time=local_end_dt,
                status='active' if local_start_dt <= now <= local_end_dt else 'pending'
            )
            print(f"Создана сессия: Start {timezone.localtime(new_session.start_time)}, End {timezone.localtime(new_session.end_time)}")


class CompleteSubmissionView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            queue_entry_id = request.data.get('queue_site/queue_entry_id')
            # Проверяем, что запись принадлежит текущему студенту
            queue_entry = QueueEntry.objects.get(id=queue_entry_id, student=request.user)

            # Убеждаемся, что студент сейчас сдаёт
            if queue_entry.status != 'submitting':
                return Response({"error": "Вы сейчас не сдаёте."}, status=status.HTTP_400_BAD_REQUEST)

            # Завершаем защиту
            queue_entry.status = 'completed'
            queue_entry.end_time = timezone.now()
            queue_entry.save()

            # Продвигаем очередь
            session = queue_entry.lab_session
            next_entry = QueueEntry.objects.filter(
                lab_session=session, status='waiting'
            ).order_by('join_time').first()

            if next_entry:
                next_entry.status = 'submitting'
                next_entry.start_time = timezone.now()
                next_entry.save()
                session.current_submitter = next_entry
            else:
                session.current_submitter = None
                # Если больше нет ожидающих, завершаем сессию
                if not QueueEntry.objects.filter(lab_session=session, status__in=['waiting', 'submitting']).exists():
                    session.status = 'completed'
            session.save()

            return Response({"message": "Защита успешно завершена."}, status=status.HTTP_200_OK)

        except QueueEntry.DoesNotExist:
            return Response({"error": "Запись не найдена или доступ запрещён."}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class RegisterView(APIView):
    def post(self, request):
        serializer = UserSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class SubjectListView(APIView):
    def get(self, request):
        subjects = Subject.objects.all()
        serializer = SubjectSerializer(subjects, many=True)
        return Response(serializer.data)


class JoinQueueView(APIView):
    def post(self, request):
        lab_session_id = request.data.get('lab_session_id')
        student_id = request.data.get('student_id')  # Предполагаем, что студент авторизован
        try:
            lab_session = LabSession.objects.get(id=lab_session_id)
            student = User.objects.get(id=student_id)
            queue_entry = QueueEntry.objects.create(lab_session=lab_session, student=student)
            serializer = QueueEntrySerializer(queue_entry)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        except (LabSession.DoesNotExist, User.DoesNotExist):
            return Response({"error": "Session or student not found"}, status=status.HTTP_404_NOT_FOUND)

