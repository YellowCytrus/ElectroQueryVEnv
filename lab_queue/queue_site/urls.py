from django.urls import path
from django.contrib.auth import views as auth_views
from .views import RegisterView, SubjectListView, JoinQueueView, CompleteSubmissionView, home_view, register_view, \
    login_view, logout_view, join_queue, queue_detail, complete_submission, CustomPasswordResetView, \
    CheckTelegramUsernameView

urlpatterns = [
    # API
    path('api/users/register/', RegisterView.as_view(), name='api_register'),
    path('api/subjects/', SubjectListView.as_view(), name='subject_list'),
    path('api/queue/join/', JoinQueueView.as_view(), name='join_queue'),
    path('api/queue/complete/', CompleteSubmissionView.as_view(), name='complete_submission'),
    # GUI
    path('', home_view, name='home'),
    path('register/', RegisterView.as_view(), name='register'),
    path('check-telegram-username/<uuid:token>/', CheckTelegramUsernameView.as_view(), name='check_telegram_username'),
    path('login/', login_view, name='login'),
    path('logout/', logout_view, name='logout'),
    path('join/<int:subject_id>/', join_queue, name='join_queue'),
    path('queue/<int:session_id>/', queue_detail, name='queue_detail'),
    path('complete/<int:entry_id>/', complete_submission, name='complete_submission'),

    # Маршруты для сброса пароля
    path('password_reset/', CustomPasswordResetView.as_view(), name='password_reset'),

    path('password_reset/done/', auth_views.PasswordResetDoneView.as_view(
        template_name='queue_site/password_reset_done.html'
    ), name='password_reset_done'),

    path('reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(
        template_name='queue_site/password_reset_confirm.html'
    ), name='password_reset_confirm'),

    path('reset/done/', auth_views.PasswordResetCompleteView.as_view(
        template_name='queue_site/password_reset_complete.html'
    ), name='password_reset_complete'),
]