import { api } from '../api.js';
import { CURRENCY } from '../config.js';
import { PRODUCT_EMOJIS, suggestEmoji } from '../emoji.js';
import { icon } from '../icons.js';
import { confirmDialog, el, emptyState, money, openDialog, pageHeader, plural, productAvatar, searchInput, shake, toast } from '../ui.js';

// Each form gets its own element ids: a closing dialog can still be in the page while the next one opens
let formCounter = 0;

export async function productsView() {
    const [{ items: uoms }, { items: initialProducts }] = await Promise.all([api.uoms.list(), api.products.list()]);
    let products = initialProducts;
    let search = '';

    const tbody = el('tbody');
    const subtitle = el('span');
    const productSearch = searchInput({
        placeholder: 'Search products',
        onInput: (value) => { search = value.toLowerCase(); render(); },
    });

    async function reload() {
        try {
            products = (await api.products.list()).items;
            render();
        } catch (error) {
            toast(error.message, 'error');
        }
    }

    function render() {
        const visible = products.filter((product) => product.name.toLowerCase().includes(search));
        subtitle.textContent = plural(products.length, 'product');

        if (!visible.length) {
            tbody.replaceChildren(el('tr', {}, el('td', { colspan: '4' }, emptyState(search
                ? { iconName: 'search', title: 'No products found', text: 'Try a different search.' }
                : { iconName: 'package', title: 'No products yet', text: 'Add the products you sell.',
                    action: el('button', { class: 'btn btn-primary', type: 'button', onclick: () => openForm() }, icon('plus', 18), 'Add product') }))));
            return;
        }

        tbody.replaceChildren(...visible.map((product) => el('tr', {},
            el('td', {}, el('div', { class: 'with-avatar' }, productAvatar(product), el('span', { class: 'name' }, product.name))),
            el('td', {}, el('span', { class: 'chip' }, product.uom_name)),
            el('td', { class: 'right num' }, el('strong', {}, money(product.price_per_unit)), el('span', { class: 'muted small' }, ` / ${product.uom_name}`)),
            el('td', { class: 'actions' },
                el('button', { class: 'icon-btn', type: 'button', title: 'Edit', 'aria-label': `Edit ${product.name}`, onclick: () => openForm(product) }, icon('pencil', 18)),
                el('button', { class: 'icon-btn danger', type: 'button', title: 'Delete', 'aria-label': `Delete ${product.name}`, onclick: () => remove(product) }, icon('trash', 18))))));
    }

    async function remove(product) {
        const confirmed = await confirmDialog({
            title: `Delete ${product.name}?`,
            message: 'The product is removed from your catalog. Products that are part of past orders cannot be deleted.',
            confirmText: 'Delete',
            danger: true,
        });
        if (!confirmed) return;

        try {
            await api.products.remove(product.id);
            toast(`${product.name} deleted`);
            await reload();
        } catch (error) {
            toast(error.message, 'error');
        }
    }

    // One dialog for both adding (no product) and editing (product given)
    function openForm(product = null) {
        const ids = { title: `product-form-title-${++formCounter}`, name: `product-name-${formCounter}`, unit: `product-unit-${formCounter}`, price: `product-price-${formCounter}` };
        const error = el('div', { class: 'alert', role: 'alert', hidden: true });
        const name = el('input', { class: 'input', id: ids.name, name: 'name', required: true, maxlength: '255', value: product?.name ?? '', autocomplete: 'off' });
        const unit = el('select', { class: 'select', id: ids.unit, name: 'uom_id', required: true },
            uoms.map((uom) => el('option', { value: String(uom.id) }, uom.name)));
        if (product) unit.value = String(product.uom_id);
        const price = el('input', {
            class: 'input', id: ids.price, name: 'price_per_unit', type: 'number', min: '0', step: '0.01', required: true, inputmode: 'decimal',
            value: product ? Number(product.price_per_unit).toFixed(2) : '', placeholder: '0.00',
        });
        const save = el('button', { class: 'btn btn-primary', type: 'submit' }, icon('check', 18), product ? 'Save changes' : 'Add product');

        // Icon picker: suggests an emoji from the name until the user picks one themselves
        let chosenIcon = product?.icon ?? null;
        let iconPicked = Boolean(product);
        const preview = el('span', { class: 'icon-preview' });
        const picker = el('div', { class: 'emoji-picker', role: 'radiogroup', 'aria-label': 'Product icon' },
            el('button', { type: 'button', class: 'emoji-option initials', role: 'radio', 'data-icon': '', title: 'No icon (initials)' }, 'Aa'),
            PRODUCT_EMOJIS.map((emoji) => el('button', { type: 'button', class: 'emoji-option', role: 'radio', 'data-icon': emoji, title: emoji }, emoji)));
        picker.addEventListener('click', (event) => {
            const option = event.target.closest('.emoji-option');
            if (!option) return;
            iconPicked = true;
            setIcon(option.dataset.icon || null);
        });

        function setIcon(value) {
            chosenIcon = value;
            preview.replaceChildren(productAvatar({ name: name.value || '?', icon: chosenIcon }, { size: 'lg' }));
            picker.querySelectorAll('.emoji-option').forEach((option) => {
                const selected = (option.dataset.icon || null) === chosenIcon;
                option.classList.toggle('selected', selected);
                option.setAttribute('aria-checked', String(selected));
            });
        }

        name.addEventListener('input', () => setIcon(iconPicked ? chosenIcon : suggestEmoji(name.value)));
        setIcon(chosenIcon);

        const dialog = el('dialog', { 'aria-labelledby': ids.title },
            el('form', { class: 'modal-card', novalidate: true, onsubmit: submit },
                el('div', { class: 'modal-header' },
                    el('h2', { id: ids.title }, product ? 'Edit product' : 'New product'),
                    el('button', { class: 'icon-btn', type: 'button', 'aria-label': 'Close', onclick: () => dialog.close() }, icon('x'))),
                el('div', { class: 'modal-body' },
                    error,
                    el('div', { class: 'name-row' }, preview,
                        el('div', { class: 'field' }, el('label', { for: ids.name }, 'Name'), name)),
                    el('div', { class: 'field' }, el('label', {}, 'Icon'), picker),
                    el('div', { class: 'field' }, el('label', { for: ids.unit }, 'Unit'), unit),
                    el('div', { class: 'field' },
                        el('label', { for: ids.price }, 'Price per unit'),
                        el('div', { class: 'input-group' }, el('span', { class: 'prefix' }, CURRENCY), price)),
                    product ? el('p', { class: 'note' }, icon('info', 16), 'Price changes only apply to new orders.') : null),
                el('div', { class: 'modal-footer' },
                    el('button', { class: 'btn', type: 'button', onclick: () => dialog.close() }, 'Cancel'),
                    save)));

        async function submit(event) {
            event.preventDefault();
            error.hidden = true;
            if (!name.value.trim()) { shake(name); name.focus(); return; }
            if (price.value === '' || Number(price.value) < 0) { shake(price); price.focus(); return; }

            const payload = { name: name.value.trim(), icon: chosenIcon, uom_id: Number(unit.value), price_per_unit: price.value };
            save.disabled = true;
            try {
                const saved = product ? await api.products.update(product.id, payload) : await api.products.create(payload);
                dialog.close();
                toast(`${saved.name} ${product ? 'updated' : 'added'}`);
                await reload();
            } catch (requestError) {
                error.textContent = requestError.message;
                error.hidden = false;
                save.disabled = false;
            }
        }

        openDialog(dialog);
        name.focus();
    }

    render();

    return el('div', { class: 'page' },
        pageHeader({
            eyebrow: subtitle,
            title: 'Products',
            actions: [productSearch.wrapper, el('button', { class: 'btn btn-primary', type: 'button', onclick: () => openForm() }, icon('plus', 18), 'Add product')],
        }),
        el('section', { class: 'card' },
            el('div', { class: 'table-wrap' },
                el('table', { class: 'table' },
                    el('thead', {}, el('tr', {},
                        el('th', {}, 'Product'), el('th', {}, 'Unit'), el('th', { class: 'right' }, 'Price'), el('th', { class: 'actions' }, el('span', { class: 'visually-hidden' }, 'Actions')))),
                    tbody))));
}
