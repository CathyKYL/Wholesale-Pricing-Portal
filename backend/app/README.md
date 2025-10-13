# Wholesale Pricing Portal - Phase 2: Database Layer

## Overview
This phase implements the PostgreSQL database layer with SQLAlchemy ORM, providing a solid foundation for storing and managing catalog data from Excel files.

## ✅ Completed Components

### 1. Database Models (`models.py`)
- **CatalogRow** ORM model with exact 1:1 mapping to Excel columns
- Uses `Numeric(12, 2)` for currency (no floats)
- Proper constraints and nullable fields
- Clear docstrings for all fields

### 2. Database Bootstrap (`db.py`)
- Reads `DATABASE_URL` from `.env` (never hardcoded)
- Provides `init_db()` for idempotent table creation
- Session factory (`SessionLocal`) for database operations
- Dependency injection support for FastAPI

### 3. Excel Data Loader (`load_excel.py`)
- Reads Excel file from `EXCEL_PATH` environment variable
- Cleans currency strings (£44.95 → Decimal)
- Handles missing/invalid data gracefully (N/A, NaN → None)
- Prevents duplicates based on title + author
- Bulk insert with single commit for performance

### 4. Smoke Test (`smoke_test.py`)
- End-to-end validation of entire setup
- Tests environment configuration
- Validates database connection
- Loads and verifies Excel data
- Provides clear pass/fail feedback

## 📊 Database Schema

### Table: `catalog_rows` (Normalized Schema)

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| id | Integer | No | Primary key (auto-increment) |
| asin | String(32) | **No** | Amazon ASIN (UK or US) |
| marketplace | String(2) | **No** | Marketplace ('US' or 'UK') |
| title | String(512) | **No** | Book title (required) |
| author | String(512) | Yes | Author name |
| available_stock | Integer | Yes | Units in stock |
| rrp | Numeric(12,2) | Yes | Recommended Retail Price |
| our_price | Numeric(12,2) | Yes | Our selling price |

**Important:** Each Excel row with both UK and US ASINs creates **TWO** database rows:
- One with `marketplace='UK'` and the UK ASIN
- One with `marketplace='US'` and the US ASIN

**Unique Constraint:** `(asin, marketplace)` - same ASIN cannot appear twice in the same marketplace

## 🚀 Usage

### Initial Setup
```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Configure .env file
DATABASE_URL=postgresql://postgres:password@localhost:5432/wholesale_portal
EXCEL_PATH=C:\path\to\Data.xlsx

# 3. Run smoke test (creates tables + loads data)
cd backend/app
python smoke_test.py
```

### Load Excel Data
```bash
cd backend/app
python load_excel.py
```

### Use in Your Code
```python
from db import init_db, SessionLocal
from models import CatalogRow

# Initialize database
init_db()

# Query data
with SessionLocal() as session:
    books = session.query(CatalogRow).filter(
        CatalogRow.rrp > 50
    ).all()
    
    for book in books:
        print(f"{book.title}: £{book.our_price}")
```

## 📋 Test Results

**Latest Smoke Test Results:**
- ✅ Environment Configuration: PASS
- ✅ Database Initialization: PASS  
- ✅ Excel Data Loading: PASS (38 rows from 25 Excel rows)
- ✅ Data Query & Verification: PASS

**Database Statistics:**
- Total Items: 38 (25 Excel rows → 38 database rows)
- UK Marketplace Items: 16
- US Marketplace Items: 22
- Average RRP: £55.31
- Average Our Price: £23.94

## 🎯 Next Steps (Phase 3)

1. **Build FastAPI Endpoints:**
   - `GET /catalog` - List all catalog items
   - `GET /catalog/{id}` - Get single item
   - `POST /catalog` - Add new item
   - `PUT /catalog/{id}` - Update item
   - `DELETE /catalog/{id}` - Delete item

2. **Add Search & Filtering:**
   - Search by title, author, ASIN
   - Filter by price range
   - Sort by various fields

3. **Integrate Keepa API (Phase 4):**
   - Fetch real-time Amazon pricing
   - Compare with our prices
   - Calculate profit margins

## 📝 Notes

- All currency operations use `Decimal` for precision
- Database operations are idempotent (safe to re-run)
- Excel loader updates existing rows instead of duplicating
- All secrets stored in `.env` (never committed to git)
- Comprehensive inline comments for non-technical readers

## 🔒 Security

- ✅ `.env` file excluded from git (in `.gitignore`)
- ✅ Database passwords never hardcoded
- ✅ API keys properly secured
- ✅ SQL injection protected by SQLAlchemy ORM

