import { api } from '../api.js';
import { ROLE_LABELS, getUser } from '../auth.js';
import { icon } from '../icons.js';
import { avatar, card, el, emptyState, formatRelative, loadingView, money, pageHeader, plural, productAvatar, quantity, toast } from '../ui.js';

const PERIODS = [{ days: 7, label: '7 days' }, { days: 30, label: '30 days' }, { days: 90, label: '90 days' }];
const WEEKDAYS = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'];
const SVG_NS = 'http://www.w3.org/2000/svg';
let selectedDays = 30;

export async function dashboardView() {
    const content = el('div', { class: 'dashboard-content' });
    const periodButtons = el('div', { class: 'segmented', role: 'radiogroup', 'aria-label': 'Period' });

    function renderPeriodButtons() {
        periodButtons.replaceChildren(...PERIODS.map((period) => el('button', {
            type: 'button', role: 'radio', 'aria-checked': String(period.days === selectedDays),
            class: period.days === selectedDays ? 'active' : '',
            onclick: () => { selectedDays = period.days; renderPeriodButtons(); load(); },
        }, period.label)));
    }

    async function load() {
        content.classList.add('is-loading');
        try {
            const [stats, recent] = await Promise.all([api.stats.summary(selectedDays), api.orders.list({ limit: 6 })]);
            content.replaceChildren(...renderDashboard(stats, recent.items));
        } catch (error) {
            toast(error.message, 'error');
        } finally {
            content.classList.remove('is-loading');
        }
    }

    renderPeriodButtons();
    content.replaceChildren(...loadingView().children);
    await load();

    return el('div', { class: 'page' },
        pageHeader({
            eyebrow: new Intl.DateTimeFormat(undefined, { weekday: 'long', day: 'numeric', month: 'long' }).format(new Date()),
            title: `${greeting()}, ${getUser().full_name.split(' ')[0]}`,
            actions: [periodButtons, el('a', { class: 'btn btn-primary', href: '#/sale' }, icon('cart', 18), 'New sale')],
        }),
        content);
}

function renderDashboard(stats, recentOrders) {
    const { current, previous } = stats;
    const vs = `vs. previous ${stats.days} days`;
    return [
        el('section', { class: 'kpis' },
            kpi({ label: 'Revenue', value: money(current.revenue), iconName: 'wallet', color: 'green', change: delta(current.revenue, previous.revenue), vs }),
            kpi({ label: 'Orders', value: quantity(current.orders), iconName: 'receipt', color: 'blue', change: delta(current.orders, previous.orders), vs }),
            kpi({ label: 'Average order', value: money(current.average_order_value), iconName: 'trending', color: 'amber',
                change: delta(current.average_order_value, previous.average_order_value), vs }),
            kpi({ label: 'Customers', value: quantity(current.customers), iconName: 'users', color: 'violet', change: delta(current.customers, previous.customers), vs })),
        el('div', { class: 'grid-dashboard' },
            card({ title: 'Revenue', subtitle: `Daily, last ${stats.days} days`, body: revenueChart(stats.daily_sales) }),
            card({ title: 'Top products', subtitle: 'By revenue', body: topProducts(stats.top_products),
                action: el('a', { class: 'link', href: '#/products' }, `${stats.product_count} products`, icon('arrowRight', 14)) })),
        el('div', { class: 'grid-dashboard' },
            card({ title: 'Busiest hours', subtitle: 'Orders by weekday and time of day', body: heatmap(stats.busiest_hours) }),
            card({ title: 'Top customers', subtitle: 'By revenue', body: topCustomers(stats.top_customers) })),
        el('div', { class: 'grid-dashboard even' },
            card({ title: 'Sales by staff', subtitle: `Last ${stats.days} days`, body: salesByStaff(stats.sales_by_staff),
                action: el('a', { class: 'link', href: '#/users' }, 'Manage staff', icon('arrowRight', 14)) }),
            card({ title: 'Recent orders', body: recentOrderList(recentOrders),
                action: el('a', { class: 'link', href: '#/orders' }, 'View all', icon('arrowRight', 16)) })),
    ];
}

function greeting() {
    const hour = new Date().getHours();
    if (hour < 12) return 'Good morning';
    if (hour < 18) return 'Good afternoon';
    return 'Good evening';
}

function delta(current, previous) {
    if (!previous) return current ? null : 0;
    return Math.round(((current - previous) / previous) * 100);
}

function kpi({ label, value, iconName, color, change, vs }) {
    const trend = change === null
        ? el('span', { class: 'trend up' }, 'New')
        : el('span', { class: `trend ${change >= 0 ? 'up' : 'down'}` }, icon(change >= 0 ? 'arrowUp' : 'arrowDown', 12), `${Math.abs(change)}%`);
    return el('article', { class: 'card kpi' },
        el('div', { class: 'kpi-top' }, el('span', {}, label), el('span', { class: `kpi-icon ${color}` }, icon(iconName))),
        el('div', { class: 'kpi-value' }, value),
        el('div', { class: 'kpi-foot' }, trend, vs));
}

