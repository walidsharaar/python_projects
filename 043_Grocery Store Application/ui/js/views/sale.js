import { api } from '../api.js';
import { icon } from '../icons.js';
import { el, emptyState, money, pageHeader, plural, productAvatar, quantity, roundTo2, searchInput, shake, toast } from '../ui.js';

const MAX_QUANTITY = 99999;

// Point-of-sale screen: tap product tiles to fill the cart, then complete the sale
export async function saleView() {
    const { items: products } = await api.products.list();
    const productsById = new Map(products.map((product) => [product.id, product]));
    const cart = new Map(); // product id -> quantity
    let search = '';

    if (!products.length) {
        return el('div', { class: 'page' },
            pageHeader({ title: 'New sale' }),
            el('div', { class: 'card' }, emptyState({
                iconName: 'package',
                title: 'No products yet',
                text: 'Add the products you sell first.',
                action: el('a', { class: 'btn btn-primary', href: '#/products' }, icon('plus', 18), 'Add products'),
            })));
    }

    const grid = el('div', { class: 'product-grid' });
    const lines = el('div', { class: 'cart-lines' });
    const totalValue = el('span', { class: 'cart-total-value' });
    const itemCount = el('span', { class: 'muted small' });
    const customer = el('input', { class: 'input', id: 'customer-name', placeholder: 'e.g. Alice Johnson', maxlength: '255', autocomplete: 'off' });
    const submit = el('button', { class: 'btn btn-primary btn-lg btn-block', type: 'submit' }, icon('check'), 'Complete sale');
    const clear = el('button', { class: 'btn btn-ghost', type: 'button', onclick: () => { cart.clear(); render(); } }, 'Clear');

    const productSearch = searchInput({
        placeholder: 'Search products…  (Enter adds the first match)',
        onInput: (value) => { search = value.toLowerCase(); renderGrid(); },
    });
    productSearch.input.addEventListener('keydown', (event) => {
        const first = visibleProducts()[0];
        if (event.key === 'Enter' && first) {
            event.preventDefault();
            add(first.id);
            productSearch.input.select();
        }
    });

    function visibleProducts() {
        return products.filter((product) => product.name.toLowerCase().includes(search));
    }

    function add(productId, delta = 1) {
        setQuantity(productId, (cart.get(productId) || 0) + delta);
        grid.querySelector(`[data-id="${productId}"]`)?.classList.add('pop');
    }

    function setQuantity(productId, value) {
        const next = roundTo2(Number(value));
        if (!(next > 0)) cart.delete(productId);
        else cart.set(productId, Math.min(next, MAX_QUANTITY));
        render();
    }

    function tile(product) {
        const inCart = cart.get(product.id);
        return el('button', {
            type: 'button',
            class: `tile${inCart ? ' in-cart' : ''}`,
            'data-id': String(product.id),
            'aria-label': `Add ${product.name}, ${money(product.price_per_unit)} per ${product.uom_name}`,
            onclick: () => add(product.id),
            onanimationend: (event) => event.currentTarget.classList.remove('pop'),
        },
        productAvatar(product, { size: 'lg' }),
        el('span', { class: 'tile-name' }, product.name),
        el('span', { class: 'tile-price' }, money(product.price_per_unit), el('small', {}, ` / ${product.uom_name}`)),
        inCart ? el('span', { class: 'tile-badge' }, quantity(inCart)) : null);
    }

    function cartLine(product, amount) {
        return el('div', { class: 'cart-line' },
            el('div', { class: 'cart-line-info' },
                el('span', { class: 'cart-line-name' }, product.icon ? `${product.icon} ${product.name}` : product.name),
                el('span', { class: 'muted small' }, `${money(product.price_per_unit)} / ${product.uom_name}`)),
            el('button', { type: 'button', class: 'icon-btn danger remove', 'aria-label': `Remove ${product.name}`, onclick: () => setQuantity(product.id, 0) }, icon('x', 16)),
            el('div', { class: 'stepper' },
                el('button', { type: 'button', class: 'icon-btn', 'aria-label': `One less ${product.name}`, onclick: () => add(product.id, -1) }, icon('minus', 16)),
                el('input', {
                    type: 'number', class: 'stepper-input', min: '0.01', max: String(MAX_QUANTITY), step: '0.01', value: String(amount),
                    'aria-label': `Quantity of ${product.name} in ${product.uom_name}`,
                    onchange: (event) => setQuantity(product.id, event.target.value),
                }),
                el('button', { type: 'button', class: 'icon-btn', 'aria-label': `One more ${product.name}`, onclick: () => add(product.id) }, icon('plus', 16))),
            el('span', { class: 'cart-line-total' }, money(product.price_per_unit * amount)));
    }

    function renderGrid() {
        const visible = visibleProducts();
        grid.replaceChildren(...(visible.length
            ? visible.map(tile)
            : [emptyState({ iconName: 'search', title: 'No products found', text: 'Try a different search.' })]));
    }

    function renderCart() {
        const entries = [...cart];
        lines.replaceChildren(...(entries.length
            ? entries.map(([id, amount]) => cartLine(productsById.get(id), amount))
            : [emptyState({ iconName: 'cart', title: 'Cart is empty', text: 'Tap a product to add it to this sale.' })]));

        // Preview only: the server recalculates every total from current prices when saving
        const total = entries.reduce((sum, [id, amount]) => sum + roundTo2(productsById.get(id).price_per_unit * amount), 0);
        totalValue.textContent = money(total);
        itemCount.textContent = plural(entries.length, 'item');
        submit.disabled = !entries.length;
        clear.disabled = !entries.length;
    }

    function render() {
        renderGrid();
        renderCart();
    }

    async function completeSale(event) {
        event.preventDefault();
        const customerName = customer.value.trim();
        if (!customerName) {
            shake(customer);
            customer.focus();
            toast('Please enter the customer name', 'error');
            return;
        }

        submit.disabled = true;
        submit.classList.add('loading');
        try {
            const order = await api.orders.create({
                customer_name: customerName,
                items: [...cart].map(([productId, amount]) => ({ product_id: productId, quantity: amount })),
            });
            toast(`Order #${order.id} saved · ${money(order.total)}`);
            location.hash = `#/orders?id=${order.id}`;
        } catch (error) {
            toast(error.message, 'error');
            submit.disabled = false;
            submit.classList.remove('loading');
        }
    }

    render();

    return el('div', { class: 'pos' },
        el('section', { class: 'pos-catalog' },
            pageHeader({ eyebrow: plural(products.length, 'product'), title: 'New sale' }),
            productSearch.wrapper,
            grid),
        el('form', { class: 'card pos-cart', onsubmit: completeSale, novalidate: true },
            el('div', { class: 'cart-header' }, el('h2', {}, 'Current sale'), clear),
            el('div', { class: 'cart-customer field' }, el('label', { for: 'customer-name' }, 'Customer'), customer),
            lines,
            el('div', { class: 'cart-footer' },
                el('div', { class: 'cart-total' }, el('div', {}, el('div', { class: 'muted small' }, 'Total'), itemCount), totalValue),
                submit)));
}
