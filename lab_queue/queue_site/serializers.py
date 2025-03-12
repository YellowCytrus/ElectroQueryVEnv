from rest_framework import serializers
from .models import User, Subject, LabSession, QueueEntry


class QueueEntrySerializer(serializers.ModelSerializer):
    class Meta:
        model = QueueEntry
        fields = ['id', 'student', 'lab_session', 'status', 'join_time', 'start_time', 'end_time']


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'telegram_id']


class SubjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = Subject
        fields = ['id', 'name', 'description']


class QueueEntrySerializer(serializers.ModelSerializer):
    student = UserSerializer(read_only=True)
    lab_session = serializers.PrimaryKeyRelatedField(queryset=LabSession.objects.all())

    class Meta:
        model = QueueEntry
        fields = ['id', 'lab_session', 'student', 'join_time', 'status', 'start_time', 'end_time']


class LabSessionSerializer(serializers.ModelSerializer):
    current_submitter = QueueEntrySerializer(read_only=True)
    subject = SubjectSerializer(read_only=True)

    class Meta:
        model = LabSession
        fields = ['id', 'subject', 'start_time', 'status', 'current_submitter']