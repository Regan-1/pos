import { useMemo, useState } from "react"

type IconName = "grid" | "orders" | "box" | "users" | "chart" | "settings" | "search" | "scan" | "bell" | "chevron" | "minus" | "plus" | "trash" | "pause" | "tag" | "card" | "cash" | "check" | "menu" | "close"

function Icon({ name, size = 20 }: { name: IconName size?: number }) {
  const paths: Record<IconName, React.ReactNode> = {
    grid: (
      <>
        <rect x="3" y="3" width="7" height="7" rx="2" />
        <rect x="14" y="3" width="7" height="7" rx="2" />
        <rect x="3" y="14" width="7" height="7" rx="2" />
        <rect x="14" y="14" width="7" height="7" rx="2" />
      </>
    ),
    orders: (
      <>
        <path d="M6 3h12v18l-3-2-3 2-3-2-3 2V3Z" />
        <path d="M9 8h6M9 12h6" />
      </>
    ),
    box: (
      <>
        <path d="m4 7 8-4 8 4-8 4-8-4Z" />
        <path d="m4 7 8 4 8-4v10l-8 4-8-4V7Z" />
        <path d="M12 11v10" />
      </>
    ),
    users: (
      <>
        <path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2" />
        <circle cx="9" cy="7" r="4" />
        <path d="M22 21v-2a4 4 0 0 0-3-3.87M16 3.13a4 4 0 0 1 0 7.75" />
      </>
    ),
    chart: (
      <>
        <path d="M4 19V9M10 19V5M16 19v-7M22 19H2" />
      </>
    ),
    settings: (
      <>
        <circle cx="12" cy="12" r="3" />
        <path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06-2.83 2.83-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21h-4v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06-2.83-2.83.06-.06A1.65 1.65 0 0 0 4.6 15a1.65 1.65 0 0 0-1.51-1H3v-4h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06 2.83-2.83.06.06A1.65 1.65 0 0 0 9 4.6a1.65 1.65 0 0 0 1-1.51V3h4v.09A1.65 1.65 0 0 0 15 4.6a1.65 1.65 0 0 0 1.82-.33l.06-.06 2.83 2.83-.06.06A1.65 1.65 0 0 0 19.4 9a1.65 1.65 0 0 0 1.51 1H21v4h-.09A1.65 1.65 0 0 0 19.4 15Z" />
      </>
    ),
    search: (
      <>
        <circle cx="11" cy="11" r="7" />
        <path d="m20 20-4-4" />
      </>
    ),
    scan: (
      <>
        <path d="M4 7V4h3M17 4h3v3M20 17v3h-3M7 20H4v-3M7 12h10" />
      </>
    ),
    bell: (
      <>
        <path d="M18 8a6 6 0 0 0-12 0c0 7-3 7-3 9h18c0-2-3-2-3-9M10 21h4" />
      </>
    ),
    chevron: <path d="m9 18 6-6-6-6" />,
    minus: <path d="M5 12h14" />,
    plus: <path d="M12 5v14M5 12h14" />,
    trash: (
      <>
        <path d="M3 6h18M8 6V4h8v2M19 6l-1 15H6L5 6M10 11v5M14 11v5" />
      </>
    ),
    pause: (
      <>
        <rect x="5" y="4" width="4" height="16" rx="1" />
        <rect x="15" y="4" width="4" height="16" rx="1" />
      </>
    ),
    tag: (
      <>
        <path d="M20 13 13 20l-9-9V4h7l9 9Z" />
        <circle cx="8.5" cy="8.5" r="1.2" />
      </>
    ),
    card: (
      <>
        <rect x="2" y="5" width="20" height="14" rx="3" />
        <path d="M2 10h20M6 15h4" />
      </>
    ),
    cash: (
      <>
        <rect x="2" y="5" width="20" height="14" rx="2" />
        <circle cx="12" cy="12" r="3" />
        <path d="M6 9H5v1M18 15h1v-1" />
      </>
    ),
    check: <path d="m5 12 4 4L19 6" />,
    menu: <path d="M4 7h16M4 12h16M4 17h16" />,
    close: <path d="m6 6 12 12M18 6 6 18" />,
  }
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.8"
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
    >
      {paths[name]}
    </svg>
  )
}

const categories = [
  "All items",
  "Beverages",
  "Bakery",
  "Pantry",
  "Snacks",
  "Home",
]

