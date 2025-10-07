# Martin Autofulfill

**Automated Shopify-to-Shopee Order Fulfillment System**

A production-ready Python application that streamlines e-commerce operations by automating order fulfillment workflows between Shopify and Shopee. Built with a clean Streamlit interface, this system enables efficient order management, product mapping, and automated data synchronization.

---

## 🎯 Project Overview

Martin Autofulfill bridges the gap between Shopify order management and Shopee purchasing workflows. The application automatically fetches unfulfilled Shopify orders, maps products to Shopee URLs, formats customer shipping data, and manages the complete fulfillment lifecycle with comprehensive logging and status tracking.

**Key Use Case**: Dropshipping operations where Shopify serves as the customer-facing storefront while Shopee is used as the supplier/fulfillment source.

---

## ✨ Features

### Implemented ✅

- **Shopify API Integration**: Real-time fetching of unfulfilled orders with automatic filtering
- **Order Management Dashboard**: Multi-tab interface for pending, processed, and ignored orders
- **Product Mapping System**: Link Shopify products to Shopee URLs with keyword-based matching
- **Smart Address Formatting**: One-click copy of customer shipping data formatted for Shopee checkout
- **Fulfillment Automation**: Update Shopify orders with tracking codes and automatic customer notifications
- **Purchase Status Tracking**: Mark orders as "Purchased/Not Purchased" with persistent state management
- **CPF Extraction**: Automatic extraction and display of Brazilian tax ID (CPF) from Shopify/Yampi orders
- **Comprehensive Logging**: CSV-based operation logs and file-based audit trails
- **Dark Mode Support**: Fully responsive UI with automatic light/dark theme adaptation
- **Error Handling**: Robust validation and error recovery mechanisms

### In Development 🔄

- **Shopee Checkout Automation**: Playwright-based browser automation for automatic form filling and purchasing

---

## 🛠️ Technology Stack

| Category | Technology | Purpose |
|----------|-----------|---------|
| **Frontend** | Streamlit | Interactive web-based UI for order management |
| **Backend** | Python 3.x | Core application logic and API integration |
| **HTTP Client** | requests | Shopify REST API communication |
| **Browser Automation** | Playwright | Shopee form filling automation (planned) |
| **API Integration** | Shopify Admin API v2023-10 | Order fetching and fulfillment updates |
| **Data Storage** | JSON | Local persistence for orders and product mappings |
| **Logging** | CSV + Python logging | Operation audit trails |

---

## 📦 Installation

### Prerequisites

- Python 3.8 or higher
- pip package manager
- Shopify store with Admin API access
- Active Shopify API token with `read_orders` and `write_fulfillments` permissions

### Setup Instructions

```bash
# Clone the repository
git clone https://github.com/abrahao-dev/martin-autofulfill.git
cd martin-autofulfill

# Create and configure environment variables
cp .env.example .env
# Edit .env with your Shopify credentials:
# SHOPIFY_STORE=your-store-name
# SHOPIFY_API_TOKEN=your-admin-api-token
# SHOPIFY_API_VERSION=2023-10

# Install Python dependencies
pip install -r requirements.txt

# (Optional) Install Playwright browsers for automation features
python -m playwright install
```

### Environment Configuration

Create a `.env` file in the project root with the following variables:

```env
SHOPIFY_STORE=your-store-name.myshopify.com
SHOPIFY_API_TOKEN=shpat_xxxxxxxxxxxxxxxxxxxxx
SHOPIFY_API_VERSION=2023-10
```

---

## 🚀 Running the Application

```bash
# Start the Streamlit web interface
streamlit run main_ui.py
```

The application will launch in your default browser at `http://localhost:8501`

---

## 📁 Project Structure

```
martin-autofulfill/
├── data/                      # Order and product data storage
│   ├── pedidos_pendentes.json    # Pending orders
│   ├── pedidos_processados.json  # Processed orders
│   ├── pedidos_ignorados.json    # Ignored orders
│   └── produtos_shopee.json      # Product mappings
├── logs/                      # Application logs
│   ├── operacoes.csv             # CSV operation audit log
│   └── martin_autofulfill.log    # Detailed text logs
├── get_shopify_orders.py      # Shopify order fetching module
├── get_shopify_locations.py   # Shopify inventory location manager
├── fulfill_shopify_order.py   # Shopify fulfillment API wrapper
├── shopify_fulfillment.py     # Core fulfillment logic
├── main_ui.py                 # Main Streamlit UI application
├── processamento_pedidos.py   # Order state management
├── produtos_ui.py             # Product mapping UI
├── shopee_produtos.py         # Product database manager
├── utils.py                   # Utility functions and validators
├── logger.py                  # Logging infrastructure
├── requirements.txt           # Python dependencies
├── .env                       # Environment configuration (not versioned)
└── README.md                  # This file
```

---

## 🔄 Workflow

1. **Fetch Orders**: Click "Update Orders" to pull unfulfilled orders from Shopify API
2. **Review Orders**: Browse pending orders in the dashboard with full customer and product details
3. **Map Products**: Associate Shopify products with Shopee URLs in the Products tab
4. **Copy Shipping Data**: Use the "Copy Shopee Address" button to get formatted customer data
5. **Purchase on Shopee**: Manually or automatically complete the Shopee checkout
6. **Mark as Fulfilled**: Enter tracking code and mark order as processed
7. **Auto-Notification**: System automatically notifies customer via Shopify email

---

## 📊 Development Roadmap

### Phase 1: Foundation ✅ (Completed)
- [x] Basic UI with mock data
- [x] Shopify API integration
- [x] Order state management (pending/processed/ignored)
- [x] Logging and audit trails

### Phase 2: Enhanced Features ✅ (Completed)
- [x] Product mapping system
- [x] Address formatting for Shopee
- [x] CPF extraction and display
- [x] Purchase status tracking
- [x] Dark mode support

### Phase 3: Automation 🔄 (In Progress)
- [ ] Playwright integration for Shopee
- [ ] Automatic form filling
- [ ] Product variant selection
- [ ] Checkout flow automation
- [ ] Retry mechanisms and error handling

### Phase 4: Future Enhancements 📋 (Planned)
- [ ] Analytics dashboard with order metrics
- [ ] Payment automation for Shopee
- [ ] Multi-account Shopee support
- [ ] Inventory synchronization
- [ ] Integration with other marketplaces

---

## 🧪 Testing

```bash
# Test Shopify API connection
python get_shopify_orders.py

# Test location retrieval
python get_shopify_locations.py

# Test fulfillment creation (requires order ID, line item ID, and tracking number)
python fulfill_shopify_order.py <order_id> <line_item_id> <tracking_number>
```

---

## 🤝 Contributing

This is a professional portfolio project demonstrating full-stack Shopify development skills. While not currently accepting contributions, the codebase showcases:

- Clean Python architecture with modular design
- RESTful API integration patterns
- State management and data persistence
- Production-ready error handling
- Professional logging practices
- Modern UI/UX with Streamlit

---

## 📄 License

This project is licensed under the terms specified in the LICENSE file.

---

## 👤 Author

**Matheus Abrahão**  
Full-Stack Developer | Shopify Specialist  
GitHub: [@abrahao-dev](https://github.com/abrahao-dev)

---

## 📧 Contact

For technical inquiries regarding this project, please open an issue on GitHub.

---

**Note**: This application is designed for educational and professional portfolio purposes, demonstrating proficiency in Shopify API development, Python backend systems, and modern web UI frameworks.
