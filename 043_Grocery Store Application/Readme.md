# Grocery Store Management System

A full-stack desktop/web application built using Python to manage products, orders, and inventory for a grocery store. This project serves as an end-to-end practical application showcasing database management, backend API development, and frontend integration.

---

##  Features

- **Product Management:** Add, edit, view, and delete grocery items along with their units and prices per unit.
- **Order Processing:** Create new customer orders with dynamic item selection, quantity calculations, and total price updates.
- **Inventory & Stock Control:** Keep track of available stock in real time.
- **Sales Analytics:** View overall sales history and detailed summaries of previous transactions.

---

## Tech Stack & Architecture

- **Backend:** Python (Flask)
- **Database:** Postgres
- **Frontend:** HTML, CSS, JavaScript (Bootstrap / jQuery)
- **Architecture Pattern:** 3-Tier Architecture
  1. **UI Layer:** User interface for store managers to manage orders and stock.
  2. **Application / Business Logic Layer:** Python Flask REST APIs for request handling and business logic.
  3. **Database Layer:** Postgres database storing tables for `products`, `orders`, `order_details`, and `uom` (Unit of Measure).


---


### Clone the Repository

```bash
git clone https://github.com/your-username/grocery-store-system.git
cd grocery-store-system
```
---

## License

This project is open-source and available under the [MIT License](LICENSE).