const products = [
  {
    id: 1,
    name: "Oat Milk",
    detail: "Original · 1L",
    price: 4.5,
    category: "Beverages",
    stock: 18,
    color: "sage",
    mark: "OAT",
  },
  {
    id: 2,
    name: "Cold Brew",
    detail: "Classic · 330ml",
    price: 5.25,
    category: "Beverages",
    stock: 12,
    color: "coffee",
    mark: "CB",
  },
  {
    id: 3,
    name: "Sourdough",
    detail: "Freshly baked",
    price: 6.75,
    category: "Bakery",
    stock: 8,
    color: "wheat",
    mark: "SD",
  },
  {
    id: 4,
    name: "Olive Oil",
    detail: "Extra virgin · 500ml",
    price: 14.9,
    category: "Pantry",
    stock: 6,
    color: "olive",
    mark: "EVOO",
  },
  {
    id: 5,
    name: "Sea Salt Crisps",
    detail: "Kettle cooked · 150g",
    price: 3.95,
    category: "Snacks",
    stock: 24,
    color: "blue",
    mark: "SALT",
  },
  {
    id: 6,
    name: "Granola",
    detail: "Almond & honey · 400g",
    price: 8.25,
    category: "Pantry",
    stock: 15,
    color: "rose",
    mark: "GR",
  },
  {
    id: 7,
    name: "Linen Towel",
    detail: "Natural stripe",
    price: 12,
    category: "Home",
    stock: 9,
    color: "linen",
    mark: "LT",
  },
  {
    id: 8,
    name: "Dark Chocolate",
    detail: "Sea salt · 70%",
    price: 4.75,
    category: "Snacks",
    stock: 20,
    color: "cocoa",
    mark: "70%",
  },
  {
    id: 9,
    name: "Sparkling Water",
    detail: "Lime · 330ml",
    price: 2.75,
    category: "Beverages",
    stock: 30,
    color: "mint",
    mark: "LIME",
  },
  {
    id: 10,
    name: "Almond Croissant",
    detail: "Freshly baked",
    price: 4.95,
    category: "Bakery",
    stock: 5,
    color: "peach",
    mark: "AC",
  },
]

type Cart = Record<number, number>

