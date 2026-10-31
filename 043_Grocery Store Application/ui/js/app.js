import { api } from './api.js';
import { ROLE_LABELS, allowed, getUser, setUser } from './auth.js';
import { icon } from './icons.js';
import { avatar, el, errorState, loadingView, toast } from './ui.js';
import { changePasswordDialog } from './views/account.js';
import { dashboardView } from './views/dashboard.js';
import { renderLogin } from './views/login.js';
import { ordersView } from './views/orders.js';
import { productsView } from './views/products.js';
import { saleView } from './views/sale.js';
import { usersView } from './views/users.js';

// roles: who may open the page (the server enforces the same rules for the data)
const routes = {
    dashboard: { title: 'Dashboard', view: dashboardView, roles: 'admin' },
    sale: { title: 'New Sale', view: saleView },
    orders: { title: 'Orders', view: ordersView },
    products: { title: 'Products', view: productsView, roles: 'admin' },
    users: { title: 'Staff', view: usersView, roles: 'admin' },
};

const homeRoute = () => (allowed('admin') ? 'dashboard' : 'sale');

const root = document.getElementById('view');
const appShell = document.getElementById('app');
const loginShell = document.getElementById('login');
let navigationId = 0;

// Hash routes: #/orders?id=12 -> view "orders" with params { id: 12 }
async function navigate() {
    if (!getUser()) return;

    const [path, queryString = ''] = location.hash.replace(/^#\/?/, '').split('?');
    if (!routes[path] || !allowed(routes[path].roles)) {
        history.replaceState(null, '', `#/${homeRoute()}`);
    }
    const name = routes[path] && allowed(routes[path].roles) ? path : homeRoute();
    const id = ++navigationId;

    document.querySelectorAll('[data-route]').forEach((link) => {
        const active = link.dataset.route === name;
        link.classList.toggle('active', active);
        if (active) link.setAttribute('aria-current', 'page'); else link.removeAttribute('aria-current');
    });
    document.title = `${routes[name].title} · FreshCart`;
    root.replaceChildren(loadingView());

    let content;
    try {
        content = await routes[name].view(new URLSearchParams(queryString));
    } catch (error) {
        console.error(error);
        content = errorState(error, navigate);
    }

    // Ignore results of a page the user already navigated away from
    if (id === navigationId && getUser()) {
        root.replaceChildren(content);
        window.scrollTo(0, 0);
    }
}

// --- Signed in / signed out ---

function showApp(user) {
    setUser(user);
    document.querySelectorAll('[data-roles]').forEach((node) => { node.hidden = !allowed(node.dataset.roles); });
    renderUserCard();
    loginShell.hidden = true;
    loginShell.replaceChildren();
    appShell.hidden = false;
    navigate();
}

function showLogin(message) {
    setUser(null);
    navigationId++;
    document.querySelectorAll('dialog[open]').forEach((dialog) => dialog.close());
    appShell.hidden = true;
    root.replaceChildren();
    loginShell.hidden = false;
    renderLogin(loginShell, { message, onSuccess: showApp });
}

async function logout() {
    try {
        await api.auth.logout();
    } finally {
        showLogin('You have been signed out.');
    }
}

function renderUserCard() {
    const user = getUser();
    document.getElementById('user-card').replaceChildren(
        el('div', { class: 'with-avatar' },
            avatar(user.full_name, { round: true }),
            el('div', { class: 'stack' },
                el('span', { class: 'name' }, user.full_name),
                el('span', { class: `role-badge ${user.role}` }, ROLE_LABELS[user.role]))),
        el('div', { class: 'user-card-actions' },
            el('button', { type: 'button', class: 'btn btn-ghost', title: 'Change password', onclick: changePasswordDialog }, icon('key', 16), 'Password'),
            el('button', { type: 'button', class: 'btn btn-ghost', title: 'Sign out', 'aria-label': 'Sign out', onclick: logout }, icon('logout', 16), 'Sign out')));
}

// --- Theme ---

function currentTheme() {
    return document.documentElement.dataset.theme
        || (window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light');
}

function renderThemeToggles() {
    const next = currentTheme() === 'dark' ? 'light' : 'dark';
    document.querySelectorAll('.theme-toggle').forEach((button) => {
        const label = next === 'dark' ? 'Dark mode' : 'Light mode';
        button.replaceChildren(icon(next === 'dark' ? 'moon' : 'sun'));
        if (button.classList.contains('nav-secondary')) button.append(label);
        button.setAttribute('aria-label', `Switch to ${label.toLowerCase()}`);
    });
}

function toggleTheme() {
    const theme = currentTheme() === 'dark' ? 'light' : 'dark';
    document.documentElement.dataset.theme = theme;
    try { localStorage.setItem('theme', theme); } catch { /* not persisted, still applied */ }
    renderThemeToggles();
}

// --- Start ---

document.querySelectorAll('[data-icon]').forEach((slot) => slot.replaceWith(icon(slot.dataset.icon)));
document.querySelectorAll('.theme-toggle').forEach((button) => button.addEventListener('click', toggleTheme));
document.querySelectorAll('[data-action="logout"]').forEach((button) => button.addEventListener('click', logout));
window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', renderThemeToggles);
renderThemeToggles();

window.addEventListener('hashchange', navigate);
window.addEventListener('auth:expired', () => {
    if (getUser()) {
        toast('Your session has ended. Please sign in again.', 'error');
        showLogin();
    }
});

(async () => {
    try {
        showApp(await api.auth.me());
    } catch {
        showLogin();
    } finally {
        document.getElementById('boot').remove();
    }
})();
