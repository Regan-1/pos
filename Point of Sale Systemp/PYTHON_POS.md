# Counter POS — Python desktop app

The Python edition is a standalone desktop point-of-sale application built with
Tkinter and SQLite. It requires no Python packages outside the standard library.

## Run

```bash
python3 pos_app.py
```

Tkinter ships with standard Python on Windows and macOS. Some Linux
distributions package it separately; on Debian or Ubuntu, install it first with:

```bash
sudo apt install python3-tk
```

The local database is created automatically as `counter_pos.db` on first run.
It stores the product catalog, inventory levels, held orders, completed sales,
payment methods, and customer names.

## Features

- Searchable product catalog with category filters
- Live stock checks and inventory updates
- Quantity controls, order discounts, and customer attachment
- Automatic subtotal, 8.5% tax, and total calculation
- Hold and resume orders
- Card and cash checkout
- Persistent completed-sales summary
- Keyboard shortcuts:
  - `Ctrl+K`: focus product search
  - `F2`: hold the current order
  - `F4`: open checkout

This desktop program is separate from the browser preview in `src/`, which is
retained as the original React implementation.
