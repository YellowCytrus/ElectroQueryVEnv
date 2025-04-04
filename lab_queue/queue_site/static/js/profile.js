// queue_site/static/js/profile.js

document.addEventListener('DOMContentLoaded', function() {
    console.log('profile.js loaded');

    let hasChanges = false;
    let originalAvatar = document.getElementById('avatar-preview').src;

    // Функция для показа уведомления
    function showNotification(message, type = 'success') {
        const toastEl = document.getElementById('notification-toast');
        const toastBody = document.getElementById('notification-toast-body');

        // Проверяем, что элементы существуют
        if (!toastEl || !toastBody) {
            console.error('Toast elements not found. Falling back to alert.');
            alert(message); // Возвращаемся к alert, если toast не найден
            return;
        }

        // Устанавливаем текст уведомления
        toastBody.textContent = message;

        // Устанавливаем класс в зависимости от типа уведомления
        toastEl.classList.remove('toast-success', 'toast-error');
        toastEl.classList.add(`toast-${type}`);

        // Инициализируем toast
        const toast = new bootstrap.Toast(toastEl, {
            autohide: true,
            delay: 3000 // Уведомление исчезает через 3 секунды
        });

        // Показываем toast
        toast.show();

        // При наведении мыши приостанавливаем автоскрытие
        toastEl.addEventListener('mouseenter', function() {
            toast._config.autohide = false; // Отключаем автоскрытие
        });

        // При уходе мыши возобновляем автоскрытие
        toastEl.addEventListener('mouseleave', function() {
            toast._config.autohide = true; // Включаем автоскрытие
            toast.hide(); // Запускаем скрытие
        });
    }

    // При клике на аватарку открываем выбор файла
    document.getElementById('avatar-preview').addEventListener('click', function() {
        document.getElementById('avatar-input').click();
    });

    // Предпросмотр загруженной аватарки
    document.getElementById('avatar-input').addEventListener('change', function(event) {
        const file = event.target.files[0];
        if (file) {
            const reader = new FileReader();
            reader.onload = function(e) {
                document.getElementById('avatar-preview').src = e.target.result;
                hasChanges = true;
                document.getElementById('save-avatar-btn').style.display = 'block';
            };
            reader.readAsDataURL(file);
        }
    });

    // Предпросмотр дефолтной аватарки
    document.getElementById('default-avatar-select').addEventListener('change', function() {
        const selectedAvatar = this.value;
        document.getElementById('avatar-preview').src = `/media/${selectedAvatar}`;
        hasChanges = true;
        document.getElementById('save-avatar-btn').style.display = 'block';
    });

    // Сохранение изменений через AJAX
    document.getElementById('save-avatar-btn').addEventListener('click', function() {
        const formData = new FormData(document.getElementById('avatar-form'));
        const avatarInput = document.getElementById('avatar-input');
        if (avatarInput.files[0]) {
            formData.append('avatar', avatarInput.files[0]);
        }

        fetch(document.getElementById('avatar-form').action, {
            method: 'POST',
            body: formData,
            headers: {
                'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value
            }
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                hasChanges = false;
                originalAvatar = document.getElementById('avatar-preview').src;
                document.getElementById('save-avatar-btn').style.display = 'none';
                showNotification('Аватарка успешно обновлена!', 'success');
            } else {
                showNotification('Ошибка при сохранении аватарки: ' + data.error, 'error');
            }
        })
        .catch(error => {
            console.error('Ошибка:', error);
            showNotification('Произошла ошибка при сохранении аватарки.', 'error');
        });
    });

    // Предупреждение при попытке покинуть страницу
    window.addEventListener('beforeunload', function(event) {
        if (hasChanges) {
            event.preventDefault();
            event.returnValue = 'У вас есть несохранённые изменения. Вы уверены, что хотите уйти?';
        }
    });

    // Показ модального окна при клике на ссылки
    document.querySelectorAll('a[href]').forEach(link => {
        link.addEventListener('click', function(event) {
            if (hasChanges) {
                event.preventDefault();
                const targetUrl = this.href;
                const modal = new bootstrap.Modal(document.getElementById('confirmModal'));
                modal.show();

                // Сохранение изменений
                document.getElementById('save-changes-btn').onclick = function() {
                    document.getElementById('save-avatar-btn').click();
                    modal.hide();
                    window.location.href = targetUrl;
                };

                // Отмена изменений
                document.getElementById('discard-changes-btn').onclick = function() {
                    hasChanges = false;
                    document.getElementById('avatar-preview').src = originalAvatar;
                    document.getElementById('save-avatar-btn').style.display = 'none';
                    modal.hide();
                    window.location.href = targetUrl;
                };
            }
        });
    });

    // AJAX для обновления статуса лабораторной работы
    const toggleButtons = document.querySelectorAll('.toggle-lab-btn');
    console.log('Found toggle buttons:', toggleButtons.length);
    toggleButtons.forEach(button => {
        console.log('Attaching event listener to button:', button);
        button.addEventListener('click', function(event) {
            event.preventDefault();
            const progressId = this.getAttribute('data-id');
            const url = this.getAttribute('data-url');
            console.log('Button clicked:', progressId, url);

            fetch(url, {
                method: 'POST',
                headers: {
                    'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value,
                    'X-Requested-With': 'XMLHttpRequest'
                }
            })
            .then(response => {
                console.log('Fetch response:', response);
                return response.json();
            })
            .then(data => {
                console.log('Fetch data:', data);
                if (data.success) {
                    // Обновляем кнопку
                    if (data.is_completed) {
                        this.classList.remove('btn-success');
                        this.classList.add('btn-outline-danger');
                        this.textContent = 'Не сдал';
                        // Подсвечиваем карточку
                        document.getElementById(`lab-${progressId}`).classList.add('bg-light');
                        document.getElementById(`lab-${progressId}`).querySelector('span').classList.add('text-muted');
                    } else {
                        this.classList.remove('btn-outline-danger');
                        this.classList.add('btn-success');
                        this.textContent = 'Сдал';
                        // Убираем подсветку карточки
                        document.getElementById(`lab-${progressId}`).classList.remove('bg-light');
                        document.getElementById(`lab-${progressId}`).querySelector('span').classList.remove('text-muted');
                    }
                    // Показываем уведомление
                    showNotification(data.message, 'success');
                } else {
                    showNotification('Ошибка при обновлении статуса.', 'error');
                }
            })
            .catch(error => {
                console.error('Ошибка:', error);
                showNotification('Произошла ошибка при обновлении статуса.', 'error');
            });
        });
    });
});