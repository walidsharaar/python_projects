// The signed-in user, shared by the router and the views.
let currentUser = null;

export const getUser = () => currentUser;
export const setUser = (user) => { currentUser = user; };
export const isAdmin = () => currentUser?.role === 'admin';

/** Whether the current user may see an element/route limited to the given roles ("admin cashier"). */
export function allowed(roles) {
    return !roles || (currentUser && roles.split(/\s+/).includes(currentUser.role));
}

export const ROLE_LABELS = { admin: 'Administrator', cashier: 'Cashier' };
