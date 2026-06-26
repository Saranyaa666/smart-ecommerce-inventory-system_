# System Design & FAQ: Questions & Answers

This document lists advanced technical questions recruiters or technical evaluators (like E-Commerce System judges) might ask about the design and implementation of this system.

---

## 🗄️ 1. Database & Transactional Integrity

### Q1: Why did you split the schema into `orders` and `order_items` tables instead of storing orders as a list or JSON string in a single row?
**Answer:**
This is called **Database Normalization (Third Normal Form - 3NF)**. Storing order items in a normalized table allows us to:
1. Enforce referential integrity using Foreign Keys linking back to the `products` table.
2. Run database-level aggregations (like sum of items sold per category, average unit sales, or top-selling products) using fast SQL `GROUP BY` operations instead of pulling entire strings into Python, splitting them, and aggregating them in memory.
3. Keep row sizes consistent and queryable.

### Q2: How did you implement transaction safety during order checkout? What happens if one item in the cart is out of stock?
**Answer:**
We implemented transaction safety by managing SQLite connections as Python **context managers** inside `OrderService.place_order`. 
1. We execute all SQL updates (stock deductions, inserting order row, and inserting order items) using the **same database connection** within a single `with` block.
2. If any validation fails (e.g., an item is out of stock, or database constraints are violated), an exception is raised, which triggers the context manager's exit callback to execute a `rollback()` on the connection.
3. If all statements complete successfully, the context manager commits the changes. This guarantees **Atomicity** (either the entire order checkout succeeds, or no changes occur).

### Q3: How do you handle race conditions in database stock deduction?
**Answer:**
In SQLite, write operations block other write operations due to file locking (SQLite lock levels). 
For multi-user scale database servers like PostgreSQL, we would prevent race conditions (two threads reading stock = 1 simultaneously and both successfully purchasing it) by:
1. Using **Pessimistic Locking**: Executing a `SELECT ... FOR UPDATE` query which locks the rows during stock check until checkout transaction commits.
2. Or using **Optimistic Locking / Check-Constraints**: In our SQLite schema, we have a check constraint: `CHECK(quantity >= 0)`. If thread A deducts stock to 0, and thread B tries to deduct it further, the database throws an integrity exception, rolling back thread B's transaction automatically.

---

## 📐 2. Architecture & Design Patterns

### Q4: Why did you write raw SQL repositories instead of using an ORM like SQLAlchemy or Django ORM?
**Answer:**
While ORMs speed up simple prototyping, writing raw SQL repositories:
1. Demonstrates an understanding of SQL details: transactions, aggregations, schema design, and constraints.
2. Keeps the application lightweight without heavy external packages, which is ideal for microservices and resource-constrained environments.
3. Provides full optimization control over query execution plans, indexes, and database-level locking mechanisms.

### Q5: What is the "Dependency Rule" in Clean Architecture, and how does it apply here?
**Answer:**
The Dependency Rule states that source code dependencies must only point inward, toward the core business logic and domain models. 
* In this project, `models/product.py` and `models/order.py` are the core domain. They have no import statements pointing to `repositories`, `database`, or presentation libraries like `rich`.
* This means our core business logic is completely isolated. If we want to replace SQLite with a Web API, a MongoDB database, or change our terminal interface to a React web dashboard, we can reuse our core models and services without editing their code.

---

## 🛡️ 3. Error Handling & Security

### Q6: Why did you implement custom exception classes rather than using Python's built-in exceptions?
**Answer:**
Custom exceptions (e.g., `InsufficientStockException`, `ProductInUseException`) allow us to:
1. Decouple backend business logic from presentation layer formatting. The services throw semantic exceptions, and the presentation layer decides how to display them to the user (e.g., in a red Rich console panel or an HTML alert).
2. Write specific exception handler blocks to trigger programmatic recovery strategies (like offering to soft-delete/archive an ordered product if a hard-delete fails).
3. Generate cleaner audit logs by recording precise semantic errors.

### Q7: Explain the difference between Soft Delete and Hard Delete. How did you implement both?
**Answer:**
* **Hard Delete** permanently removes a row from a table using `DELETE FROM`. If a row is referenced by another table (like `products` referenced by `order_items`), a hard delete breaks referential integrity.
* **Soft Delete** sets a flag (like `is_active = 0` or `is_archived = 1`) on the row, leaving the data intact but hiding it from active search queries.
* **Our implementation**: The Products table has an `is_active` column.
  1. Customers can only view and order products where `is_active = 1`.
  2. If an operator tries to delete a product that has no sales records, we perform a hard delete.
  3. If they attempt to hard-delete a product with order history, the database raises an integrity constraint error. We catch it, throw a custom exception, and guide the user to **soft-delete (archive)** it instead, keeping reports and invoices intact.

---

## 🧪 4. Testing & Maintenance

### Q8: What testing strategy did you follow? How did you manage database side-effects in unit tests?
**Answer:**
We used Python's built-in `unittest` framework to execute automated test cases covering:
1. Domain model validations (prices, negative quantities).
2. Stock adjustments (restocking, stock reductions).
3. Transaction rollbacks (ensuring all-or-nothing checkouts).
4. soft delete mechanics.

To prevent tests from corrupting production database data:
* We instantiate the repository layer using a dedicated test database filename (`test_inventory.db`).
* We run `setUp()` before each test case to clean out all table data, ensuring a deterministic starting state.
* We run `tearDownClass()` to delete the database file from disk entirely after the suite completes, leaving no garbage files.
