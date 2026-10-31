import { CURRENCY } from './config.js';
import { icon } from './icons.js';

// --- DOM ---

/**
 * Create an element. Children that are not Nodes become text nodes, so data from the
 * server is never interpreted as HTML.
 */
export function el(tag, props = {}, ...children) {
    const node = document.createElement(tag);
    for (const [key, value] of Object.entries(props)) {
        if (value === null || value === undefined || value === false) continue;
        if (key === 'class') node.className = value;
        else if (key === 'style' && typeof value === 'object') {
            // setProperty also handles CSS custom properties such as --hue
            for (const [name, styleValue] of Object.entries(value)) {
                node.style.setProperty(name.startsWith('--') ? name : name.replace(/[A-Z]/g, (c) => `-${c.toLowerCase()}`), styleValue);
            }
        }
        else if (key.startsWith('on')) node.addEventListener(key.slice(2), value);
        else if (key in node && typeof value !== 'string') node[key] = value;
        else node.setAttribute(key, value === true ? '' : value);
    }
    node.append(...children.flat(Infinity)
        .filter((child) => child !== null && child !== undefined && child !== false)
        .map((child) => (child instanceof Node ? child : document.createTextNode(String(child)))));
    return node;
}

export function debounce(fn, wait = 250) {
    let timer;
    return (...args) => {
        clearTimeout(timer);
        timer = setTimeout(() => fn(...args), wait);
    };
}

// --- Formatting ---

const moneyFormat = new Intl.NumberFormat(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 });
const quantityFormat = new Intl.NumberFormat(undefined, { maximumFractionDigits: 2 });
const dateTimeFormat = new Intl.DateTimeFormat(undefined, { dateStyle: 'medium', timeStyle: 'short' });
const relativeFormat = new Intl.RelativeTimeFormat(undefined, { numeric: 'auto' });

export const money = (value) => `${CURRENCY} ${moneyFormat.format(Number(value) || 0)}`;
export const quantity = (value) => quantityFormat.format(Number(value) || 0);
export const formatDateTime = (iso) => dateTimeFormat.format(new Date(iso));
export const roundTo2 = (value) => Math.round(value * 100) / 100;

export function formatRelative(iso) {
    const seconds = (new Date(iso) - Date.now()) / 1000;
    const units = [['day', 86400], ['hour', 3600], ['minute', 60]];
    for (const [unit, size] of units) {
        if (Math.abs(seconds) >= size) return relativeFormat.format(Math.round(seconds / size), unit);
    }
    return 'just now';
}

export const plural = (count, word) => `${quantity(count)} ${word}${Number(count) === 1 ? '' : 's'}`;

// --- Building blocks ---

/** Coloured square with an emoji (products with an icon) or the name's initials. */
export function avatar(name, { size = '', round = false, emoji = null } = {}) {
    const words = String(name).trim().split(/\s+/);
    const initials = (words[0]?.[0] || '?') + (words.length > 1 ? words[words.length - 1][0] : words[0]?.[1] || '');
    let hash = 0;
    for (const char of String(name)) hash = (hash * 31 + char.charCodeAt(0)) % 360;
    return el('span', {
        class: `avatar ${size ? `avatar-${size}` : ''} ${round ? 'avatar-round' : ''} ${emoji ? 'avatar-emoji' : ''}`,
        style: { '--hue': String(hash) },
        'aria-hidden': 'true',
    }, emoji || initials.toUpperCase());
}

export const productAvatar = (product, options = {}) => avatar(product.name, { ...options, emoji: product.icon });

export function pageHeader({ eyebrow, title, actions = [] }) {
    return el('header', { class: 'page-header' },
        el('div', {}, eyebrow ? el('div', { class: 'eyebrow' }, eyebrow) : null, el('h1', {}, title)),
        actions.length ? el('div', { class: 'page-actions' }, actions) : null);
}

export function card({ title, subtitle, action, body, className = '' }) {
    return el('section', { class: `card ${className}` },
        title ? el('div', { class: 'card-header' },
            el('div', {}, el('h2', {}, title), subtitle ? el('div', { class: 'muted' }, subtitle) : null),
            action || null) : null,
        el('div', { class: 'card-body' }, body));
}

export function searchInput({ placeholder, onInput, value = '' }) {
    const input = el('input', { type: 'search', class: 'input', placeholder, 'aria-label': placeholder, value });
    input.addEventListener('input', () => onInput(input.value.trim()));
    return { wrapper: el('div', { class: 'search' }, icon('search', 18), input), input };
}

export function emptyState({ iconName, title, text, action }) {
    return el('div', { class: 'empty' },
        el('span', { class: 'empty-icon' }, icon(iconName, 24)),
        el('strong', {}, title),
        text ? el('span', {}, text) : null,
        action || null);
}

export function loadingView() {
    return el('div', { class: 'page', 'aria-busy': 'true' },
        el('div', { class: 'skeleton', style: { height: '56px', maxWidth: '360px' } }),
        el('div', { class: 'skeleton-grid' }, [1, 2, 3, 4].map(() => el('div', { class: 'skeleton', style: { height: '120px' } }))),
        el('div', { class: 'skeleton', style: { height: '320px' } }));
}

export function errorState(error, retry) {
    return el('div', { class: 'page' }, card({
        body: emptyState({
            iconName: 'alert',
            title: 'Something went wrong',
            text: error.message || String(error),
            action: el('button', { class: 'btn', type: 'button', onclick: retry }, icon('refresh', 18), 'Try again'),
        }),
    }));
}

export function shake(node) {
    node.classList.remove('shake');
    void node.offsetWidth; // restart the animation
    node.classList.add('shake');
    node.addEventListener('animationend', () => node.classList.remove('shake'), { once: true });
}

// --- Feedback ---

export function toast(message, type = 'success') {
    const node = el('div', { class: `toast ${type}` }, icon(type === 'error' ? 'alert' : 'check', 18), el('span', {}, message));
    document.getElementById('toasts').append(node);
    setTimeout(() => {
        node.classList.add('leaving');
        node.addEventListener('animationend', () => node.remove(), { once: true });
    }, type === 'error' ? 5000 : 3200);
}

/** Show a native <dialog>; it is removed from the page when closed. */
export function openDialog(dialog) {
    document.body.append(dialog);
    // Clicking the backdrop (the dialog element itself, outside its card) closes it
    dialog.addEventListener('click', (event) => { if (event.target === dialog) dialog.close(); });
    dialog.addEventListener('close', () => dialog.remove());
    dialog.showModal();
    return dialog;
}

export function confirmDialog({ title, message, confirmText = 'Confirm', danger = false }) {
    return new Promise((resolve) => {
        let confirmed = false;
        const dialog = el('dialog', { 'aria-labelledby': 'confirm-title' },
            el('div', { class: 'modal-card' },
                el('div', { class: 'modal-body', style: { paddingTop: '24px' } },
                    danger ? el('span', { class: 'confirm-icon' }, icon('trash', 22)) : null,
                    el('h2', { id: 'confirm-title' }, title),
                    message ? el('p', {}, message) : null),
                el('div', { class: 'modal-footer' },
                    el('button', { class: 'btn', type: 'button', onclick: () => dialog.close() }, 'Cancel'),
                    el('button', {
                        class: `btn ${danger ? 'btn-danger' : 'btn-primary'}`,
                        type: 'button',
                        onclick: () => { confirmed = true; dialog.close(); },
                    }, confirmText))));
        dialog.addEventListener('close', () => resolve(confirmed));
        openDialog(dialog);
    });
}
