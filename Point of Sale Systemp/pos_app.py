"""Counter POS — a standalone Python desktop point-of-sale application.

Run with:
    python3 pos_app.py

The application uses only Python's standard library. Products, stock, held
orders, and completed sales are persisted in a local SQLite database.
"""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Callable

try:
    import tkinter as tk
    from tkinter import messagebox, simpledialog
except ModuleNotFoundError as error:
    raise SystemExit(
        "Counter POS requires Tkinter. On Debian/Ubuntu, install it with "
        "'sudo apt install python3-tk', then run this command again."
    ) from error


APP_DIR = Path(__file__).resolve().parent
DEFAULT_DATABASE = APP_DIR / "counter_pos.db"
TAX_RATE = 0.085

COLORS = {
    "ink": "#20251F",
    "muted": "#858B84",
    "line": "#E0E3DC",
    "canvas": "#F5F6F1",
    "panel": "#FFFFFF",
    "sidebar": "#1E2823",
    "sidebar_muted": "#9FA9A3",
    "accent": "#C8F06C",
    "accent_dark": "#1D271F",
    "success": "#658C55",
    "danger": "#B65447",
}

PRODUCT_COLORS = {
    "sage": "#D8E3D2",
    "coffee": "#D9C6B1",
    "wheat": "#EAD8AE",
    "olive": "#CCD1A8",
    "blue": "#CCDCE4",
    "rose": "#E3C9C5",
    "linen": "#DDD8CD",
    "cocoa": "#CBB8AD",
    "mint": "#CCE3DC",
    "peach": "#EACDB3",
}


@dataclass(frozen=True)
class Product:
    id: int
    name: str
    detail: str
    price: float
    category: str
    stock: int
    color: str
    mark: str