function svg(tag, attrs = {}, ...children) {
    const node = document.createElementNS(SVG_NS, tag);
    for (const [key, value] of Object.entries(attrs)) node.setAttribute(key, value);
    node.append(...children);
    return node;
}

// Area chart with a hover crosshair; one point per day
function revenueChart(days) {
    const width = 720;
    const height = 240;
    const pad = { top: 16, right: 12, bottom: 28, left: 12 };
    const plotWidth = width - pad.left - pad.right;
    const plotHeight = height - pad.top - pad.bottom;
    const max = Math.max(...days.map((day) => day.revenue), 1) * 1.1;
    const x = (index) => pad.left + (days.length === 1 ? plotWidth / 2 : (index / (days.length - 1)) * plotWidth);
    const y = (value) => pad.top + plotHeight - (value / max) * plotHeight;
    const points = days.map((day, index) => [x(index), y(day.revenue)]);
    const line = points.map(([px, py], index) => `${index ? 'L' : 'M'}${px.toFixed(1)},${py.toFixed(1)}`).join(' ');
    const area = `${line} L${x(days.length - 1).toFixed(1)},${pad.top + plotHeight} L${x(0).toFixed(1)},${pad.top + plotHeight} Z`;
    const short = new Intl.DateTimeFormat(undefined, { day: 'numeric', month: 'short' });
    const long = new Intl.DateTimeFormat(undefined, { weekday: 'long', day: 'numeric', month: 'long' });
    const labelEvery = Math.ceil(days.length / 7);

    const chart = svg('svg', { viewBox: `0 0 ${width} ${height}`, role: 'img', 'aria-label': `Daily revenue for the last ${days.length} days` },
        svg('defs', {}, svg('linearGradient', { id: 'area-fill', x1: 0, y1: 0, x2: 0, y2: 1 },
            svg('stop', { offset: '0%', class: 'area-stop-top' }), svg('stop', { offset: '100%', class: 'area-stop-bottom' }))));
    for (const ratio of [0, 0.25, 0.5, 0.75, 1]) {
        const lineY = pad.top + plotHeight * ratio;
        chart.append(svg('line', { class: 'grid-line', x1: pad.left, x2: width - pad.right, y1: lineY, y2: lineY }));
    }
    chart.append(svg('path', { class: 'area', d: area, fill: 'url(#area-fill)' }), svg('path', { class: 'line', d: line }));

    days.forEach((day, index) => {
        const fromEnd = days.length - 1 - index;
        if (fromEnd % labelEvery === 0) {
            const date = new Date(`${day.date}T00:00:00`);
            chart.append(svg('text', { class: 'axis-label', x: x(index), y: height - 6, 'text-anchor': 'middle' },
                fromEnd === 0 ? 'Today' : short.format(date)));
        }
    });

    const crosshair = svg('line', { class: 'crosshair', y1: pad.top, y2: pad.top + plotHeight, visibility: 'hidden' });
    const dot = svg('circle', { class: 'dot', r: 5, visibility: 'hidden' });
    chart.append(crosshair, dot);

    const tooltip = el('div', { class: 'chart-tooltip', role: 'presentation' });
    const slot = plotWidth / Math.max(days.length - 1, 1);
    days.forEach((day, index) => {
        const hit = svg('rect', { class: 'hit', x: x(index) - slot / 2, y: 0, width: slot, height, fill: 'transparent' });
        const show = () => {
            const [px, py] = points[index];
            for (const [attr, value] of [['x1', px], ['x2', px]]) crosshair.setAttribute(attr, value);
            crosshair.setAttribute('visibility', 'visible');
            dot.setAttribute('cx', px);
            dot.setAttribute('cy', py);
            dot.setAttribute('visibility', 'visible');
            tooltip.replaceChildren(el('strong', {}, money(day.revenue)),
                `${plural(day.orders, 'order')} · ${long.format(new Date(`${day.date}T00:00:00`))}`);
            tooltip.style.left = `${(px / width) * 100}%`;
            tooltip.style.top = `${(py / height) * 100}%`;
            tooltip.classList.add('visible');
        };
        hit.addEventListener('mouseenter', show);
        hit.addEventListener('click', show);
        chart.append(hit);
    });
    chart.addEventListener('mouseleave', () => {
        tooltip.classList.remove('visible');
        crosshair.setAttribute('visibility', 'hidden');
        dot.setAttribute('visibility', 'hidden');
    });

    const total = days.reduce((sum, day) => sum + day.revenue, 0);
    const best = days.reduce((top, day) => (day.revenue > top.revenue ? day : top), days[0]);
    return el('div', {},
        el('div', { class: 'chart-summary' },
            el('div', {}, el('strong', {}, money(total)), el('span', {}, 'Total')),
            el('div', {}, el('strong', {}, money(total / days.length)), el('span', {}, 'Per day')),
            best?.revenue ? el('div', {}, el('strong', {}, money(best.revenue)),
                el('span', {}, `Best day · ${short.format(new Date(`${best.date}T00:00:00`))}`)) : null),
        el('div', { class: 'chart' }, chart, tooltip));
}

