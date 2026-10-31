import { api } from '../api.js';
import { icon } from '../icons.js';
import { el, openDialog, shake, toast } from '../ui.js';

const MIN_PASSWORD_LENGTH = 8;

export function changePasswordDialog() {
    const error = el('div', { class: 'alert', role: 'alert', hidden: true });
    const field = (id, label, autocomplete) => {
        const input = el('input', { class: 'input', id, type: 'password', autocomplete, required: true });
        return { input, node: el('div', { class: 'field' }, el('label', { for: id }, label), input) };
    };
    const current = field('current-password', 'Current password', 'current-password');
    const next = field('new-password', `New password (at least ${MIN_PASSWORD_LENGTH} characters)`, 'new-password');
    const repeat = field('repeat-password', 'Repeat new password', 'new-password');
    const save = el('button', { class: 'btn btn-primary', type: 'submit' }, icon('check', 18), 'Change password');

    async function submit(event) {
        event.preventDefault();
        error.hidden = true;
        const fail = (message, input) => { error.textContent = message; error.hidden = false; shake(input); input.focus(); };
        if (!current.input.value) return fail('Enter your current password.', current.input);
        if (next.input.value.length < MIN_PASSWORD_LENGTH) return fail(`The new password needs at least ${MIN_PASSWORD_LENGTH} characters.`, next.input);
        if (next.input.value !== repeat.input.value) return fail('The new passwords do not match.', repeat.input);

        save.disabled = true;
        try {
            await api.auth.changePassword(current.input.value, next.input.value);
            dialog.close();
            toast('Password changed. Other devices have been signed out.');
        } catch (requestError) {
            fail(requestError.message, current.input);
            save.disabled = false;
        }
    }

    const dialog = el('dialog', { 'aria-labelledby': 'password-title' },
        el('form', { class: 'modal-card', novalidate: true, onsubmit: submit },
            el('div', { class: 'modal-header' },
                el('h2', { id: 'password-title' }, 'Change password'),
                el('button', { class: 'icon-btn', type: 'button', 'aria-label': 'Close', onclick: () => dialog.close() }, icon('x'))),
            el('div', { class: 'modal-body' }, error, current.node, next.node, repeat.node),
            el('div', { class: 'modal-footer' },
                el('button', { class: 'btn', type: 'button', onclick: () => dialog.close() }, 'Cancel'),
                save)));

    openDialog(dialog);
    current.input.focus();
}
