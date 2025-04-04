from django import forms
from django.contrib.auth.forms import UserCreationForm, PasswordResetForm
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from .models import User, RegistrationToken
import uuid

class CustomUserCreationForm(UserCreationForm):
    telegram_username = forms.CharField(
        max_length=32,
        required=False,
        help_text="Ваш Telegram username (например, @username). Используется для отправки уведомлений."
    )

    class Meta:
        model = User
        fields = ['username', 'telegram_username', 'password1', 'password2']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.registration_token = RegistrationToken.objects.create()
        print(f"Created RegistrationToken: {self.registration_token.token}")  

    def clean_telegram_username(self):
        telegram_username = self.cleaned_data.get('telegram_username')
        if telegram_username and not telegram_username.startswith('@'):
            telegram_username = '@' + telegram_username
        if User.objects.filter(telegram_username=telegram_username).exclude(pk=self.instance.pk).exists():
            raise forms.ValidationError("Этот Telegram username уже используется.")
        return telegram_username

class CustomPasswordResetForm(PasswordResetForm):
    email = None
    username = forms.CharField(
        max_length=150,
        required=True,
        label="Имя пользователя",
        help_text="Введите ваше имя пользователя для сброса пароля."
    )

    def clean_username(self):
        username = self.cleaned_data.get('username')
        if not User.objects.filter(telegram_username=username).exists():
            raise forms.ValidationError("Пользователь с таким именем не найден.")
        return username

    def save(self, domain_override=None, use_https=False, token_generator=None, request=None, **kwargs):
        telegram_username = self.cleaned_data['username']
        user = User.objects.get(telegram_username=telegram_username)
        self.uid = urlsafe_base64_encode(force_bytes(user.pk))
        self.token = token_generator.make_token(user)
        return user


class UserAvatarForm(forms.Form):
    avatar = forms.ImageField(
        label="Загрузить свою аватарку",
        required=False,
        widget=forms.ClearableFileInput(attrs={'class': 'form-control'})
    )
    default_avatar = forms.ChoiceField(
        label="Или выберите дефолтную аватарку",
        choices=[
            ('avatars/defaults/avatar1.jpg', 'Аватар 1'),
            ('avatars/defaults/avatar2.jpg', 'Аватар 2'),
            # ('avatars/defaults/avatar3.jpg', 'Аватар 3'),
        ],
        widget=forms.Select(attrs={'class': 'form-select'})
    )