class POSDatabase:
    """SQLite persistence for products and sales."""

    def __init__(self, path: str | Path = DEFAULT_DATABASE) -> None:
        self.connection = sqlite3.connect(path)
        self.connection.row_factory = sqlite3.Row
        self._create_schema()
        self._seed_products()

    def _create_schema(self) -> None:
        self.connection.executescript(
            """
            PRAGMA foreign_keys = ON;

            CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                detail TEXT NOT NULL,
                price REAL NOT NULL CHECK (price >= 0),
                category TEXT NOT NULL,
                stock INTEGER NOT NULL DEFAULT 0 CHECK (stock >= 0),
                color TEXT NOT NULL,
                mark TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS sales (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                created_at TEXT NOT NULL,
                status TEXT NOT NULL CHECK (status IN ('held', 'completed')),
                payment_method TEXT,
                customer TEXT,
                subtotal REAL NOT NULL,
                discount REAL NOT NULL DEFAULT 0,
                tax REAL NOT NULL,
                total REAL NOT NULL
            );

            CREATE TABLE IF NOT EXISTS sale_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                sale_id INTEGER NOT NULL REFERENCES sales(id) ON DELETE CASCADE,
                product_id INTEGER NOT NULL REFERENCES products(id),
                product_name TEXT NOT NULL,
                unit_price REAL NOT NULL,
                quantity INTEGER NOT NULL CHECK (quantity > 0)
            );
            """
        )
        self.connection.commit()

    def _seed_products(self) -> None:
        count = self.connection.execute("SELECT COUNT(*) FROM products").fetchone()[0]
        if count:
            return
        products = [
            ("Oat Milk", "Original · 1L", 4.50, "Beverages", 18, "sage", "OAT"),
            ("Cold Brew", "Classic · 330ml", 5.25, "Beverages", 12, "coffee", "CB"),
            ("Sourdough", "Freshly baked", 6.75, "Bakery", 8, "wheat", "SD"),
            ("Olive Oil", "Extra virgin · 500ml", 14.90, "Pantry", 6, "olive", "EVOO"),
            ("Sea Salt Crisps", "Kettle cooked · 150g", 3.95, "Snacks", 24, "blue", "SALT"),
            ("Granola", "Almond & honey · 400g", 8.25, "Pantry", 15, "rose", "GR"),
            ("Linen Towel", "Natural stripe", 12.00, "Home", 9, "linen", "LT"),
            ("Dark Chocolate", "Sea salt · 70%", 4.75, "Snacks", 20, "cocoa", "70%"),
            ("Sparkling Water", "Lime · 330ml", 2.75, "Beverages", 30, "mint", "LIME"),
            ("Almond Croissant", "Freshly baked", 4.95, "Bakery", 5, "peach", "AC"),
            ("Herbal Tea", "Chamomile · 20 bags", 6.40, "Beverages", 14, "sage", "TEA"),
            ("Tomato Pasta", "Bronze cut · 500g", 4.20, "Pantry", 22, "peach", "PASTA"),
        ]
        self.connection.executemany(
            """
            INSERT INTO products
                (name, detail, price, category, stock, color, mark)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            products,
        )
        self.connection.commit()

    def products(self, category: str = "All items", query: str = "") -> list[Product]:
        clauses: list[str] = []
        values: list[str] = []
        if category != "All items":
            clauses.append("category = ?")
            values.append(category)
        if query.strip():
            clauses.append("(name LIKE ? OR detail LIKE ?)")
            term = f"%{query.strip()}%"
            values.extend([term, term])
        where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
        rows = self.connection.execute(
            f"SELECT * FROM products {where} ORDER BY name", values
        ).fetchall()
        return [Product(**dict(row)) for row in rows]

    def product(self, product_id: int) -> Product:
        row = self.connection.execute(
            "SELECT * FROM products WHERE id = ?", (product_id,)
        ).fetchone()
        if row is None:
            raise ValueError("Product does not exist.")
        return Product(**dict(row))

    def save_sale(
        self,
        cart: dict[int, int],
        *,
        status: str,
        payment_method: str | None,
        customer: str,
        discount_rate: float,
    ) -> int:
        if not cart:
            raise ValueError("The order is empty.")
        products = [self.product(product_id) for product_id in cart]
        for product in products:
            if status == "completed" and cart[product.id] > product.stock:
                raise ValueError(f"Only {product.stock} {product.name} are in stock.")

        subtotal = sum(product.price * cart[product.id] for product in products)
        discount = subtotal * discount_rate
        taxable = subtotal - discount
        tax = taxable * TAX_RATE
        total = taxable + tax

        with self.connection:
            cursor = self.connection.execute(
                """
                INSERT INTO sales
                    (created_at, status, payment_method, customer,
                     subtotal, discount, tax, total)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    datetime.now().isoformat(timespec="seconds"),
                    status,
                    payment_method,
                    customer or None,
                    subtotal,
                    discount,
                    tax,
                    total,
                ),
            )
            sale_id = int(cursor.lastrowid)
            self.connection.executemany(
                """
                INSERT INTO sale_items
                    (sale_id, product_id, product_name, unit_price, quantity)
                VALUES (?, ?, ?, ?, ?)
                """,
                [
                    (sale_id, product.id, product.name, product.price, cart[product.id])
                    for product in products
                ],
            )
            if status == "completed":
                self.connection.executemany(
                    "UPDATE products SET stock = stock - ? WHERE id = ?",
                    [(cart[product.id], product.id) for product in products],
                )
        return sale_id

    def held_sales(self) -> list[sqlite3.Row]:
        return self.connection.execute(
            """
            SELECT s.*, SUM(si.quantity) AS item_count
            FROM sales s
            JOIN sale_items si ON si.sale_id = s.id
            WHERE s.status = 'held'
            GROUP BY s.id
            ORDER BY s.id DESC
            """
        ).fetchall()

    def resume_sale(self, sale_id: int) -> tuple[dict[int, int], str, float]:
        sale = self.connection.execute(
            "SELECT * FROM sales WHERE id = ? AND status = 'held'", (sale_id,)
        ).fetchone()
        if sale is None:
            raise ValueError("Held order was not found.")
        items = self.connection.execute(
            "SELECT product_id, quantity FROM sale_items WHERE sale_id = ?", (sale_id,)
        ).fetchall()
        cart = {row["product_id"]: row["quantity"] for row in items}
        discount_rate = sale["discount"] / sale["subtotal"] if sale["subtotal"] else 0
        with self.connection:
            self.connection.execute("DELETE FROM sales WHERE id = ?", (sale_id,))
        return cart, sale["customer"] or "", discount_rate

    def close(self) -> None:
        self.connection.close()


class ScrollFrame(tk.Frame):
    """A vertically scrolling frame that responds to the mouse wheel."""

    def __init__(self, parent: tk.Misc, *, background: str) -> None:
        super().__init__(parent, bg=background)
        self.canvas = tk.Canvas(
            self, bg=background, highlightthickness=0, bd=0
        )
        scrollbar = tk.Scrollbar(
            self, orient="vertical", command=self.canvas.yview, bd=0
        )
        self.content = tk.Frame(self.canvas, bg=background)
        self.window = self.canvas.create_window(
            (0, 0), window=self.content, anchor="nw"
        )
        self.canvas.configure(yscrollcommand=scrollbar.set)
        self.canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        self.content.bind(
            "<Configure>",
            lambda _event: self.canvas.configure(
                scrollregion=self.canvas.bbox("all")
            ),
        )
        self.canvas.bind(
            "<Configure>",
            lambda event: self.canvas.itemconfigure(self.window, width=event.width),
        )
        self.canvas.bind("<MouseWheel>", self._wheel)
        self.content.bind("<MouseWheel>", self._wheel)

    def _wheel(self, event: tk.Event) -> None:
        self.canvas.yview_scroll(int(-event.delta / 120), "units")


