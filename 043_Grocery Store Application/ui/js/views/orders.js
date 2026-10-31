import { api } from '../api.js';
import { icon } from '../icons.js';
import { avatar, debounce, el, emptyState, formatDateTime, money, openDialog, pageHeader, plural, quantity, searchInput, toast } from '../ui.js';

const PAGE_SIZE = 15;

export async function ordersView(params) {
    const state = { search: '', offset: 0 };
    const tbody = el('tbody');
    const pager = el('div', { class: 'pager' });
    const subtitle = el('span');

    const orderSearch = searchInput({
        placeholder: 'Search customer or #order',
        onInput: debounce((value) => {
            state.search = value;
            state.offset = 0;
            load();
        }),
    });

    async function load() {
        tbody.setAttribute('aria-busy', 'true');
        try {
            render(await api.orders.list({ limit: PAGE_SIZE, offset: state.offset, q: state.search }));
        } catch (error) {
            toast(error.message, 'error');
        } finally {
            tbody.removeAttribute('aria-busy');
        }
    }

    function render(page) {
        subtitle.textContent = state.search ? `${plural(page.total, 'match')} for “${state.search}”` : plural(page.total, 'order');

        if (!page.items.length) {
            tbody.replaceChildren(el('tr', {}, el('td', { colspan: '6' }, emptyState(state.search
                ? { iconName: 'search', title: 'No matching orders', text: 'Try another name or order number.' }
                : { iconName: 'receipt', title: 'No orders yet', text: 'Completed sales appear here.',
                    action: el('a', { class: 'btn btn-primary', href: '#/sale' }, 'New sale') }))));
        } else {
            tbody.replaceChildren(...page.items.map(orderRow));
        }

        const from = page.total ? page.offset + 1 : 0;
        const to = page.offset + page.items.length;
        pager.replaceChildren(
            el('span', { class: 'muted' }, `${from}–${to} of ${page.total}`),
            el('div', { class: 'pager-buttons' },
                el('button', {
                    class: 'btn', type: 'button', disabled: page.offset === 0, 'aria-label': 'Previous page',
                    onclick: () => { state.offset = Math.max(0, state.offset - PAGE_SIZE); load(); },
                }, icon('chevronLeft', 18)),
                el('button', {
                    class: 'btn', type: 'button', disabled: to >= page.total, 'aria-label': 'Next page',
                    onclick: () => { state.offset += PAGE_SIZE; load(); },
                }, icon('chevronRight', 18))));
    }

    function orderRow(order) {
        const open = () => openOrder(order.id);
        return el('tr', {
            class: 'clickable', tabindex: '0', 'aria-label': `Open order ${order.id}`,
            onclick: open,
            onkeydown: (event) => { if (event.key === 'Enter' || event.key === ' ') { event.preventDefault(); open(); } },
        },
        el('td', {}, el('span', { class: 'order-id' }, `#${order.id}`)),
        el('td', {}, el('div', { class: 'with-avatar' }, avatar(order.customer_name, { round: true }), el('span', { class: 'name' }, order.customer_name))),
        el('td', { class: 'muted hide-sm' }, formatDateTime(order.created_at)),
        el('td', { class: 'hide-sm' }, el('span', { class: 'chip' }, plural(order.items.length, 'item'))),
        el('td', { class: 'muted hide-sm' }, order.created_by_name || '—'),
        el('td', { class: 'right num' }, el('strong', {}, money(order.total))));
    }

    await load();

    // Deep link from the dashboard or after a sale: #/orders?id=12
    const requestedId = Number(params.get('id'));
    if (requestedId > 0) setTimeout(() => openOrder(requestedId));

    return el('div', { class: 'page' },
        pageHeader({
            eyebrow: subtitle,
            title: 'Orders',
            actions: [orderSearch.wrapper, el('a', { class: 'btn btn-primary', href: '#/sale' }, icon('plus', 18), 'New sale')],
        }),
        el('section', { class: 'card' },
            el('div', { class: 'table-wrap' },
                el('table', { class: 'table' },
                    el('thead', {}, el('tr', {},
                        el('th', {}, 'Order'), el('th', {}, 'Customer'), el('th', { class: 'hide-sm' }, 'Date'),
                        el('th', { class: 'hide-sm' }, 'Items'), el('th', { class: 'hide-sm' }, 'Sold by'), el('th', { class: 'right' }, 'Total'))),
                    tbody)),
            pager));
}

async function openOrder(orderId) {
    let order;
    try {
        order = await api.orders.get(orderId);
    } catch (error) {
        toast(error.message, 'error');
        return;
    }

    const dialog = el('dialog', { class: 'drawer', 'aria-labelledby': 'order-title' },
        el('div', { class: 'drawer-panel' },
            el('header', { class: 'drawer-header' },
                el('div', {}, el('div', { class: 'muted small' }, formatDateTime(order.created_at)), el('h2', { id: 'order-title' }, `Order #${order.id}`)),
                el('button', { class: 'icon-btn', type: 'button', 'aria-label': 'Close', onclick: () => dialog.close() }, icon('x'))),
            el('div', { class: 'drawer-body' },
                el('div', { class: 'with-avatar' },
                    avatar(order.customer_name, { size: 'lg', round: true }),
                    el('div', { class: 'stack' }, el('span', { class: 'muted small' }, 'Customer'), el('strong', {}, order.customer_name)),
                    order.created_by_name ? el('div', { class: 'stack sold-by' }, el('span', { class: 'muted small' }, 'Sold by'), el('strong', {}, order.created_by_name)) : null),
                el('div', { class: 'receipt' },
                    order.items.map((item) => el('div', { class: 'receipt-line' },
                        el('div', { class: 'stack' },
                            el('strong', {}, item.product_icon ? `${item.product_icon} ${item.product_name}` : item.product_name),
                            el('span', { class: 'muted' }, `${quantity(item.quantity)} ${item.uom_name} × ${money(item.unit_price)}`)),
                        el('strong', { class: 'num' }, money(item.total)))),
                    el('div', { class: 'receipt-total' }, el('span', {}, 'Total'), el('strong', {}, money(order.total)))),
                el('p', { class: 'note' }, icon('info', 16), 'Prices are the prices at the time of sale.')),
            el('footer', { class: 'drawer-footer' },
                el('button', { class: 'btn', type: 'button', onclick: () => window.print() }, icon('printer', 18), 'Print receipt'),
                el('button', { class: 'btn btn-primary', type: 'button', onclick: () => dialog.close(), style: { marginLeft: 'auto' } }, 'Done'))));

    // Drop ?id= from the address when closing, without reloading the list
    dialog.addEventListener('close', () => {
        if (location.hash.includes('?')) history.replaceState(null, '', '#/orders');
    });
    openDialog(dialog);
}
