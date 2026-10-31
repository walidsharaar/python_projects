import { api } from '../api.js';
import { icon } from '../icons.js';
import { el, shake } from '../ui.js';

// Decorative produce floating on the welcome panel
const FLOATING = ['🍅', '🥕', '🍎', '🥖', '🥛', '🍌', '🧀', '🥦', '🍇', '🥚', '🍊', '🫐'];

export function renderLogin(container, { message, onSuccess }) {
    const error = el('div', { class: 'alert', role: 'alert', hidden: !message || undefined }, message || '');
    if (message) error.classList.add('alert-info');

    const username = el('input', { class: 'input', id: 'login-username', name: 'username', autocomplete: 'username', required: true, autocapitalize: 'none', spellcheck: 'false' });
    const password = el('input', { class: 'input', id: 'login-password', name: 'password', type: 'password', autocomplete: 'current-password', required: true });
    const reveal = el('button', {
        type: 'button', class: 'icon-btn input-suffix', 'aria-label': 'Show password',
        onclick: () => {
            const visible = password.type === 'text';
            password.type = visible ? 'password' : 'text';
            reveal.replaceChildren(icon(visible ? 'eye' : 'eyeOff', 18));
            reveal.setAttribute('aria-label', visible ? 'Show password' : 'Hide password');
        },
    }, icon('eye', 18));
    const submit = el('button', { class: 'btn btn-primary btn-lg btn-block', type: 'submit' }, 'Sign in', icon('arrowRight', 18));

    async function signIn(event) {
        event.preventDefault();
        error.hidden = true;
        error.classList.remove('alert-info');
        if (!username.value.trim()) { shake(username); username.focus(); return; }
        if (!password.value) { shake(password); password.focus(); return; }

        submit.disabled = true;
        submit.classList.add('loading');
        try {
            const user = await api.auth.login(username.value.trim(), password.value);
            onSuccess(user);
        } catch (requestError) {
            error.textContent = requestError.message;
            error.hidden = false;
            password.value = '';
            shake(form);
            password.focus();
            submit.disabled = false;
            submit.classList.remove('loading');
        }
    }

    const form = el('form', { class: 'login-form', novalidate: true, onsubmit: signIn },
        el('div', { class: 'login-heading' },
            el('span', { class: 'brand-mark' }, icon('leaf')),
            el('h1', {}, 'Welcome back'),
            el('p', { class: 'muted' }, 'Sign in to FreshCart to continue.')),
        error,
        el('div', { class: 'field' }, el('label', { for: 'login-username' }, 'Username'),
            el('div', { class: 'input-group' }, el('span', { class: 'prefix' }, icon('user', 18)), username)),
        el('div', { class: 'field' }, el('label', { for: 'login-password' }, 'Password'),
            el('div', { class: 'input-group' }, el('span', { class: 'prefix' }, icon('lock', 18)), password, reveal)),
        submit,
        el('p', { class: 'login-hint muted small' }, icon('shield', 14), 'Forgot your password? Ask an administrator to reset it.'));

    const hero = el('section', { class: 'login-hero', 'aria-hidden': 'true' },
        // Scatter the emoji over the top half of the panel, the text sits at the bottom
        el('div', { class: 'login-floating' }, FLOATING.map((emoji, index) =>
            el('span', { style: { '--i': String(index), left: `${6 + ((index * 37) % 88)}%`, top: `${5 + ((index * 23) % 52)}%` } }, emoji))),
        el('div', { class: 'login-hero-text' },
            el('div', { class: 'brand' }, el('span', { class: 'brand-mark' }, icon('leaf')), 'FreshCart'),
            el('h2', {}, 'Fresh sales,', el('br'), 'fresh insights.'),
            el('p', {}, 'Ring up sales in seconds, keep your products and prices tidy, and see how your store is doing at a glance.'),
            el('ul', { class: 'login-features' },
                el('li', {}, icon('cart', 18), 'Fast point of sale'),
                el('li', {}, icon('trending', 18), 'Live sales dashboard'),
                el('li', {}, icon('users', 18), 'Staff accounts & roles'))));

    container.replaceChildren(el('div', { class: 'login-page' }, hero, el('section', { class: 'login-panel' }, form)));
    username.focus();
}
