from django.urls import path
from .views import RegisterView, SubjectListView, JoinQueueView, CompleteSubmissionView, home_view, register_view, \
    login_view, logout_view, join_queue, queue_detail, complete_submission

urlpatterns = [
    # API
    path('api/users/register/', RegisterView.as_view(), name='api_register'),
    path('api/subjects/', SubjectListView.as_view(), name='subject_list'),
    path('api/queue/join/', JoinQueueView.as_view(), name='join_queue'),
    path('api/queue/complete/', CompleteSubmissionView.as_view(), name='complete_submission'),
    # GUI
    path('', home_view, name='home'),
    path('register/', register_view, name='register'),
    path('login/', login_view, name='login'),
    path('logout/', logout_view, name='logout'),
    path('join/<int:subject_id>/', join_queue, name='join_queue'),
    path('queue/<int:session_id>/', queue_detail, name='queue_detail'),
    path('complete/<int:entry_id>/', complete_submission, name='complete_submission'),
]

