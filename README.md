# SmartInventory — Inventory Management System

> **AI-Powered Inventory Tracking, Shortage Analysis & Restocking Engine**

SmartInventory is a Streamlit-based inventory management system designed for electronics manufacturing and procurement teams. It uses LLM-powered column mapping (Groq / Gemini) to automatically align BOM files with your stock database — no manual column matching required.

---

## ✨ Key Features

| Feature | Description |
|---|---|
| **📦 Stock Management** | Live database editor with search, inline editing, and critical threshold alerts |
| **🚚 Shortage Analysis** | Upload a BOM file → system auto-detects columns via LLM → generates shortage report |
| **📥 Restocking** | Upload incoming shipment files → quantities auto-merge into inventory |
| **🤖 AI Column Mapping** | Groq (primary) + Gemini (fallback) automatically maps column names across different file formats |
| **🌐 Multilingual UI** | Full Arabic / Turkish / English support with instant language switching |
| **🗃️ SQLite Backend** | Persistent inventory with dynamic schema evolution |

---

## 🌐 Multilingual Support

SmartInventory supports **three languages** out of the box:

| Language | Code | Direction |
|---|---|---|
| Türkçe (Turkish) | `tr` | LTR |
| English | `en` | LTR |
| العربية (Arabic) | `ar` | RTL |

### How to Switch Languages

1. Open the **⚙️ Settings** tab
2. Select your preferred language from the **🌐 Language** dropdown
3. The entire UI updates instantly — tabs, buttons, labels, tooltips, and messages

> **Note:** Arabic activates RTL (right-to-left) layout. Data tables remain LTR for readability.

---

## 🚀 Installation

### Prerequisites

- Python 3.10+
- pip

### Setup

```bash
# Clone the repository
git clone https://github.com/SAMER2244/Smartinventory
cd smartinventory

# Install dependencies
pip install -r requirements.txt

# Configure API keys
cp .env.example .env
# Edit .env with your Groq and/or Gemini API keys
```

### Run

```bash
streamlit run app.py
```

Or use the provided launcher scripts:

- **Linux/macOS:** `./run_app.sh`
- **Windows:** `Start_App.bat`

---

## ⚙️ Configuration

Create a `.env` file in the project root:

```env
GROQ_API_KEY=gsk_your_groq_key_here
GEMINI_API_KEY=your_gemini_key_here
```

Both keys are optional — the system will use whichever is available, with Groq as primary and Gemini as fallback.

You can also set API keys directly from the **Settings** tab in the UI.

---

## 📁 Project Structure

```
smartinventory/
├── app.py                  # Main Streamlit application
├── core/
│   ├── __init__.py
│   ├── config.py           # API client initialization & model selection
│   ├── database.py         # SQLite schema & connection management
│   ├── i18n.py             # Translation helper (t() function)
│   ├── llm.py              # LLM-powered column mapping (Groq + Gemini)
│   ├── processor.py        # Excel processing, shortage calc, restocking
│   └── translations.py     # All UI strings in AR / TR / EN
├── data/                   # Initial inventory files for migration
├── outputs/                # Generated reports
├── logs/                   # Application logs
├── requirements.txt
├── .env                    # API keys (git-ignored)
├── .gitignore
└── README.md
```

---

## 🔧 Adding a New Language

1. Open `core/translations.py`
2. Add a new language code to every translation entry:
   ```python
   "page_title": {
       "tr": "Envanter Yönetim Sistemi",
       "en": "Inventory Management System",
       "ar": "نظام إدارة المخزون",
       "de": "Bestandsverwaltungssystem",  # ← new
   },
   ```
3. Add the display label in `core/i18n.py`:
   ```python
   LANG_OPTIONS = {
       "Türkçe": "tr",
       "English": "en",
       "العربية": "ar",
       "Deutsch": "de",  # ← new
   }
   ```
4. Restart the app — the new language appears in the Settings dropdown.

---

## 📄 License

This project is open source. See [LICENSE](LICENSE) for details.

---

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request