export default function App() {
  const [category, setCategory] = useState("All items")
  const [query, setQuery] = useState("")
  const [cart, setCart] = useState<Cart>({ 2: 1, 3: 2 })
  const [paymentOpen, setPaymentOpen] = useState(false)
  const [paymentMethod, setPaymentMethod] = useState<"card" | "cash">("card")
  const [complete, setComplete] = useState(false)
  const [toast, setToast] = useState("")
  const [mobileCart, setMobileCart] = useState(false)
  const [sidebarOpen, setSidebarOpen] = useState(false)

  const filtered = products.filter(
    (product) =>
      (category === "All items" || product.category === category) &&
      product.name.toLowerCase().includes(query.toLowerCase()),
  )
  const cartItems = products.filter((product) => cart[product.id])
  const itemCount = Object.values(cart).reduce((sum, qty) => sum + qty, 0)
  const subtotal = useMemo(
    () =>
      cartItems.reduce(
        (sum, product) => sum + product.price * cart[product.id],
        0,
      ),
    [cart, cartItems],
  )
  const tax = subtotal * 0.085
  const total = subtotal + tax

  const updateQuantity = (id: number, change: number) => {
    setCart((current) => {
      const next = Math.max(0, (current[id] || 0) + change)
      const updated = { ...current, [id]: next }
      if (!next) delete updated[id]
      return updated
    })
  }

  const notify = (message: string) => {
    setToast(message)
    window.setTimeout(() => setToast(""), 2200)
  }

  const finishSale = () => {
    setComplete(true)
    window.setTimeout(() => {
      setComplete(false)
      setPaymentOpen(false)
      setMobileCart(false)
      setCart({})
    }, 1800)
  }

  return (
    <main className="app-shell">
      <aside className={`sidebar ${sidebarOpen ? "open" : ""}`}>
        <div className="brand">
          <div className="brand-mark">
            <span />
            <span />
            <span />
          </div>
          <span>Counter</span>
          <button
            className="mobile-close"
            onClick={() => setSidebarOpen(false)}
            aria-label="Close menu"
          >
            <Icon name="close" />
          </button>
        </div>
        <nav className="main-nav" aria-label="Primary navigation">
          <button className="active">
            <Icon name="grid" />
            <span>Register</span>
          </button>
          <button
            onClick={() =>
              notify("Orders view is ready for your next workflow")
            }
          >
            <Icon name="orders" />
            <span>Orders</span>
            <b>6</b>
          </button>
          <button onClick={() => notify("Inventory is synced")}>
            <Icon name="box" />
            <span>Inventory</span>
          </button>
          <button onClick={() => notify("Customers view selected")}>
            <Icon name="users" />
            <span>Customers</span>
          </button>
          <button onClick={() => notify("Reports view selected")}>
            <Icon name="chart" />
            <span>Reports</span>
          </button>
        </nav>
        <div className="sidebar-bottom">
          <button onClick={() => notify("Settings opened")}>
            <Icon name="settings" />
            <span>Settings</span>
          </button>
          <div className="profile">
            <div className="avatar">MK</div>
            <div>
              <strong>Maya Kim</strong>
              <small>Store manager</small>
            </div>
            <Icon name="chevron" size={16} />
          </div>
        </div>
      </aside>
      {sidebarOpen && (
        <button
          className="sidebar-scrim"
          aria-label="Close menu"
          onClick={() => setSidebarOpen(false)}
        />
      )}

      <section className="catalog">
        <header className="topbar">
          <button
            className="menu-button"
            onClick={() => setSidebarOpen(true)}
            aria-label="Open menu"
          >
            <Icon name="menu" />
          </button>
          <div>
            <p>Monday, 24 June</p>
            <h1>Good morning, Maya</h1>
          </div>
          <div className="top-actions">
            <span className="status">
              <i /> Register open
            </span>
            <button className="icon-button" aria-label="Notifications">
              <Icon name="bell" />
              <b />
            </button>
          </div>
        </header>

        <div className="catalog-content">
          <div className="search-row">
            <label className="search-box">
              <Icon name="search" />
              <input
                value={query}
                onChange={(event) => setQuery(event.target.value)}
                placeholder="Search products or scan barcode"
              />
              <span className="key">⌘ K</span>
            </label>
            <button
              className="scan-button"
              onClick={() => notify("Scanner is ready")}
            >
              <Icon name="scan" />
              <span>Scan</span>
            </button>
          </div>

          <div className="category-list" aria-label="Product categories">
            {categories.map((item) => (
              <button
                key={item}
                className={category === item ? "active" : ""}
                onClick={() => setCategory(item)}
              >
                {item}
              </button>
            ))}
          </div>

          <div className="section-heading">
            <div>
              <h2>
                {category === "All items" ? "Popular products" : category}
              </h2>
              <p>{filtered.length} products available</p>
            </div>
            <button onClick={() => setCategory("All items")}>
              View all <Icon name="chevron" size={16} />
            </button>
          </div>

          {filtered.length ? (
            <div className="product-grid">
              {filtered.map((product) => (
                <button
                  className="product-card"
                  key={product.id}
                  onClick={() => updateQuantity(product.id, 1)}
                >
                  <div className={`product-art ${product.color}`}>
                    <div className="package">
                      <span>{product.mark}</span>
                      <i />
                    </div>
                    {cart[product.id] && (
                      <b className="in-cart">{cart[product.id]}</b>
                    )}
                  </div>
                  <div className="product-info">
                    <div>
                      <h3>{product.name}</h3>
                      <p>{product.detail}</p>
                    </div>
                    <div className="product-meta">
                      <strong>${product.price.toFixed(2)}</strong>
                      <span>{product.stock} in stock</span>
                    </div>
                  </div>
                </button>
              ))}
            </div>
          ) : (
            <div className="empty-products">
              <Icon name="search" size={28} />
              <h3>No products found</h3>
              <p>Try a different product name or category.</p>
            </div>
          )}
        </div>
      </section>

      <aside className={`cart-panel ${mobileCart ? "mobile-open" : ""}`}>
        <div className="cart-header">
          <div>
            <h2>Current order</h2>
            <p>Order #1048</p>
          </div>
          <button
            onClick={() => setMobileCart(false)}
            className="cart-close"
            aria-label="Close cart"
          >
            <Icon name="close" />
          </button>
          <button className="more-button" aria-label="More order options">
            •••
          </button>
        </div>
        <button
          className="customer-button"
          onClick={() => notify("Customer assigned to this order")}
        >
          <span className="customer-icon">
            <Icon name="users" size={18} />
          </span>
          <span>
            <strong>Add customer</strong>
            <small>Earn points and view history</small>
          </span>
          <Icon name="chevron" size={17} />
        </button>

        <div className="cart-items">
          {cartItems.length ? (
            cartItems.map((product) => (
              <div className="cart-item" key={product.id}>
                <div className={`mini-art ${product.color}`}>
                  <span>{product.mark}</span>
                </div>
                <div className="cart-item-main">
                  <div className="cart-item-title">
                    <div>
                      <h3>{product.name}</h3>
                      <p>{product.detail}</p>
                    </div>
                    <strong>
                      ${(product.price * cart[product.id]).toFixed(2)}
                    </strong>
                  </div>
                  <div className="quantity">
                    <button
                      onClick={() => updateQuantity(product.id, -1)}
                      aria-label={`Remove one ${product.name}`}
                    >
                      <Icon name="minus" size={14} />
                    </button>
                    <span>{cart[product.id]}</span>
                    <button
                      onClick={() => updateQuantity(product.id, 1)}
                      aria-label={`Add one ${product.name}`}
                    >
                      <Icon name="plus" size={14} />
                    </button>
                    <button
                      className="delete"
                      onClick={() =>
                        setCart((current) => {
                          const next = { ...current }
                          delete next[product.id]
                          return next
                        })
                      }
                      aria-label={`Delete ${product.name}`}
                    >
                      <Icon name="trash" size={16} />
                    </button>
                  </div>
                </div>
              </div>
            ))
          ) : (
            <div className="empty-cart">
              <div>
                <Icon name="orders" size={28} />
              </div>
              <h3>Your order is empty</h3>
              <p>Select a product to start a new sale.</p>
            </div>
          )}
        </div>

        <div className="cart-footer">
          <div className="order-tools">
            <button onClick={() => notify("Order held successfully")}>
              <Icon name="pause" size={17} /> Hold
            </button>
            <button onClick={() => notify("Discount options opened")}>
              <Icon name="tag" size={17} /> Discount
            </button>
            <button onClick={() => setCart({})}>
              <Icon name="trash" size={17} /> Clear
            </button>
          </div>
          <div className="totals">
            <div>
              <span>Subtotal</span>
              <strong>${subtotal.toFixed(2)}</strong>
            </div>
            <div>
              <span>
                Tax <small>8.5%</small>
              </span>
              <strong>${tax.toFixed(2)}</strong>
            </div>
            <div className="total">
              <span>Total</span>
              <strong>${total.toFixed(2)}</strong>
            </div>
          </div>
          <button
            className="checkout-button"
            disabled={!itemCount}
            onClick={() => setPaymentOpen(true)}
          >
            <span>Charge</span>
            <strong>${total.toFixed(2)}</strong>
          </button>
          <p className="item-summary">
            {itemCount} {itemCount === 1 ? "item" : "items"} in order
          </p>
        </div>
      </aside>

      <button
        className="mobile-cart-button"
        onClick={() => setMobileCart(true)}
      >
        <span>
          <Icon name="orders" size={19} /> {itemCount} items
        </span>
        <strong>${total.toFixed(2)}</strong>
      </button>

      {paymentOpen && (
        <div
          className="modal-backdrop"
          onMouseDown={() => !complete && setPaymentOpen(false)}
        >
          <section
            className="payment-modal"
            onMouseDown={(event) => event.stopPropagation()}
            role="dialog"
            aria-modal="true"
            aria-labelledby="payment-title"
          >
            {complete ? (
              <div className="payment-success">
                <div className="success-mark">
                  <Icon name="check" size={34} />
                </div>
                <h2>Payment complete</h2>
                <p>Order #1048 has been paid successfully.</p>
              </div>
            ) : (
              <>
                <div className="modal-header">
                  <div>
                    <p>Order #1048</p>
                    <h2 id="payment-title">Take payment</h2>
                  </div>
                  <button
                    onClick={() => setPaymentOpen(false)}
                    aria-label="Close payment"
                  >
                    <Icon name="close" />
                  </button>
                </div>
                <div className="amount-due">
                  <span>Amount due</span>
                  <strong>${total.toFixed(2)}</strong>
                </div>
                <p className="method-label">Payment method</p>
                <div className="payment-methods">
                  <button
                    className={paymentMethod === "card" ? "active" : ""}
                    onClick={() => setPaymentMethod("card")}
                  >
                    <Icon name="card" size={24} />
                    <span>
                      <strong>Card</strong>
                      <small>Tap, insert, or swipe</small>
                    </span>
                    {paymentMethod === "card" && (
                      <i>
                        <Icon name="check" size={13} />
                      </i>
                    )}
                  </button>
                  <button
                    className={paymentMethod === "cash" ? "active" : ""}
                    onClick={() => setPaymentMethod("cash")}
                  >
                    <Icon name="cash" size={24} />
                    <span>
                      <strong>Cash</strong>
                      <small>Record a cash payment</small>
                    </span>
                    {paymentMethod === "cash" && (
                      <i>
                        <Icon name="check" size={13} />
                      </i>
                    )}
                  </button>
                </div>
                <button className="pay-button" onClick={finishSale}>
                  {paymentMethod === "card"
                    ? "Confirm card payment"
                    : "Confirm cash payment"}{" "}
                  · ${total.toFixed(2)}
                </button>
              </>
            )}
          </section>
        </div>
      )}
      {toast && (
        <div className="toast">
          <Icon name="check" size={16} />
          {toast}
        </div>
      )}
    </main>
  )
}
