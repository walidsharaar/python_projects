import { api } from '../api.js';
import { ROLE_LABELS, getUser } from '../auth.js';
import { icon } from '../icons.js';
import { avatar, el, emptyState, formatRelative, openDialog, pageHeader, plural, shake, toast } from '../ui.js';

const MIN_PASSWORD_LENGTH = 8;
const ROLE_HELP = {
    admin: 'Full access: dashboard, products, staff and all sales.',
    cashier: 'Can make sales and view orders. Cannot change products, prices or staff.',
};
let formCounter = 0;

export async function usersView() {
    let users = (await api.users.list()).items;
    const tbody = el('tbody');
    const subtitle = el('span');

    async function reload() {
        try {
            users = (await api.users.list()).items;
            render();
        } catch (error) {
            toast(error.message, 'error');
        }
    }

    function render() {
        const active = users.filter((user) => user.is_active).length;
        subtitle.textContent = `${plural(users.length, 'account')} · ${active} active`;
        tbody.replaceChildren(...users.map((user) => {
            const isMe = user.id === getUser().id;
            return el('tr', { class: user.is_active ? '' : 'inactive' },
                el('td', {}, el('div', { class: 'with-avatar' },
                    avatar(user.full_name, { round: true }),
                    el('div', { class: 'stack' },
                        el('span', { class: 'name' }, user.full_name, isMe ? el('span', { class: 'chip chip-sm' }, 'You') : null),
                        el('span', { class: 'sub' }, `@${user.username}`)))),
                el('td', {}, el('span', { class: `role-badge ${user.role}` }, ROLE_LABELS[user.role])),
                el('td', {}, el('span', { class: `status ${user.is_active ? 'on' : 'off'}` }, user.is_active ? 'Active' : 'Disabled')),
                el('td', { class: 'muted hide-sm' }, user.last_login_at ? formatRelative(user.last_login_at) : 'Never'),
                el('td', { class: 'actions' },
                    el('button', { class: 'icon-btn', type: 'button', title: 'Edit', 'aria-label': `Edit ${user.full_name}`, onclick: () => openForm(user) }, icon('pencil', 18))));
        }));
    }

    // One dialog for creating (no user) and editing (user given)
    function openForm(user = null) {
        const isMe = user?.id === getUser().id;
        const ids = { title: `user-title-${++formCounter}`, name: `user-name-${formCounter}`, username: `user-username-${formCounter}`, password: `user-password-${formCounter}` };
        const error = el('div', { class: 'alert', role: 'alert', hidden: true });
        const fullName = el('input', { class: 'input', id: ids.name, name: 'full_name', required: true, maxlength: '255', value: user?.full_name ?? '', autocomplete: 'off' });
        const username = el('input', {
            class: 'input', id: ids.username, name: 'username', required: !user, maxlength: '50', autocomplete: 'off',
            autocapitalize: 'none', spellcheck: 'false', value: user ? user.username : '', disabled: Boolean(user),
        });
        const password = el('input', {
            class: 'input', id: ids.password, name: 'password', type: 'password', autocomplete: 'new-password',
            placeholder: user ? 'Leave empty to keep the current password' : `At least ${MIN_PASSWORD_LENGTH} characters`,
        });

        let role = user?.role ?? 'cashier';
        const roleHelp = el('p', { class: 'note' }, icon('info', 16), ROLE_HELP[role]);
        const roleOptions = el('div', { class: 'segmented', role: 'radiogroup', 'aria-label': 'Role' },
            Object.entries(ROLE_LABELS).map(([value, label]) => el('button', {
                type: 'button', role: 'radio', class: value === role ? 'active' : '', 'aria-checked': String(value === role),
                disabled: isMe, 'data-value': value,
                onclick: (event) => {
                    role = value;
                    roleOptions.querySelectorAll('button').forEach((button) => {
                        const selected = button === event.currentTarget;
                        button.classList.toggle('active', selected);
                        button.setAttribute('aria-checked', String(selected));
                    });
                    roleHelp.replaceChildren(icon('info', 16), ROLE_HELP[value]);
                },
            }, icon(value === 'admin' ? 'shield' : 'cart', 16), label)));

        const activeToggle = el('input', { type: 'checkbox', class: 'switch-input', checked: user ? user.is_active : true, disabled: isMe, id: `user-active-${formCounter}` });
        const save = el('button', { class: 'btn btn-primary', type: 'submit' }, icon('check', 18), user ? 'Save changes' : 'Create account');

        async function submit(event) {
            event.preventDefault();
            error.hidden = true;
            if (!fullName.value.trim()) { shake(fullName); fullName.focus(); return; }
            if (!user && !/^[a-zA-Z0-9._-]{3,50}$/.test(username.value.trim())) {
                error.textContent = 'Username: 3-50 letters, digits, ".", "_" or "-".';
                error.hidden = false;
                shake(username);
                username.focus();
                return;
            }
            if ((!user || password.value) && password.value.length < MIN_PASSWORD_LENGTH) {
                error.textContent = `The password needs at least ${MIN_PASSWORD_LENGTH} characters.`;
                error.hidden = false;
                shake(password);
                password.focus();
                return;
            }

            save.disabled = true;
            try {
                const saved = user
                    ? await api.users.update(user.id, { full_name: fullName.value.trim(), role, is_active: activeToggle.checked, password: password.value || undefined })
                    : await api.users.create({ full_name: fullName.value.trim(), username: username.value.trim(), role, password: password.value });
                dialog.close();
                toast(user ? `${saved.full_name} updated` : `Account for ${saved.full_name} created`);
                await reload();
            } catch (requestError) {
                error.textContent = requestError.message;
                error.hidden = false;
                save.disabled = false;
            }
        }

        const dialog = el('dialog', { 'aria-labelledby': ids.title },
            el('form', { class: 'modal-card', novalidate: true, onsubmit: submit },
                el('div', { class: 'modal-header' },
                    el('h2', { id: ids.title }, user ? 'Edit staff account' : 'New staff account'),
                    el('button', { class: 'icon-btn', type: 'button', 'aria-label': 'Close', onclick: () => dialog.close() }, icon('x'))),
                el('div', { class: 'modal-body' },
                    error,
                    el('div', { class: 'field' }, el('label', { for: ids.name }, 'Full name'), fullName),
                    el('div', { class: 'field' }, el('label', { for: ids.username }, 'Username'),
                        el('div', { class: 'input-group' }, el('span', { class: 'prefix' }, '@'), username)),
                    el('div', { class: 'field' }, el('label', {}, 'Role'), roleOptions, roleHelp),
                    el('div', { class: 'field' }, el('label', { for: ids.password }, user ? 'Reset password' : 'Password'), password),
                    user ? el('label', { class: 'switch', for: activeToggle.id },
                        activeToggle, el('span', { class: 'switch-track', 'aria-hidden': 'true' }),
                        el('span', {}, el('strong', {}, 'Account active'), el('span', { class: 'muted small' }, ' · disabled accounts cannot sign in'))) : null,
                    isMe ? el('p', { class: 'note' }, icon('lock', 16), 'You cannot change your own role or disable your own account.') : null),
                el('div', { class: 'modal-footer' },
                    el('button', { class: 'btn', type: 'button', onclick: () => dialog.close() }, 'Cancel'),
                    save)));

        openDialog(dialog);
        fullName.focus();
    }

    render();

    return el('div', { class: 'page' },
        pageHeader({
            eyebrow: subtitle,
            title: 'Staff',
            actions: [el('button', { class: 'btn btn-primary', type: 'button', onclick: () => openForm() }, icon('plus', 18), 'Add staff')],
        }),
        el('div', { class: 'role-cards' },
            Object.entries(ROLE_LABELS).map(([value, label]) => el('div', { class: 'card role-card' },
                el('span', { class: `role-icon ${value}` }, icon(value === 'admin' ? 'shield' : 'cart')),
                el('div', {}, el('strong', {}, label), el('p', { class: 'muted small' }, ROLE_HELP[value]))))),
        el('section', { class: 'card' },
            el('div', { class: 'table-wrap' },
                el('table', { class: 'table' },
                    el('thead', {}, el('tr', {},
                        el('th', {}, 'Name'), el('th', {}, 'Role'), el('th', {}, 'Status'),
                        el('th', { class: 'hide-sm' }, 'Last sign-in'), el('th', { class: 'actions' }, el('span', { class: 'visually-hidden' }, 'Actions')))),
                    users.length ? tbody : emptyState({ iconName: 'users', title: 'No staff yet' })))));
}