class CounterPOS(tk.Tk):
    """Main desktop register window."""

    def __init__(self, database: POSDatabase | None = None) -> None:
        super().__init__()
        self.db = database or POSDatabase()
        self.cart: dict[int, int] = {}
        self.category = "All items"
        self.customer = ""
        self.discount_rate = 0.0
        self.search_var = tk.StringVar()
        self.clock_var = tk.StringVar()
        self.toast_job: str | None = None

        self.title("Counter POS")
        self.geometry("1400x840")
        self.minsize(1080, 680)
        self.configure(bg=COLORS["canvas"])
        self.protocol("WM_DELETE_WINDOW", self._close)
        self.option_add("*Font", ("Arial", 10))

        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)
        self._build_sidebar()
        self._build_catalog()
        self._build_cart()
        self._bind_shortcuts()
        self._refresh_products()
        self._refresh_cart()
        self._update_clock()

    @staticmethod
    def _label(
        parent: tk.Misc,
        text: str = "",
        *,
        size: int = 10,
        weight: str = "normal",
        color: str = COLORS["ink"],
        background: str = COLORS["panel"],
        **kwargs: object,
    ) -> tk.Label:
        return tk.Label(
            parent,
            text=text,
            font=("Arial", size, weight),
            fg=color,
            bg=background,
            **kwargs,
        )

    @staticmethod
    def _button(
        parent: tk.Misc,
        text: str,
        command: Callable[[], None],
        *,
        background: str = COLORS["panel"],
        foreground: str = COLORS["ink"],
        activebackground: str | None = None,
        font: tuple[str, int, str] = ("Arial", 10, "normal"),
        **kwargs: object,
    ) -> tk.Button:
        return tk.Button(
            parent,
            text=text,
            command=command,
            bg=background,
            fg=foreground,
            activebackground=activebackground or background,
            activeforeground=foreground,
            font=font,
            relief="flat",
            bd=0,
            cursor="hand2",
            **kwargs,
        )

    def _build_sidebar(self) -> None:
        sidebar = tk.Frame(self, bg=COLORS["sidebar"], width=205)
        sidebar.grid(row=0, column=0, sticky="nsew")
        sidebar.grid_propagate(False)

        brand = tk.Frame(sidebar, bg=COLORS["sidebar"])
        brand.pack(fill="x", padx=22, pady=(27, 30))
        mark = tk.Canvas(
            brand, width=30, height=30, bg=COLORS["sidebar"], highlightthickness=0
        )
        mark.create_rectangle(1, 1, 29, 29, fill=COLORS["accent"], outline="", width=0)
        mark.create_line(9, 20, 11, 13, fill=COLORS["sidebar"], width=4)
        mark.create_line(15, 20, 17, 9, fill=COLORS["sidebar"], width=4)
        mark.create_line(21, 20, 22, 15, fill=COLORS["sidebar"], width=4)
        mark.pack(side="left")
        self._label(
            brand,
            "Counter",
            size=18,
            weight="bold",
            color="#F4F6F2",
            background=COLORS["sidebar"],
        ).pack(side="left", padx=10)

        navigation = [
            ("Register", lambda: self.notify("Register is open")),
            ("Orders", self._show_sales_summary),
            ("Inventory", self._show_inventory),
            ("Customers", lambda: self.notify("Add a customer from the current order")),
            ("Reports", self._show_sales_summary),
        ]
        for index, (name, command) in enumerate(navigation):
            button = self._button(
                sidebar,
                f"  {name}",
                command,
                background=COLORS["accent"] if index == 0 else COLORS["sidebar"],
                foreground=COLORS["accent_dark"]
                if index == 0
                else COLORS["sidebar_muted"],
                activebackground="#344139",
                font=("Arial", 10, "bold" if index == 0 else "normal"),
                anchor="w",
                padx=18,
            )
            button.pack(fill="x", padx=14, pady=3, ipady=10)

        profile = tk.Frame(sidebar, bg=COLORS["sidebar"])
        profile.pack(side="bottom", fill="x", padx=20, pady=20)
        tk.Frame(profile, bg="#3A463F", height=1).pack(fill="x", pady=(0, 16))
        avatar = self._label(
            profile,
            "MK",
            size=9,
            weight="bold",
            background="#D8C9F1",
            color="#28322B",
            width=4,
            height=2,
        )
        avatar.pack(side="left")
        person = tk.Frame(profile, bg=COLORS["sidebar"])
        person.pack(side="left", padx=10)
        self._label(
            person,
            "Maya Kim",
            size=10,
            weight="bold",
            color="#F1F3EF",
            background=COLORS["sidebar"],
        ).pack(anchor="w")
        self._label(
            person,
            "Store manager",
            size=8,
            color=COLORS["sidebar_muted"],
            background=COLORS["sidebar"],
        ).pack(anchor="w", pady=(2, 0))

    def _build_catalog(self) -> None:
        center = tk.Frame(self, bg=COLORS["canvas"])
        center.grid(row=0, column=1, sticky="nsew")
        center.grid_rowconfigure(2, weight=1)
        center.grid_columnconfigure(0, weight=1)

        header = tk.Frame(center, bg="#FAFBF8", height=86)
        header.grid(row=0, column=0, sticky="ew")
        header.grid_propagate(False)
        intro = tk.Frame(header, bg="#FAFBF8")
        intro.pack(side="left", padx=30, pady=18)
        self.date_label = self._label(
            intro,
            "",
            size=8,
            color=COLORS["muted"],
            background="#FAFBF8",
        )
        self.date_label.pack(anchor="w")
        self._label(
            intro,
            "Good morning, Maya",
            size=17,
            weight="bold",
            background="#FAFBF8",
        ).pack(anchor="w", pady=(4, 0))
        status = tk.Frame(header, bg=COLORS["panel"], padx=11, pady=8)
        status.pack(side="right", padx=30)
        self._label(
            status,
            "●",
            size=9,
            color=COLORS["success"],
            background=COLORS["panel"],
        ).pack(side="left")
        self._label(
            status,
            "Register open",
            size=9,
            weight="bold",
            color="#5D645D",
            background=COLORS["panel"],
        ).pack(side="left", padx=(6, 0))

        tools = tk.Frame(center, bg=COLORS["canvas"])
        tools.grid(row=1, column=0, sticky="ew", padx=28, pady=(23, 13))
        tools.grid_columnconfigure(0, weight=1)
        search = tk.Frame(
            tools,
            bg=COLORS["panel"],
            highlightthickness=1,
            highlightbackground=COLORS["line"],
        )
        search.grid(row=0, column=0, sticky="ew", padx=(0, 10))
        self._label(
            search,
            "Search",
            size=9,
            weight="bold",
            color=COLORS["muted"],
            background=COLORS["panel"],
        ).pack(side="left", padx=(13, 8))
        self.search_entry = tk.Entry(
            search,
            textvariable=self.search_var,
            bd=0,
            relief="flat",
            bg=COLORS["panel"],
            fg=COLORS["ink"],
            insertbackground=COLORS["ink"],
            font=("Arial", 10),
        )
        self.search_entry.pack(side="left", fill="x", expand=True, ipady=13)
        self.search_entry.bind("<KeyRelease>", lambda _event: self._refresh_products())
        self._label(
            search,
            "Ctrl K",
            size=8,
            color="#9CA09B",
            background="#F2F3F0",
            padx=6,
            pady=3,
        ).pack(side="right", padx=10)
        self._button(
            tools,
            "Held orders",
            self._show_held_orders,
            background=COLORS["panel"],
            foreground="#505750",
            font=("Arial", 9, "bold"),
            padx=15,
        ).grid(row=0, column=1, ipady=13)

        content = tk.Frame(center, bg=COLORS["canvas"])
        content.grid(row=2, column=0, sticky="nsew", padx=28)
        content.grid_rowconfigure(2, weight=1)
        content.grid_columnconfigure(0, weight=1)

        self.category_frame = tk.Frame(content, bg=COLORS["canvas"])
        self.category_frame.grid(row=0, column=0, sticky="ew", pady=(2, 20))
        self._build_categories()

        heading = tk.Frame(content, bg=COLORS["canvas"])
        heading.grid(row=1, column=0, sticky="ew", pady=(0, 12))
        self.section_title = self._label(
            heading,
            "Popular products",
            size=15,
            weight="bold",
            background=COLORS["canvas"],
        )
        self.section_title.pack(side="left")
        self.product_count = self._label(
            heading, "", size=9, color=COLORS["muted"], background=COLORS["canvas"]
        )
        self.product_count.pack(side="right")

        self.products_scroll = ScrollFrame(content, background=COLORS["canvas"])
        self.products_scroll.grid(row=2, column=0, sticky="nsew")
        self.products_scroll.canvas.bind(
            "<Configure>", lambda _event: self.after_idle(self._refresh_products)
        )

    def _build_categories(self) -> None:
        for category in ["All items", "Beverages", "Bakery", "Pantry", "Snacks", "Home"]:
            selected = category == self.category
            self._button(
                self.category_frame,
                category,
                lambda value=category: self._select_category(value),
                background=COLORS["sidebar"] if selected else COLORS["canvas"],
                foreground="#FFFFFF" if selected else "#6D736C",
                activebackground=COLORS["sidebar"],
                font=("Arial", 9, "bold" if selected else "normal"),
                padx=13,
                pady=8,
            ).pack(side="left", padx=(0, 7))

    def _build_cart(self) -> None:
        cart = tk.Frame(
            self,
            bg=COLORS["panel"],
            width=370,
            highlightthickness=1,
            highlightbackground=COLORS["line"],
        )
        cart.grid(row=0, column=2, sticky="nsew")
        cart.grid_propagate(False)
        cart.grid_rowconfigure(2, weight=1)
        cart.grid_columnconfigure(0, weight=1)

        header = tk.Frame(cart, bg=COLORS["panel"], height=86)
        header.grid(row=0, column=0, sticky="ew")
        header.grid_propagate(False)
        title = tk.Frame(header, bg=COLORS["panel"])
        title.pack(side="left", padx=22, pady=17)
        self._label(
            title, "Current order", size=16, weight="bold"
        ).pack(anchor="w")
        self.order_number = self._label(
            title, "New order", size=8, color=COLORS["muted"]
        )
        self.order_number.pack(anchor="w", pady=(4, 0))

        self.customer_button = self._button(
            cart,
            "Add customer\nEarn points and view history",
            self._add_customer,
            background="#FAFBF8",
            foreground="#454C45",
            font=("Arial", 9, "bold"),
            anchor="w",
            justify="left",
            padx=14,
            pady=10,
        )
        self.customer_button.grid(row=1, column=0, sticky="ew", padx=20, pady=(10, 4))

        self.cart_scroll = ScrollFrame(cart, background=COLORS["panel"])
        self.cart_scroll.grid(row=2, column=0, sticky="nsew", padx=20)

        footer = tk.Frame(cart, bg=COLORS["panel"])
        footer.grid(row=3, column=0, sticky="ew", padx=20, pady=(8, 18))
        actions = tk.Frame(footer, bg=COLORS["panel"])
        actions.pack(fill="x", pady=(0, 13))
        for name, command in [
            ("Hold", self._hold_order),
            ("Discount", self._apply_discount),
            ("Clear", self._clear_cart),
        ]:
            actions.grid_columnconfigure(
                ["Hold", "Discount", "Clear"].index(name), weight=1
            )
            self._button(
                actions,
                name,
                command,
                background="#F4F5F2",
                foreground="#626862",
                font=("Arial", 8, "bold"),
                pady=8,
            ).grid(
                row=0,
                column=["Hold", "Discount", "Clear"].index(name),
                sticky="ew",
                padx=3,
            )

        self.subtotal_label = self._total_row(footer, "Subtotal")
        self.discount_label = self._total_row(footer, "Discount")
        self.tax_label = self._total_row(footer, f"Tax ({TAX_RATE:.1%})")
        tk.Frame(footer, bg=COLORS["line"], height=1).pack(fill="x", pady=9)
        total_row = tk.Frame(footer, bg=COLORS["panel"])
        total_row.pack(fill="x")
        self._label(
            total_row, "Total", size=13, weight="bold"
        ).pack(side="left")
        self.total_label = self._label(
            total_row, "$0.00", size=17, weight="bold"
        )
        self.total_label.pack(side="right")
        self.charge_button = self._button(
            footer,
            "Charge $0.00",
            self._open_payment,
            background=COLORS["accent"],
            foreground=COLORS["accent_dark"],
            activebackground="#B8DF5D",
            font=("Arial", 11, "bold"),
            pady=13,
        )
        self.charge_button.pack(fill="x", pady=(14, 0))

    def _total_row(self, parent: tk.Misc, title: str) -> tk.Label:
        row = tk.Frame(parent, bg=COLORS["panel"])
        row.pack(fill="x", pady=3)
        self._label(
            row, title, size=9, color="#737973"
        ).pack(side="left")
        value = self._label(row, "$0.00", size=9, weight="bold")
        value.pack(side="right")
        return value

    def _bind_shortcuts(self) -> None:
        self.bind("<Control-k>", lambda _event: self._focus_search())
        self.bind("<F2>", lambda _event: self._hold_order())
        self.bind("<F4>", lambda _event: self._open_payment())
        self.bind("<Escape>", lambda _event: self.search_var.set(""))

    def _focus_search(self) -> str:
        self.search_entry.focus_set()
        self.search_entry.select_range(0, "end")
        return "break"

    def _select_category(self, category: str) -> None:
        self.category = category
        for widget in self.category_frame.winfo_children():
            widget.destroy()
        self._build_categories()
        self._refresh_products()

    def _refresh_products(self) -> None:
        if not hasattr(self, "products_scroll"):
            return
        for widget in self.products_scroll.content.winfo_children():
            widget.destroy()
        products = self.db.products(self.category, self.search_var.get())
        title = "Popular products" if self.category == "All items" else self.category
        self.section_title.configure(text=title)
        self.product_count.configure(
            text=f"{len(products)} product{'s' if len(products) != 1 else ''} available"
        )
        if not products:
            self._label(
                self.products_scroll.content,
                "No products found\nTry another search or category.",
                size=11,
                color=COLORS["muted"],
                background=COLORS["canvas"],
                justify="center",
            ).pack(pady=100)
            return

        width = max(self.products_scroll.canvas.winfo_width(), 500)
        columns = 3 if width >= 650 else 2
        for column in range(columns):
            self.products_scroll.content.grid_columnconfigure(column, weight=1)
        for index, product in enumerate(products):
            self._product_card(product).grid(
                row=index // columns,
                column=index % columns,
                sticky="nsew",
                padx=6,
                pady=6,
            )

    def _product_card(self, product: Product) -> tk.Frame:
        card = tk.Frame(
            self.products_scroll.content,
            bg=COLORS["panel"],
            highlightthickness=1,
            highlightbackground=COLORS["line"],
            cursor="hand2",
        )
        art_color = PRODUCT_COLORS.get(product.color, "#DDE1DA")
        art = tk.Frame(card, bg=art_color, height=100)
        art.pack(fill="x")
        art.pack_propagate(False)
        package = self._label(
            art,
            product.mark,
            size=8,
            weight="bold",
            background="#F7F7F3",
            color="#3E463F",
            width=7,
            height=3,
        )
        package.place(relx=0.5, rely=0.5, anchor="center")
        if product.id in self.cart:
            self._label(
                art,
                str(self.cart[product.id]),
                size=8,
                weight="bold",
                background=COLORS["sidebar"],
                color="#FFFFFF",
                width=2,
            ).place(relx=0.94, rely=0.12, anchor="ne")

        info = tk.Frame(card, bg=COLORS["panel"])
        info.pack(fill="both", expand=True, padx=12, pady=10)
        self._label(
            info, product.name, size=10, weight="bold", anchor="w"
        ).pack(fill="x")
        self._label(
            info,
            product.detail,
            size=8,
            color="#939893",
            anchor="w",
        ).pack(fill="x", pady=(3, 9))
        meta = tk.Frame(info, bg=COLORS["panel"])
        meta.pack(fill="x")
        self._label(
            meta, f"${product.price:.2f}", size=10, weight="bold"
        ).pack(side="left")
        self._label(
            meta,
            f"{product.stock} in stock",
            size=8,
            color="#858B84" if product.stock else COLORS["danger"],
        ).pack(side="right")

        def add(_event: tk.Event | None = None) -> None:
            self._add_to_cart(product)

        def bind_click(widget: tk.Misc) -> None:
            widget.bind("<Button-1>", add)
            for child in widget.winfo_children():
                bind_click(child)

        bind_click(card)
        return card

    def _add_to_cart(self, product: Product) -> None:
        quantity = self.cart.get(product.id, 0)
        if quantity >= product.stock:
            self.notify(f"Only {product.stock} {product.name} are available", error=True)
            return
        self.cart[product.id] = quantity + 1
        self._refresh_cart()
        self._refresh_products()

    def _change_quantity(self, product_id: int, change: int) -> None:
        product = self.db.product(product_id)
        next_quantity = self.cart.get(product_id, 0) + change
        if next_quantity > product.stock:
            self.notify(f"Only {product.stock} {product.name} are available", error=True)
            return
        if next_quantity <= 0:
            self.cart.pop(product_id, None)
        else:
            self.cart[product_id] = next_quantity
        self._refresh_cart()
        self._refresh_products()

    def _refresh_cart(self) -> None:
        for widget in self.cart_scroll.content.winfo_children():
            widget.destroy()
        if not self.cart:
            empty = tk.Frame(self.cart_scroll.content, bg=COLORS["panel"])
            empty.pack(fill="both", expand=True, pady=85)
            self._label(
                empty, "Your order is empty", size=12, weight="bold"
            ).pack()
            self._label(
                empty,
                "Select a product to start a new sale.",
                size=9,
                color=COLORS["muted"],
            ).pack(pady=(5, 0))
        else:
            for product_id, quantity in self.cart.items():
                self._cart_item(self.db.product(product_id), quantity).pack(fill="x")
        subtotal, discount, tax, total = self._totals()
        self.subtotal_label.configure(text=f"${subtotal:.2f}")
        self.discount_label.configure(text=f"-${discount:.2f}")
        self.tax_label.configure(text=f"${tax:.2f}")
        self.total_label.configure(text=f"${total:.2f}")
        item_count = sum(self.cart.values())
        self.charge_button.configure(
            text=f"Charge ${total:.2f}",
            state="normal" if item_count else "disabled",
            cursor="hand2" if item_count else "arrow",
        )
        self.customer_button.configure(
            text=(
                f"{self.customer}\nCustomer attached to this order"
                if self.customer
                else "Add customer\nEarn points and view history"
            )
        )

    def _cart_item(self, product: Product, quantity: int) -> tk.Frame:
        row = tk.Frame(self.cart_scroll.content, bg=COLORS["panel"])
        row.pack_propagate(False)
        art = self._label(
            row,
            product.mark,
            size=7,
            weight="bold",
            background=PRODUCT_COLORS.get(product.color, "#DDE1DA"),
            width=7,
            height=4,
        )
        art.pack(side="left", pady=12)
        details = tk.Frame(row, bg=COLORS["panel"])
        details.pack(side="left", fill="both", expand=True, padx=11, pady=12)
        top = tk.Frame(details, bg=COLORS["panel"])
        top.pack(fill="x")
        self._label(
            top, product.name, size=9, weight="bold"
        ).pack(side="left")
        self._label(
            top, f"${product.price * quantity:.2f}", size=9, weight="bold"
        ).pack(side="right")
        self._label(
            details, product.detail, size=8, color=COLORS["muted"]
        ).pack(anchor="w", pady=(2, 7))
        controls = tk.Frame(details, bg=COLORS["panel"])
        controls.pack(fill="x")
        self._button(
            controls,
            "−",
            lambda: self._change_quantity(product.id, -1),
            background="#F1F3EF",
            font=("Arial", 10, "bold"),
            width=3,
        ).pack(side="left")
        self._label(
            controls, str(quantity), size=9, weight="bold", width=3
        ).pack(side="left")
        self._button(
            controls,
            "+",
            lambda: self._change_quantity(product.id, 1),
            background="#F1F3EF",
            font=("Arial", 10, "bold"),
            width=3,
        ).pack(side="left")
        self._button(
            controls,
            "Remove",
            lambda: self._remove_item(product.id),
            foreground=COLORS["danger"],
            font=("Arial", 8, "normal"),
        ).pack(side="right")
        tk.Frame(row, height=1, bg="#ECEEE9").pack(side="bottom", fill="x")
        return row

    def _remove_item(self, product_id: int) -> None:
        self.cart.pop(product_id, None)
        self._refresh_cart()
        self._refresh_products()

    def _totals(self) -> tuple[float, float, float, float]:
        subtotal = sum(
            self.db.product(product_id).price * quantity
            for product_id, quantity in self.cart.items()
        )
        discount = subtotal * self.discount_rate
        taxable = subtotal - discount
        tax = taxable * TAX_RATE
        return subtotal, discount, tax, taxable + tax

    def _add_customer(self) -> None:
        name = simpledialog.askstring(
            "Customer", "Customer name:", initialvalue=self.customer, parent=self
        )
        if name is not None:
            self.customer = name.strip()
            self._refresh_cart()

    def _apply_discount(self) -> None:
        percent = simpledialog.askfloat(
            "Order discount",
            "Discount percentage (0–100):",
            initialvalue=self.discount_rate * 100,
            minvalue=0,
            maxvalue=100,
            parent=self,
        )
        if percent is not None:
            self.discount_rate = percent / 100
            self._refresh_cart()
            self.notify(f"{percent:g}% discount applied")

    def _clear_cart(self) -> None:
        if not self.cart:
            return
        if messagebox.askyesno(
            "Clear order", "Remove every item from the current order?", parent=self
        ):
            self.cart.clear()
            self.customer = ""
            self.discount_rate = 0
            self._refresh_cart()
            self._refresh_products()

    def _hold_order(self) -> None:
        if not self.cart:
            self.notify("Add products before holding an order", error=True)
            return
        sale_id = self.db.save_sale(
            self.cart,
            status="held",
            payment_method=None,
            customer=self.customer,
            discount_rate=self.discount_rate,
        )
        self.cart = {}
        self.customer = ""
        self.discount_rate = 0
        self._refresh_cart()
        self._refresh_products()
        self.notify(f"Order #{sale_id:04d} held")

    def _show_held_orders(self) -> None:
        rows = self.db.held_sales()
        dialog = self._dialog("Held orders", "520x430")
        body = tk.Frame(dialog, bg=COLORS["panel"])
        body.pack(fill="both", expand=True, padx=24, pady=(0, 24))
        if not rows:
            self._label(
                body,
                "No held orders\nHeld orders will appear here.",
                size=11,
                color=COLORS["muted"],
                justify="center",
            ).pack(expand=True)
            return
        for sale in rows:
            row = tk.Frame(
                body,
                bg="#F6F7F4",
                highlightthickness=1,
                highlightbackground=COLORS["line"],
            )
            row.pack(fill="x", pady=5)
            info = tk.Frame(row, bg="#F6F7F4")
            info.pack(side="left", padx=13, pady=11)
            self._label(
                info,
                f"Order #{sale['id']:04d}",
                size=10,
                weight="bold",
                background="#F6F7F4",
            ).pack(anchor="w")
            created = datetime.fromisoformat(sale["created_at"]).strftime("%d %b · %H:%M")
            self._label(
                info,
                f"{created} · {sale['item_count']} items · ${sale['total']:.2f}",
                size=8,
                color=COLORS["muted"],
                background="#F6F7F4",
            ).pack(anchor="w", pady=(3, 0))
            self._button(
                row,
                "Resume",
                lambda sale_id=sale["id"], window=dialog: self._resume_order(
                    sale_id, window
                ),
                background=COLORS["accent"],
                font=("Arial", 9, "bold"),
                padx=14,
                pady=8,
            ).pack(side="right", padx=12)

    def _resume_order(self, sale_id: int, dialog: tk.Toplevel) -> None:
        if self.cart and not messagebox.askyesno(
            "Replace current order",
            "Resuming this order will replace the current cart. Continue?",
            parent=dialog,
        ):
            return
        self.cart, self.customer, self.discount_rate = self.db.resume_sale(sale_id)
        dialog.destroy()
        self._refresh_cart()
        self._refresh_products()
        self.notify(f"Order #{sale_id:04d} resumed")

    def _open_payment(self) -> None:
        if not self.cart:
            self.notify("The order is empty", error=True)
            return
        dialog = self._dialog("Take payment", "460x500")
        _, _, _, total = self._totals()
        amount = tk.Frame(dialog, bg="#F1F3ED")
        amount.pack(fill="x", padx=24, pady=(2, 23))
        self._label(
            amount, "Amount due", size=10, color="#687068", background="#F1F3ED"
        ).pack(side="left", padx=16, pady=18)
        self._label(
            amount,
            f"${total:.2f}",
            size=19,
            weight="bold",
            background="#F1F3ED",
        ).pack(side="right", padx=16)
        self._label(
            dialog,
            "PAYMENT METHOD",
            size=8,
            weight="bold",
            color=COLORS["muted"],
        ).pack(anchor="w", padx=24, pady=(0, 8))
        method = tk.StringVar(value="Card")
        for name, detail in [
            ("Card", "Tap, insert, or swipe"),
            ("Cash", "Record a cash payment"),
        ]:
            row = tk.Frame(
                dialog,
                bg="#F8F9F6",
                highlightthickness=1,
                highlightbackground=COLORS["line"],
            )
            row.pack(fill="x", padx=24, pady=4)
            radio = tk.Radiobutton(
                row,
                text=f"{name}\n{detail}",
                variable=method,
                value=name,
                bg="#F8F9F6",
                activebackground="#F8F9F6",
                fg=COLORS["ink"],
                selectcolor=COLORS["accent"],
                anchor="w",
                justify="left",
                font=("Arial", 10, "bold"),
                padx=10,
                pady=10,
            )
            radio.pack(fill="x")
        self._button(
            dialog,
            f"Confirm payment · ${total:.2f}",
            lambda: self._complete_sale(method.get(), dialog),
            background=COLORS["accent"],
            foreground=COLORS["accent_dark"],
            activebackground="#B8DF5D",
            font=("Arial", 11, "bold"),
            pady=13,
        ).pack(side="bottom", fill="x", padx=24, pady=24)

    def _complete_sale(self, method: str, dialog: tk.Toplevel) -> None:
        try:
            sale_id = self.db.save_sale(
                self.cart,
                status="completed",
                payment_method=method.lower(),
                customer=self.customer,
                discount_rate=self.discount_rate,
            )
        except ValueError as error:
            messagebox.showerror("Unable to complete sale", str(error), parent=dialog)
            return
        for widget in dialog.winfo_children():
            widget.destroy()
        success = tk.Frame(dialog, bg=COLORS["panel"])
        success.pack(fill="both", expand=True)
        self._label(
            success,
            "✓",
            size=28,
            weight="bold",
            background=COLORS["accent"],
            color=COLORS["accent_dark"],
            width=3,
            height=2,
        ).pack(pady=(75, 18))
        self._label(
            success, "Payment complete", size=18, weight="bold"
        ).pack()
        self._label(
            success,
            f"Order #{sale_id:04d} was paid by {method.lower()}.",
            size=9,
            color=COLORS["muted"],
        ).pack(pady=(6, 0))
        self.cart = {}
        self.customer = ""
        self.discount_rate = 0
        self._refresh_cart()
        self._refresh_products()
        self.after(1800, dialog.destroy)

    def _dialog(self, title: str, geometry: str) -> tk.Toplevel:
        dialog = tk.Toplevel(self)
        dialog.title(title)
        dialog.geometry(geometry)
        dialog.resizable(False, False)
        dialog.configure(bg=COLORS["panel"])
        dialog.transient(self)
        dialog.grab_set()
        header = tk.Frame(dialog, bg=COLORS["panel"])
        header.pack(fill="x", padx=24, pady=22)
        self._label(header, title, size=17, weight="bold").pack(side="left")
        self._button(
            header,
            "Close",
            dialog.destroy,
            foreground=COLORS["muted"],
            font=("Arial", 8, "normal"),
        ).pack(side="right")
        return dialog

    def _show_inventory(self) -> None:
        low_stock = [product for product in self.db.products() if product.stock <= 8]
        message = "\n".join(
            f"{product.name}: {product.stock} remaining" for product in low_stock
        )
        messagebox.showinfo(
            "Inventory",
            f"Low-stock products\n\n{message or 'All stock levels are healthy.'}",
            parent=self,
        )

    def _show_sales_summary(self) -> None:
        row = self.db.connection.execute(
            """
            SELECT COUNT(*) AS orders, COALESCE(SUM(total), 0) AS revenue
            FROM sales WHERE status = 'completed'
            """
        ).fetchone()
        messagebox.showinfo(
            "Sales summary",
            f"Completed orders: {row['orders']}\nRevenue: ${row['revenue']:.2f}",
            parent=self,
        )

    def notify(self, message: str, *, error: bool = False) -> None:
        if hasattr(self, "toast") and self.toast.winfo_exists():
            self.toast.destroy()
        self.toast = self._label(
            self,
            message,
            size=9,
            weight="bold",
            color="#FFFFFF",
            background=COLORS["danger"] if error else COLORS["sidebar"],
            padx=16,
            pady=10,
        )
        self.toast.place(relx=0.5, rely=0.965, anchor="s")
        if self.toast_job:
            self.after_cancel(self.toast_job)
        self.toast_job = self.after(2400, self.toast.destroy)

    def _update_clock(self) -> None:
        now = datetime.now()
        self.date_label.configure(text=now.strftime("%A, %d %B").upper())
        self.clock_var.set(now.strftime("%H:%M"))
        self.after(30_000, self._update_clock)

    def _close(self) -> None:
        self.db.close()
        self.destroy()


def main() -> None:
    app = CounterPOS()
    app.mainloop()


if __name__ == "__main__":
    main()
