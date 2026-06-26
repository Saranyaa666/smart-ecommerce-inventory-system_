# Developer Guide: Codebase Explanation in Plain Language

Welcome! If you are a Developer preparing this project for your resume, college labs, or a competition like E-Commerce System, this guide is written for you. It explains the design, coding concepts, and architecture in simple language.

---

## 🏫 1. What is this project about?
At its core, this project is a **Smart Inventory & Order Management System**. It manages two primary entities:
1. **Products** (the things you sell: name, category, price, stock quantity, and low-stock alert thresholds).
2. **Orders** (when a customer buys products: date, items bought, subtotal, and total amount).

But instead of writing all the code in a single massive file (which makes it hard to maintain and test), we divide the code into specialized folders using a pattern called **Clean Architecture**.

---

## 📐 2. The Core Concept: Clean Architecture
Imagine building a house. You don't put the bathroom plumbing, electrical wiring, and television controls in a single wall. You separate them. If your TV breaks, your toilet should still flush.

In code, we do the same using **layers**:
* **Domain Models (`models/`)**: These are simple Python classes (like `Product` and `Order`) that hold data and basic logic (like checking if stock is low or calculating item totals). They do not know about SQLite databases or CLI print commands. They represent the "pure business rules".
* **Repositories (`repositories/`)**: These are database operators. If you need to write SQL queries like `SELECT`, `INSERT`, or `UPDATE`, you write them inside repositories (like `ProductRepository`). If you decide to change your database from SQLite to PostgreSQL in the future, you **only** have to modify this folder!
* **Services (`services/`)**: This is where the core business decisions happen. For example, when placing an order:
  * Check if the product is active.
  * Check if we have enough stock.
  * Deduct the stock.
  * Save the order.
  All these steps are organized inside `OrderService`.
* **Presentation Layer (`main.py`)**: This is the User Interface (CLI). It displays menus, accepts inputs, and prints pretty tables using the `rich` library. It calls the services to do the actual work.

---

## 💻 3. Key Software Engineering Concepts Used

### A. Object-Oriented Programming (OOP)
Instead of using complex dictionaries or arrays to store product data, we map them to objects of classes:
* **Encapsulation**: The `Product` class encapsulates attributes (price, quantity) and methods (like `validate()`) together.
* **Domain Validation**: When a user inputs product data, we call `product.validate()`. If price is negative, we raise an exception, preventing bad data from entering our system.

### B. Relational Database Normalization (3NF)
A common mistake in beginner projects is storing orders in a single row like:
`Order ID: 1 | Products: "Laptop, Phone" | Quantities: "1, 2" | Total: $2800`
This is bad design because you can't run SQL queries to find "how many Phones were sold in total?"

To fix this, we normalize the database:
1. **`products` Table**: Stores name, price, and current stock.
2. **`orders` Table**: Stores the date and total order amount.
3. **`order_items` Table**: Connects the two. If Order #1 has a Laptop and a Phone, we add two rows in `order_items` referencing `order_id = 1`. This is called a **One-to-Many Relationship** (One order can have many line items).

### C. Database Transactions (ACID)
What happens if a customer checks out a Laptop and a Wireless Mouse, but someone buys the last Mouse right before checkout?
If we don't use transactions, the system might deduct the Laptop stock, fail to deduct the Mouse stock, and leave the database in an incomplete/broken state.

To prevent this, we use **Transactions**:
* We open a connection and use SQLite's transaction wrapper:
  ```python
  with db_manager.get_connection() as conn:
      # If ANY error happens inside this block, 
      # all changes are automatically ROLLED BACK.
      # If the block finishes successfully, changes are COMMITTED.
  ```
This is called **Atomic execution** (all modifications succeed, or none do).

### D. Soft Delete (Archiving)
In e-commerce, if a product (e.g., iPhone 12) is discontinued, you can't just delete it from your database. If you delete it, what happens to your historical sales reports from last year that reference the iPhone 12 ID? They will break or show missing data.

Instead of a hard delete, we perform a **Soft Delete (Archiving)**:
* We added an `is_active` column (0 or 1) in our SQL schema.
* When a product is archived, we set `is_active = 0`.
* In `main.py`, buyers only search for and buy products where `is_active = 1`.
* If a recruiter attempts to permanently delete a product that has orders, the repository catches the foreign key constraint fail and advises them to soft-delete/archive it instead.

### E. Structured Auditing (Logging)
In production environments, using `print()` for debugging is discouraged. Instead, we use Python's `logging` module. It records system activities, user choices, stock warning thresholds, and exception alerts into `system.log`.

---

## 🏃 4. How to explain this project in an Interview
If a recruiter asks, "Explain your inventory project," you can respond:

> *"I built a modular E-Commerce Inventory and Order Management System in Python using Clean Architecture and SQLite. 
> 
> The system implements database-level ACID transactions to prevent stock race conditions, soft-deletes to protect historical sales records, and aggregated database reports (such as top-selling products by quantity and revenue). 
> 
> By organizing the codebase into distinct layers (Domain Models, SQL Repositories, Business Services, and CLI Presentation), I ensured that changing the database or the front-end user interface requires zero modifications to the core business logic. I also wrote a full suite of unit tests verifying transaction rollbacks and domain validations."*