function heatmap(cells) {
    if (!cells.length) {
        return emptyState({ iconName: 'clock', title: 'No sales in this period', text: 'Busy times will show up here.' });
    }
    const counts = new Map(cells.map((cell) => [`${cell.weekday}-${cell.hour}`, cell.orders]));
    const max = Math.max(...cells.map((cell) => cell.orders));
    const firstHour = Math.min(8, ...cells.map((cell) => cell.hour));
    const lastHour = Math.max(20, ...cells.map((cell) => cell.hour));
    const hours = Array.from({ length: lastHour - firstHour + 1 }, (_, index) => firstHour + index);
    const busiest = cells.reduce((top, cell) => (cell.orders > top.orders ? cell : top));

    const grid = el('div', { class: 'heatmap', style: { '--columns': String(hours.length) }, role: 'table', 'aria-label': 'Orders by weekday and hour' },
        el('span', { class: 'heatmap-corner' }),
        hours.map((hour) => el('span', { class: 'heatmap-hour' }, hour % 3 === 0 ? String(hour).padStart(2, '0') : '')),
        WEEKDAYS.map((name, dayIndex) => [
            el('span', { class: 'heatmap-day' }, name),
            hours.map((hour) => {
                const count = counts.get(`${dayIndex + 1}-${hour}`) || 0;
                return el('span', {
                    class: 'heatmap-cell',
                    style: { '--level': String(count ? 0.18 + 0.82 * (count / max) : 0) },
                    title: `${name} ${String(hour).padStart(2, '0')}:00 – ${plural(count, 'order')}`,
                });
            }),
        ]));

    return el('div', {},
        el('div', { class: 'scroll-x' }, grid),
        el('div', { class: 'heatmap-footer' },
            el('span', { class: 'muted small' }, icon('star', 14), ` Busiest: ${WEEKDAYS[busiest.weekday - 1]} around ${String(busiest.hour).padStart(2, '0')}:00`),
            el('span', { class: 'heatmap-legend' }, 'Less', [0.18, 0.45, 0.72, 1].map((level) =>
                el('span', { class: 'heatmap-cell', style: { '--level': String(level) } })), 'More')));
}

function rankList(rows, { emptyIcon, emptyTitle }) {
    if (!rows.length) return emptyState({ iconName: emptyIcon, title: emptyTitle, text: 'Nothing in this period yet.' });
    const max = rows[0].value || 1;
    return el('ol', { class: 'rank-list' }, rows.map((row) =>
        el('li', { class: 'rank-item' },
            el('div', { class: 'rank-row' },
                el('div', { class: 'with-avatar' }, row.avatar,
                    el('div', { class: 'stack' }, el('span', { class: 'name' }, row.title), el('span', { class: 'sub' }, row.subtitle))),
                el('strong', { class: 'num' }, money(row.value))),
            el('div', { class: 'meter', 'aria-hidden': 'true' }, el('span', { style: { width: `${(row.value / max) * 100}%` } })))));
}

function topProducts(products) {
    return rankList(products.map((product) => ({
        avatar: productAvatar(product),
        title: product.name,
        subtitle: `${quantity(product.quantity)} ${product.uom_name} sold`,
        value: product.revenue,
    })), { emptyIcon: 'package', emptyTitle: 'No sales yet' });
}

function topCustomers(customers) {
    return rankList(customers.map((customer) => ({
        avatar: avatar(customer.name, { round: true }),
        title: customer.name,
        subtitle: `${plural(customer.orders, 'order')} · last ${formatRelative(customer.last_order_at)}`,
        value: customer.revenue,
    })), { emptyIcon: 'users', emptyTitle: 'No customers yet' });
}

function salesByStaff(staff) {
    if (!staff.length) {
        return emptyState({ iconName: 'users', title: 'No staff sales yet', text: 'Sales made by signed-in staff appear here.' });
    }
    return rankList(staff.map((member) => ({
        avatar: avatar(member.name, { round: true }),
        title: member.name,
        subtitle: `${ROLE_LABELS[member.role]} · ${plural(member.orders, 'sale')}`,
        value: member.revenue,
    })), {});
}

function recentOrderList(orders) {
    if (!orders.length) {
        return emptyState({
            iconName: 'receipt', title: 'No orders yet', text: 'Your first sale is one click away.',
            action: el('a', { class: 'btn btn-primary', href: '#/sale' }, 'New sale'),
        });
    }
    return el('ul', { class: 'activity-list' }, orders.map((order) =>
        el('li', { class: 'activity-item' },
            el('a', { href: `#/orders?id=${order.id}` },
                el('div', { class: 'with-avatar' },
                    avatar(order.customer_name, { round: true }),
                    el('div', { class: 'stack' },
                        el('span', { class: 'name' }, order.customer_name),
                        el('span', { class: 'sub' }, `#${order.id} · ${order.items.map((item) => item.product_icon || '').join('')} ${plural(order.items.length, 'item')}`))),
                el('div', { class: 'activity-meta' },
                    el('strong', {}, money(order.total)),
                    el('span', {}, formatRelative(order.created_at)))))));
}
