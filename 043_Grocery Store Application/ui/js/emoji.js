// Product icons: a picker palette and name-based suggestions.

export const PRODUCT_EMOJIS = [
    '🍎', '🍏', '🍐', '🍊', '🍋', '🍌', '🍉', '🍇', '🍓', '🫐', '🍒', '🍑', '🥭', '🍍', '🥥', '🥝',
    '🍅', '🥑', '🍆', '🥔', '🥕', '🌽', '🌶️', '🫑', '🥒', '🥬', '🥦', '🧄', '🧅', '🍄', '🥜', '🫘',
    '🍞', '🥐', '🥖', '🥨', '🥯', '🧀', '🥚', '🧈', '🥞', '🥓', '🥩', '🍗', '🍖', '🐟', '🦐', '🍤',
    '🍚', '🍝', '🌾', '🍬', '🍫', '🍪', '🍯', '🥛', '🧃', '☕', '🍵', '🧋', '🥤', '💧', '🍷', '🍺',
    '🧂', '🫒', '🥫', '🧴', '🧻', '🧼', '🧽', '🛒',
];

const KEYWORDS = [
    ['green apple', '🍏'], ['apple', '🍎'], ['pear', '🍐'], ['orange juice', '🧃'], ['juice', '🧃'], ['orange', '🍊'],
    ['lemon', '🍋'], ['lime', '🍋'], ['banana', '🍌'], ['melon', '🍉'], ['grape', '🍇'], ['strawberr', '🍓'],
    ['blueberr', '🫐'], ['cherr', '🍒'], ['peach', '🍑'], ['mango', '🥭'], ['pineapple', '🍍'], ['coconut', '🥥'],
    ['kiwi', '🥝'], ['tomato', '🍅'], ['avocado', '🥑'], ['eggplant', '🍆'], ['aubergine', '🍆'], ['potato', '🥔'],
    ['carrot', '🥕'], ['corn', '🌽'], ['chili', '🌶️'], ['pepper', '🫑'], ['cucumber', '🥒'], ['lettuce', '🥬'],
    ['salad', '🥬'], ['spinach', '🥬'], ['broccoli', '🥦'], ['garlic', '🧄'], ['onion', '🧅'], ['mushroom', '🍄'],
    ['peanut', '🥜'], ['nut', '🥜'], ['bean', '🫘'], ['croissant', '🥐'], ['baguette', '🥖'], ['bread', '🍞'],
    ['bagel', '🥯'], ['cheese', '🧀'], ['egg', '🥚'], ['butter', '🧈'], ['bacon', '🥓'], ['beef', '🥩'],
    ['steak', '🥩'], ['meat', '🥩'], ['chicken', '🍗'], ['fish', '🐟'], ['salmon', '🐟'], ['tuna', '🐟'],
    ['shrimp', '🦐'], ['prawn', '🦐'], ['rice', '🍚'], ['pasta', '🍝'], ['spaghetti', '🍝'], ['flour', '🌾'],
    ['wheat', '🌾'], ['oat', '🌾'], ['sugar', '🍬'], ['candy', '🍬'], ['chocolate', '🍫'], ['cookie', '🍪'],
    ['biscuit', '🍪'], ['honey', '🍯'], ['milk', '🥛'], ['yogurt', '🥛'], ['coffee', '☕'], ['tea', '🍵'],
    ['soda', '🥤'], ['cola', '🥤'], ['water', '💧'], ['wine', '🍷'], ['beer', '🍺'], ['salt', '🧂'],
    ['olive', '🫒'], ['oil', '🫒'], ['can', '🥫'], ['soup', '🥫'], ['shampoo', '🧴'], ['soap', '🧼'],
    ['tissue', '🧻'], ['toilet', '🧻'], ['sponge', '🧽'],
];

export function suggestEmoji(name) {
    const lower = String(name).toLowerCase();
    return KEYWORDS.find(([keyword]) => lower.includes(keyword))?.[1] || null;
}
