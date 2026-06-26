import sys
import logging
from typing import List, Dict, Any

# Configure logging to write to system.log file
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.FileHandler("system.log", encoding="utf-8"),
    ]
)
logger = logging.getLogger("InventorySystem.CLI")

# Third-party imports
try:
    from rich.console import Console
    from rich.table import Table
    from rich.panel import Panel
    from rich.prompt import Prompt, IntPrompt, FloatPrompt, Confirm
    from rich.text import Text
    from rich.align import Align
except ImportError:
    print("Error: The 'rich' library is required to run this application.")
    print("Please install it by running: pip install rich")
    sys.exit(1)

# Application imports
from database.connection import DatabaseConnectionManager
from repositories.product_repository import ProductRepository
from repositories.order_repository import OrderRepository
from services.inventory_service import InventoryService
from services.order_service import OrderService
from services.report_service import ReportService
from models.product import Product
from utils.helpers import generate_invoice, export_sales_report_to_csv, export_inventory_report_to_csv
from exceptions.custom_exceptions import (
    InventorySystemException,
    ProductNotFoundException,
    InsufficientStockException,
    DuplicateProductException,
    ProductInUseException,
)

# Initialize console
console = Console()

class ECommerceApp:
    def __init__(self, db_path: str = "inventory_system.db"):
        logger.info("Initializing Smart E-Commerce Inventory App...")
        self.db_manager = DatabaseConnectionManager(db_path)
        self.product_repo = ProductRepository(self.db_manager)
        self.order_repo = OrderRepository(self.db_manager)
        
        self.inventory_service = InventoryService(self.product_repo)
        self.order_service = OrderService(self.order_repo, self.product_repo)
        self.report_service = ReportService(self.db_manager)
        logger.info("App components initialized successfully.")

    def display_welcome_banner(self):
        """Renders a beautiful welcome banner for the CLI."""
        banner_text = Text()
        banner_text.append("=== SMART E-COMMERCE INVENTORY & ORDER MANAGEMENT SYSTEM ===\n", style="bold cyan")
        banner_text.append("Built with Python, SQLite, OOP, and Clean Architecture\n", style="italic white")
        banner_text.append("A Clean Architecture based Inventory & Order Management System", style="bold green")
        
        panel = Panel(
            Align.center(banner_text),
            border_style="cyan",
            title="[bold yellow]Welcome[/bold yellow]",
            subtitle="[italic]v1.1.0 (Refined Version)[/italic]"
        )
        console.print(panel)

    def display_menu(self):
        """Displays options organized in sections."""
        menu_table = Table(title="[bold yellow]Main Menu Options[/bold yellow]", show_header=True, header_style="bold magenta", expand=True)
        menu_table.add_column("Category", style="cyan", width=25)
        menu_table.add_column("Option & Action", style="white")

        menu_table.add_row("1. Product Management", " [bold green]1[/bold green] - View Products (Active or All)\n [bold green]2[/bold green] - Add New Product\n [bold green]3[/bold green] - Update Product Details\n [bold green]4[/bold green] - Delete/Archive Product\n [bold green]5[/bold green] - Search Products")
        menu_table.add_section()
        menu_table.add_row("2. Inventory Tracking", " [bold green]6[/bold green] - Restock Product (Add Stock)\n [bold green]7[/bold green] - View Low Stock Alerts")
        menu_table.add_section()
        menu_table.add_row("3. Order Management", " [bold green]8[/bold green] - Place Customer Order\n [bold green]9[/bold green] - View Order History\n [bold green]10[/bold green] - View & Print Order Invoice")
        menu_table.add_section()
        menu_table.add_row("4. Business Analytics & Reports", " [bold green]11[/bold green] - Sales Analytics Report (with CSV export)\n [bold green]12[/bold green] - Inventory Status Report (with CSV export)\n [bold green]13[/bold green] - View Top Selling Products")
        menu_table.add_section()
        menu_table.add_row("5. Database Utilities", " [bold green]14[/bold green] - Seed Database with Sample Test Data")
        menu_table.add_section()
        menu_table.add_row("Exit System", " [bold red]0[/bold red] - Exit Application")

        console.print(menu_table)

    def run(self):
        """Main execution loop for the CLI application."""
        self.display_welcome_banner()
        
        while True:
            self.display_menu()
            choice = Prompt.ask("\nSelect an option [0-14]", choices=[str(i) for i in range(15)])
            logger.info(f"User selected option: {choice}")
            
            try:
                if choice == "1":
                    self.view_products_workflow()
                elif choice == "2":
                    self.add_product()
                elif choice == "3":
                    self.update_product()
                elif choice == "4":
                    self.delete_product()
                elif choice == "5":
                    self.search_products()
                elif choice == "6":
                    self.restock_product()
                elif choice == "7":
                    self.view_low_stock_alerts()
                elif choice == "8":
                    self.place_order()
                elif choice == "9":
                    self.view_order_history()
                elif choice == "10":
                    self.view_invoice()
                elif choice == "11":
                    self.generate_sales_report()
                elif choice == "12":
                    self.generate_inventory_report()
                elif choice == "13":
                    self.view_top_selling_products()
                elif choice == "14":
                    self.seed_test_data()
                elif choice == "0":
                    console.print("[bold yellow]Exiting Smart Inventory System. Goodbye![/bold yellow]")
                    logger.info("Application exited by user.")
                    break
            except InventorySystemException as e:
                console.print(f"[bold red]Business Logic Error: {e}[/bold red]")
                logger.error(f"Business Logic Error: {e}", exc_info=True)
            except Exception as e:
                console.print(f"[bold red]Unexpected Error: {e}[/bold red]")
                logger.critical(f"System Error: {e}", exc_info=True)
                
            input("\nPress Enter to return to the Main Menu...")

    # --- CLI WORKFLOWS ---

    def view_products_workflow(self):
        """Handles choice of viewing active vs all (including archived) products."""
        console.print("\n[bold yellow]View Products Options:[/bold yellow]")
        console.print(" [1] View Active Products Only (Default)")
        console.print(" [2] View All Products (Including Archived)")
        sub_choice = Prompt.ask("Choose option", choices=["1", "2"], default="1")
        
        if sub_choice == "1":
            products = self.inventory_service.get_all_products(active_only=True)
            self.view_all_products(products_list=products, title="Active Product Catalog")
        else:
            products = self.inventory_service.get_all_products(active_only=False)
            self.view_all_products(products_list=products, title="Complete Product Database (Active + Archived)")

    def view_all_products(self, products_list: List[Product] = None, title: str = "All Products"):
        """Displays products in a clean, color-coded System."""
        products = products_list if products_list is not None else self.inventory_service.get_all_products(active_only=True)
        
        if not products:
            console.print("[yellow]No products found in the database. Select option 14 to seed sample data.[/yellow]")
            return

        table = Table(title=f"[bold cyan]{title}[/bold cyan]", show_header=True, header_style="bold blue")
        table.add_column("ID", justify="right", style="cyan")
        table.add_column("Product Name", style="white")
        table.add_column("Category", style="magenta")
        table.add_column("Price", justify="right", style="green")
        table.add_column("Quantity in Stock", justify="right")
        table.add_column("Threshold", justify="right", style="yellow")
        table.add_column("Status", justify="center")

        for p in products:
            price_str = f"${p.price:.2f}"
            
            # Status colors based on stock levels and active flag
            if not p.is_active:
                status = "[bold red]Archived[/bold red]"
                qty_str = f"[dim]{p.quantity}[/dim]"
            elif p.quantity == 0:
                status = "[bold red]Out of Stock[/bold red]"
                qty_str = f"[bold red]{p.quantity}[/bold red]"
            elif p.is_low_stock:
                status = "[bold yellow]Low Stock Alert[/bold yellow]"
                qty_str = f"[bold yellow]{p.quantity}[/bold yellow]"
            else:
                status = "[bold green]Healthy[/bold green]"
                qty_str = f"[green]{p.quantity}[/green]"

            table.add_row(
                str(p.product_id),
                p.product_name,
                p.category,
                price_str,
                qty_str,
                str(p.low_stock_threshold),
                status
            )
            
        console.print(table)

    def add_product(self):
        """Prompts user for product data and inserts it."""
        console.print("[bold yellow]Add New Product[/bold yellow]")
        name = Prompt.ask("Enter Product Name")
        category = Prompt.ask("Enter Category")
        price = FloatPrompt.ask("Enter Price ($)", default=0.0)
        quantity = IntPrompt.ask("Enter Initial Stock Quantity", default=0)
        threshold = IntPrompt.ask("Enter Low Stock Alert Threshold", default=5)

        new_product = Product(
            product_name=name,
            category=category,
            price=price,
            quantity=quantity,
            low_stock_threshold=threshold
        )
        
        saved_product = self.inventory_service.add_product(new_product)
        console.print(f"[bold green]Success![/bold green] Product '{saved_product.product_name}' added with ID: {saved_product.product_id}.")

    def update_product(self):
        """Prompts user for modifications on an existing product."""
        console.print("[bold yellow]Update Product Details[/bold yellow]")
        product_id = IntPrompt.ask("Enter Product ID to update")
        
        try:
            product = self.inventory_service.get_product(product_id)
        except ProductNotFoundException as e:
            console.print(f"[bold red]{e}[/bold red]")
            return

        console.print(f"Updating product: [cyan]{product.product_name}[/cyan] (Category: {product.category})")
        
        name = Prompt.ask("Enter Product Name", default=product.product_name)
        category = Prompt.ask("Enter Category", default=product.category)
        price = FloatPrompt.ask("Enter Price ($)", default=product.price)
        quantity = IntPrompt.ask("Enter Quantity", default=product.quantity)
        threshold = IntPrompt.ask("Enter Low Stock Threshold", default=product.low_stock_threshold)
        is_active = Confirm.ask("Is this product active (visible for order)?", default=product.is_active)

        product.product_name = name
        product.category = category
        product.price = price
        product.quantity = quantity
        product.low_stock_threshold = threshold
        product.is_active = is_active

        if self.inventory_service.update_product(product):
            console.print(f"[bold green]Success![/bold green] Product ID {product_id} updated successfully.")
        else:
            console.print("[red]Failed to update product details.[/red]")

    def delete_product(self):
        """Attempts a permanent delete, prompts soft delete (archive) on referential failure."""
        console.print("[bold red]Delete / Archive Product[/bold red]")
        product_id = IntPrompt.ask("Enter Product ID")
        
        try:
            product = self.inventory_service.get_product(product_id)
        except ProductNotFoundException as e:
            console.print(f"[bold red]{e}[/bold red]")
            return

        # Offer options
        console.print(f"\nProduct: [cyan]{product.product_name}[/cyan] | Category: {product.category}")
        console.print(" [1] Hard Delete (Remove permanently - fails if product has orders)")
        console.print(" [2] Soft Delete/Archive (Keeps sales records intact, hides product from catalog)")
        choice = Prompt.ask("Choose operation", choices=["1", "2"], default="2")

        if choice == "1":
            confirm = Confirm.ask(f"Are you sure you want to permanently delete [red]{product.product_name}[/red]?")
            if confirm:
                try:
                    self.inventory_service.delete_product(product_id)
                    console.print(f"[bold green]Success![/bold green] Product '{product.product_name}' hard-deleted.")
                except ProductInUseException as e:
                    console.print(f"[yellow]{e}[/yellow]")
                    soft_confirm = Confirm.ask("Would you like to soft-delete (archive) this product instead?")
                    if soft_confirm:
                        self.inventory_service.archive_product(product_id)
                        console.print(f"[bold green]Success![/bold green] Product '{product.product_name}' archived.")
            else:
                console.print("[yellow]Deletion cancelled.[/yellow]")
        else:
            confirm = Confirm.ask(f"Are you sure you want to archive '{product.product_name}'?")
            if confirm:
                self.inventory_service.archive_product(product_id)
                console.print(f"[bold green]Success![/bold green] Product '{product.product_name}' archived.")
            else:
                console.print("[yellow]Archive operation cancelled.[/yellow]")

    def search_products(self):
        """Searches products based on name/category keywords."""
        console.print("[bold yellow]Search Products[/bold yellow]")
        query = Prompt.ask("Enter search query (Name or Category)")
        results = self.inventory_service.search_products(query, active_only=False)
        self.view_all_products(products_list=results, title=f"Search Results for '{query}'")

    def restock_product(self):
        """Allows users to add stock to an existing product."""
        console.print("[bold yellow]Restock Product (Add Quantity)[/bold yellow]")
        product_id = IntPrompt.ask("Enter Product ID")
        
        try:
            product = self.inventory_service.get_product(product_id)
        except ProductNotFoundException as e:
            console.print(f"[bold red]{e}[/bold red]")
            return

        console.print(f"Current Stock for [cyan]{product.product_name}[/cyan]: [green]{product.quantity}[/green]")
        added_qty = IntPrompt.ask("Enter quantity to add")
        
        if added_qty <= 0:
            console.print("[red]Quantity to add must be greater than zero.[/red]")
            return

        self.inventory_service.restock_product(product_id, added_qty)
        console.print(f"[bold green]Success![/bold green] Stock updated. New quantity: {product.quantity + added_qty}")

    def view_low_stock_alerts(self):
        """Displays only active items under the low-stock threshold."""
        alerts = self.inventory_service.get_low_stock_alerts(active_only=True)
        if not alerts:
            console.print("[bold green]All products have healthy stock levels! No alerts.[/bold green]")
        else:
            self.view_all_products(products_list=alerts, title="LOW STOCK WARNINGS (Active Products Only)")

    def place_order(self):
        """Interactive multi-item order placement workflow."""
        console.print("[bold yellow]Place Customer Order[/bold yellow]")
        
        # Display active products to pick from
        self.view_all_products(title="Available Catalog")
        
        items_to_order = []
        
        while True:
            product_id = IntPrompt.ask("\nEnter Product ID to add to order (0 to finish selection)")
            if product_id == 0:
                break
                
            try:
                product = self.inventory_service.get_product(product_id)
            except ProductNotFoundException as e:
                console.print(f"[bold red]{e}[/bold red]")
                continue
                
            if not product.is_active:
                console.print("[bold red]This product is archived and cannot be ordered.[/bold red]")
                continue

            console.print(f"Selected: [cyan]{product.product_name}[/cyan] | Price: ${product.price:.2f} | Available Stock: {product.quantity}")
            quantity = IntPrompt.ask("Enter Quantity to order")
            
            if quantity <= 0:
                console.print("[red]Quantity must be positive.[/red]")
                continue
                
            if quantity > product.quantity:
                console.print(f"[bold red]Error: Insufficient stock. Only {product.quantity} units available.[/bold red]")
                continue

            # Check if product is already added in order cart, merge quantities
            existing_cart_item = next((item for item in items_to_order if item["product_id"] == product_id), None)
            if existing_cart_item:
                total_qty = existing_cart_item["quantity"] + quantity
                if total_qty > product.quantity:
                    console.print(f"[bold red]Error: Combined quantity ({total_qty}) exceeds stock ({product.quantity}).[/bold red]")
                    continue
                existing_cart_item["quantity"] = total_qty
                console.print(f"Updated quantity for {product.product_name} in cart to {total_qty}.")
            else:
                items_to_order.append({"product_id": product_id, "quantity": quantity})
                console.print(f"Added {quantity} x {product.product_name} to cart.")
        
        if not items_to_order:
            console.print("[yellow]Cart is empty. Order placement cancelled.[/yellow]")
            return

        # Checkout confirmation
        console.print("\n[bold yellow]--- Order Summary ---[/bold yellow]")
        summary_table = Table(show_header=True, header_style="bold magenta")
        summary_table.add_column("Item", style="white")
        summary_table.add_column("Qty", justify="center")
        summary_table.add_column("Unit Price", justify="right")
        summary_table.add_column("Subtotal", justify="right", style="green")
        
        estimated_total = 0.0
        for item in items_to_order:
            p = self.inventory_service.get_product(item["product_id"])
            subtotal = p.price * item["quantity"]
            estimated_total += subtotal
            summary_table.add_row(
                p.product_name,
                str(item["quantity"]),
                f"${p.price:.2f}",
                f"${subtotal:.2f}"
            )
        console.print(summary_table)
        console.print(f"[bold]Estimated Grand Total: [green]${estimated_total:.2f}[/green][/bold]")
        
        confirm = Confirm.ask("Proceed to complete payment and place order?")
        if not confirm:
            console.print("[yellow]Order checkout cancelled.[/yellow]")
            return
            
        # Place order via service
        try:
            saved_order = self.order_service.place_order(items_to_order)
            console.print("[bold green]Success! Order placed successfully.[/bold green]")
            console.print(Panel(generate_invoice(saved_order), title="[bold green]Receipt[/bold green]", border_style="green"))
            
            # Post-order stock check warning
            for item in saved_order.items:
                refreshed_p = self.inventory_service.get_product(item.product_id)
                if refreshed_p.is_low_stock:
                    console.print(f"[bold yellow]⚠️ Low stock alert triggered for '{refreshed_p.product_name}'! Remaining: {refreshed_p.quantity}[/bold yellow]")
        except InsufficientStockException as e:
            console.print(f"[bold red]Transaction Failed: {e}[/bold red]")

    def view_order_history(self):
        """Displays orders history listing ids, dates and amounts."""
        orders = self.order_service.get_order_history()
        if not orders:
            console.print("[yellow]No order history found.[/yellow]")
            return

        table = Table(title="[bold cyan]Order History[/bold cyan]", show_header=True, header_style="bold magenta")
        table.add_column("Order ID", justify="right", style="cyan")
        table.add_column("Order Date/Time", style="white")
        table.add_column("Items Count", justify="center")
        table.add_column("Total Amount", justify="right", style="green")

        for o in orders:
            table.add_row(
                str(o.order_id),
                str(o.order_date),
                str(len(o.items)),
                f"${o.total_amount:.2f}"
            )
        console.print(table)

    def view_invoice(self):
        """Fetches order and prints a clean invoice receipt."""
        console.print("[bold yellow]View Order Invoice[/bold yellow]")
        order_id = IntPrompt.ask("Enter Order ID")
        
        try:
            order = self.order_service.get_order_details(order_id)
            invoice_txt = generate_invoice(order)
            console.print(Panel(invoice_txt, title=f"[green]Invoice #{order_id}[/green]", border_style="cyan"))
        except Exception as e:
            console.print(f"[bold red]Error: {e}[/bold red]")

    def generate_sales_report(self):
        """Renders sales dashboard reporting revenue and offers CSV export."""
        console.print("[bold yellow]Generating Sales Analytics Report...[/bold yellow]")
        report = self.report_service.get_sales_report()
        
        summary_text = Text()
        summary_text.append(f"Total Completed Orders : {report['total_orders']}\n", style="white")
        summary_text.append(f"Total Gross Revenue    : ${report['total_revenue']:.2f}\n", style="bold green")
        summary_text.append(f"Average Order Value    : ${report['average_order_value']:.2f}\n", style="white")
        summary_text.append(f"Total Products Sold    : {report['total_items_sold']} units", style="cyan")
        
        console.print(Panel(summary_text, title="[bold green]Sales Summary Dashboard[/bold green]", expand=True))
        
        if report["category_sales_breakdown"]:
            table = Table(title="[bold yellow]Sales Breakdown by Category[/bold yellow]", show_header=True, header_style="bold blue")
            table.add_column("Category", style="cyan")
            table.add_column("Units Sold", justify="right")
            table.add_column("Revenue Generated", justify="right", style="green")
            
            for cat in report["category_sales_breakdown"]:
                table.add_row(
                    cat["category"],
                    str(cat["items_sold"]),
                    f"${cat['revenue']:.2f}"
                )
            console.print(table)

        # Export prompt
        export_choice = Confirm.ask("Would you like to export this sales report to CSV?")
        if export_choice:
            filepath = "sales_report.csv"
            export_sales_report_to_csv(report, filepath)
            console.print(f"[bold green]Success![/bold green] Sales report exported to '{filepath}'.")
            logger.info(f"Report exported: {filepath}")

    def generate_inventory_report(self):
        """Renders inventory statistics and offers CSV export."""
        console.print("[bold yellow]Generating Inventory Status Report...[/bold yellow]")
        report = self.report_service.get_inventory_report()
        
        summary_text = Text()
        summary_text.append(f"Total Unique SKUs      : {report['total_products']}\n", style="cyan")
        summary_text.append(f"Total Stock Volume     : {report['total_stock_items']} units\n", style="white")
        summary_text.append(f"Total Stock Valuation  : ${report['total_valuation']:.2f}\n", style="bold green")
        summary_text.append(f"Average Product Price  : ${report['average_price']:.2f}\n", style="white")
        summary_text.append(f"Low Stock Items Alert  : {report['low_stock_count']} items", style="bold yellow" if report['low_stock_count'] > 0 else "green")
        
        console.print(Panel(summary_text, title="[bold cyan]Inventory Valuation Dashboard[/bold cyan]", expand=True))
        
        if report["category_breakdown"]:
            table = Table(title="[bold yellow]Stock Allocation by Category[/bold yellow]", show_header=True, header_style="bold blue")
            table.add_column("Category", style="cyan")
            table.add_column("Unique Products", justify="right")
            table.add_column("Total Stock in Hand", justify="right")
            table.add_column("Portfolio Valuation", justify="right", style="green")
            
            for cat in report["category_breakdown"]:
                table.add_row(
                    cat["category"],
                    str(cat["product_count"]),
                    str(cat["stock_quantity"]),
                    f"${cat['valuation']:.2f}"
                )
            console.print(table)

        # Export prompt
        export_choice = Confirm.ask("Would you like to export this inventory report to CSV?")
        if export_choice:
            filepath = "inventory_report.csv"
            export_inventory_report_to_csv(report, filepath)
            console.print(f"[bold green]Success![/bold green] Inventory report exported to '{filepath}'.")
            logger.info(f"Report exported: {filepath}")

    def view_top_selling_products(self):
        """Displays top 5 best selling items."""
        console.print("[bold yellow]Fetching Top Selling Products...[/bold yellow]")
        top_products = self.report_service.get_top_selling_products(limit=5)
        
        if not top_products:
            console.print("[yellow]No sales recorded yet. Place an order to see analytical updates.[/yellow]")
            return

        table = Table(title="[bold gold1]🏆 Top Selling Products Dashboard[/bold gold1]", show_header=True, header_style="bold yellow")
        table.add_column("Rank", justify="center", style="bold cyan")
        table.add_column("Product Name", style="white")
        table.add_column("Category", style="magenta")
        table.add_column("Quantity Sold", justify="right", style="bold green")
        table.add_column("Total Revenue Generated", justify="right", style="green")

        for idx, p in enumerate(top_products, start=1):
            table.add_row(
                str(idx),
                p["product_name"],
                p["category"],
                str(p["total_quantity_sold"]),
                f"${p['total_revenue']:.2f}"
            )
        console.print(table)

    def seed_test_data(self):
        """Seeds the database with test data for demonstration purposes."""
        # Check if database already has products to prevent duplicates
        existing = self.inventory_service.get_all_products(active_only=False)
        if existing:
            confirm = Confirm.ask("[yellow]Database already contains products. Seeding will skip existing products or fail if unique name collisions occur. Continue?[/yellow]")
            if not confirm:
                return

        sample_products = [
            Product("Flagship Laptop Pro", "Electronics", 1299.99, 15, low_stock_threshold=5),
            Product("Smart Watch Active", "Electronics", 199.99, 25, low_stock_threshold=6),
            Product("Noise-Cancelling Headphones", "Electronics", 149.99, 4, low_stock_threshold=5), # Low Stock!
            Product("Organic Green Tea", "Grocery", 12.50, 100, low_stock_threshold=15),
            Product("Ergonomic Office Chair", "Furniture", 249.99, 3, low_stock_threshold=5),    # Low Stock!
            Product("Leather Travel Duffle", "Luggage", 89.99, 12, low_stock_threshold=4),
            Product("Stainless Water Bottle", "Fitness", 24.99, 8, low_stock_threshold=10),     # Low Stock!
            Product("Superfood Blender Pro", "Kitchen Appliance", 79.99, 20, low_stock_threshold=5),
        ]

        seeded_count = 0
        for p in sample_products:
            try:
                self.inventory_service.add_product(p)
                seeded_count += 1
            except DuplicateProductException:
                pass
                
        console.print(f"[bold green]Seeded {seeded_count} sample products successfully![/bold green]")
        
        # Seed some sample orders if database is totally empty of orders
        orders_check = self.order_service.get_order_history()
        if not orders_check and seeded_count > 0:
            console.print("[yellow]Seeding mock order history for analytical reports...[/yellow]")
            try:
                refreshed_products = self.inventory_service.get_all_products(active_only=False)
                p_map = {p.product_name: p.product_id for p in refreshed_products}
                
                # Order 1
                if "Flagship Laptop Pro" in p_map and "Stainless Water Bottle" in p_map:
                    self.order_service.place_order([
                        {"product_id": p_map["Flagship Laptop Pro"], "quantity": 1},
                        {"product_id": p_map["Stainless Water Bottle"], "quantity": 2}
                    ])
                
                # Order 2
                if "Smart Watch Active" in p_map and "Organic Green Tea" in p_map:
                    self.order_service.place_order([
                        {"product_id": p_map["Smart Watch Active"], "quantity": 2},
                        {"product_id": p_map["Organic Green Tea"], "quantity": 5}
                    ])
                    
                # Order 3
                if "Noise-Cancelling Headphones" in p_map and "Superfood Blender Pro" in p_map:
                    self.order_service.place_order([
                        {"product_id": p_map["Noise-Cancelling Headphones"], "quantity": 1},
                        {"product_id": p_map["Superfood Blender Pro"], "quantity": 1}
                    ])
                console.print("[bold green]Mock orders seeded successfully![/bold green]")
                logger.info("Database successfully seeded with products and mock order history.")
            except Exception as e:
                console.print(f"[red]Error seeding orders: {e}[/red]")
                logger.error(f"Error seeding mock orders: {e}", exc_info=True)


if __name__ == "__main__":
    app = ECommerceApp()
    app.run()
