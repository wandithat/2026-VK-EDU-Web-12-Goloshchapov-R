(function () {
    function getCookie(name) {
        const cookies = document.cookie ? document.cookie.split(';') : [];
        for (const cookie of cookies) {
            const value = cookie.trim();
            if (value.startsWith(name + '=')) {
                return decodeURIComponent(value.substring(name.length + 1));
            }
        }
        return null;
    }

    function showError(form, message) {
        let error = form.parentElement.querySelector('.js-action-error');
        if (!error) {
            error = document.createElement('div');
            error.className = 'alert alert-danger js-action-error mt-2';
            form.insertAdjacentElement('afterend', error);
        }
        error.textContent = message || 'Не удалось выполнить действие. Попробуйте ещё раз.';
    }

    document.addEventListener('change', function (event) {
        const checkbox = event.target.closest('[data-submit-on-change]');
        if (checkbox && checkbox.checked) {
            checkbox.form.requestSubmit();
        }
    });

    document.addEventListener('submit', async function (event) {
        const voteForm = event.target.closest('[data-ajax-vote]');
        const correctForm = event.target.closest('[data-correct-answer]');
        const form = voteForm || correctForm;
        if (!form) {
            return;
        }

        event.preventDefault();
        const button = form.querySelector('button[type="submit"]');
        if (button) {
            button.disabled = true;
        }

        try {
            const response = await fetch(form.action, {
                method: 'POST',
                headers: {
                    'X-CSRFToken': getCookie('csrftoken'),
                    'X-Requested-With': 'XMLHttpRequest',
                },
                body: new FormData(form),
                credentials: 'same-origin',
            });
            const data = await response.json();
            if (!response.ok) {
                if (response.status === 401) {
                    window.location.href = '/login/?next=' + encodeURIComponent(window.location.pathname + window.location.search);
                    return;
                }
                throw new Error(data.error || 'Ошибка запроса.');
            }

            if (voteForm) {
                const widget = form.closest('[data-vote-widget]');
                if (widget) {
                    widget.querySelector('[data-rating]').textContent = data.rating;
                    const upButton = widget.querySelector('input[name="value"][value="up"] + button');
                    const downButton = widget.querySelector('input[name="value"][value="down"] + button');
                    if (upButton) {
                        upButton.classList.toggle('vote-widget__btn--liked', data.liked);
                    }
                    if (downButton) {
                        downButton.classList.toggle('vote-widget__btn--disliked', data.disliked);
                    }
                }
            }

            if (correctForm) {
                const badge = document.createElement('span');
                badge.className = 'badge bg-success align-self-start';
                badge.textContent = 'Правильный ответ';
                form.replaceWith(badge);
                document.querySelectorAll('[data-correct-answer]').forEach(function (otherForm) {
                    otherForm.remove();
                });
            }
        } catch (error) {
            const checkbox = form.querySelector('[data-submit-on-change]');
            if (checkbox) {
                checkbox.checked = false;
            }
            showError(form, error.message);
        } finally {
            if (button && button.isConnected) {
                button.disabled = false;
            }
        }
    });
})();
