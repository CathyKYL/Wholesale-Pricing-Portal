"""
Export Database to SQL File
----------------------------
Export your local PostgreSQL database to a SQL file for Supabase import.
"""

import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, inspect, text
from datetime import datetime

load_dotenv()

# Get current local database URL
DATABASE_URL = os.getenv("DATABASE_URL")

print("\n" + "=" * 100)
print("📦 EXPORTING LOCAL DATABASE FOR SUPABASE MIGRATION")
print("=" * 100)

print(f"\n📍 Source: {DATABASE_URL.split('@')[1] if '@' in DATABASE_URL else DATABASE_URL}")

# Connect to database
engine = create_engine(DATABASE_URL)

# Output file
output_file = "wholesale_portal_backup.sql"

print(f"📄 Output file: {output_file}")

with open(output_file, 'w', encoding='utf-8') as f:
    # Header
    f.write("-- Wholesale Portal Database Export\n")
    f.write(f"-- Exported: {datetime.now()}\n")
    f.write(f"-- Source: Local PostgreSQL\n")
    f.write(f"-- Destination: Supabase\n\n")
    
    with engine.connect() as conn:
        # Get all schemas
        schemas = conn.execute(text("""
            SELECT schema_name 
            FROM information_schema.schemata 
            WHERE schema_name NOT IN ('information_schema', 'pg_catalog', 'pg_toast')
            ORDER BY schema_name
        """)).fetchall()
        
        print(f"\n📂 Found {len(schemas)} schemas to export:")
        for schema in schemas:
            print(f"   • {schema[0]}")
        
        # Create schemas
        f.write("-- ==================== SCHEMAS ====================\n\n")
        for schema in schemas:
            schema_name = schema[0]
            if schema_name != 'public':  # public already exists
                f.write(f"CREATE SCHEMA IF NOT EXISTS {schema_name};\n")
        f.write("\n")
        
        # Get all tables from all schemas
        inspector = inspect(engine)
        total_tables = 0
        total_rows = 0
        
        for schema in schemas:
            schema_name = schema[0]
            tables = inspector.get_table_names(schema=schema_name)
            
            if not tables:
                continue
            
            f.write(f"\n-- ==================== SCHEMA: {schema_name} ====================\n\n")
            
            for table_name in tables:
                total_tables += 1
                full_table = f"{schema_name}.{table_name}"
                
                # Get row count
                row_count = conn.execute(text(f"SELECT COUNT(*) FROM {full_table}")).fetchone()[0]
                total_rows += row_count
                
                print(f"\n📊 Exporting: {full_table} ({row_count:,} rows)")
                
                # Get table structure
                f.write(f"-- Table: {full_table}\n")
                f.write(f"-- Rows: {row_count:,}\n\n")
                
                # Get CREATE TABLE statement (simplified)
                columns_info = inspector.get_columns(table_name, schema=schema_name)
                pk_constraint = inspector.get_pk_constraint(table_name, schema=schema_name)
                unique_constraints = inspector.get_unique_constraints(table_name, schema=schema_name)
                indexes = inspector.get_indexes(table_name, schema=schema_name)
                
                # Build CREATE TABLE
                f.write(f"CREATE TABLE IF NOT EXISTS {full_table} (\n")
                
                col_defs = []
                for col in columns_info:
                    col_def = f"    {col['name']} {col['type']}"
                    if not col['nullable']:
                        col_def += " NOT NULL"
                    if col.get('default'):
                        col_def += f" DEFAULT {col['default']}"
                    col_defs.append(col_def)
                
                # Add primary key
                if pk_constraint and pk_constraint['constrained_columns']:
                    pk_cols = ', '.join(pk_constraint['constrained_columns'])
                    col_defs.append(f"    PRIMARY KEY ({pk_cols})")
                
                f.write(',\n'.join(col_defs))
                f.write("\n);\n\n")
                
                # Add unique constraints
                for uc in unique_constraints:
                    cols = ', '.join(uc['column_names'])
                    f.write(f"ALTER TABLE {full_table} ADD CONSTRAINT {uc['name']} UNIQUE ({cols});\n")
                
                if unique_constraints:
                    f.write("\n")
                
                # Export data
                if row_count > 0:
                    f.write(f"-- Data for {full_table}\n")
                    
                    # Get all data
                    result = conn.execute(text(f"SELECT * FROM {full_table}"))
                    rows = result.fetchall()
                    columns = result.keys()
                    
                    # Build INSERT statements (batch)
                    batch_size = 100
                    for i in range(0, len(rows), batch_size):
                        batch = rows[i:i+batch_size]
                        
                        f.write(f"INSERT INTO {full_table} ({', '.join(columns)}) VALUES\n")
                        
                        value_strings = []
                        for row in batch:
                            values = []
                            for val in row:
                                if val is None:
                                    values.append('NULL')
                                elif isinstance(val, str):
                                    # Escape single quotes
                                    escaped = val.replace("'", "''")
                                    values.append(f"'{escaped}'")
                                elif isinstance(val, (int, float)):
                                    values.append(str(val))
                                elif isinstance(val, datetime):
                                    values.append(f"'{val.isoformat()}'")
                                else:
                                    values.append(f"'{str(val)}'")
                            value_strings.append(f"({', '.join(values)})")
                        
                        f.write(',\n'.join(value_strings))
                        f.write('\nON CONFLICT DO NOTHING;\n\n')
                
                # Create indexes
                for idx in indexes:
                    if not idx.get('unique'):  # Unique indexes already handled
                        cols = ', '.join(idx['column_names'])
                        idx_name = idx['name']
                        f.write(f"CREATE INDEX IF NOT EXISTS {idx_name} ON {full_table} ({cols});\n")
                
                if indexes:
                    f.write("\n")

print("\n" + "=" * 100)
print("✅ EXPORT COMPLETE!")
print("=" * 100)
print(f"\n📊 Summary:")
print(f"   • Schemas exported: {len(schemas)}")
print(f"   • Tables exported: {total_tables}")
print(f"   • Total rows: {total_rows:,}")
print(f"   • Output file: {output_file}")
print(f"   • File size: {os.path.getsize(output_file) / 1024:.1f} KB")

print(f"\n🚀 Next Steps:")
print(f"   1. Create Supabase project at https://supabase.com")
print(f"   2. Get connection string from Settings → Database")
print(f"   3. Import using:")
print(f'      psql "YOUR_SUPABASE_URL" < {output_file}')
print(f"\n📖 See MIGRATE_TO_SUPABASE.md for detailed instructions")
print("=" * 100 + "\n")





