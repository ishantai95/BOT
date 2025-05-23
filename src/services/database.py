import pandas as pd
from sqlalchemy import create_engine, text, MetaData
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from ..models.chat import CustomerStats

class DatabaseService:
    def __init__(self, db_url: str):
        print(f"Initializing database with URL: {db_url}")  # Debug log
        # Convert the regular PostgreSQL URL to async
        self.db_url = db_url.replace('postgresql://', 'postgresql+asyncpg://')
        self.engine = create_async_engine(
            self.db_url,
            poolclass=StaticPool
        )
        self.async_session = sessionmaker(
            self.engine, 
            class_=AsyncSession, 
            expire_on_commit=False
        )
        self.metadata = MetaData()
    
    async def check_customer_exists(self, customer_name: str) -> bool:
        print(f"Checking if customer exists: {customer_name}")  # Debug log
        async with self.async_session() as session:
            result = await session.execute(
                text("SELECT COUNT(*) FROM invoice WHERE \"customerName\" = :name"),
                {"name": customer_name}
            )
            count = result.scalar_one()
            print(f"Found {count} invoices for customer")  # Debug log
            return count > 0
    
    async def get_customer_stats(self, customer_name: str) -> CustomerStats:
        async with self.async_session() as session:
            result = await session.execute(
                text("""
                SELECT 
                    COUNT(*) as total_invoice,
                    SUM("totalAmount") as total_amount,
                    MIN("issueDate") as first_invoice,
                    MAX("issueDate") as last_invoice,
                    COUNT(DISTINCT status) as status_types,
                    STRING_AGG(DISTINCT status, ', ') as statuses,
                    STRING_AGG(DISTINCT currency, ', ') as currencies
                FROM invoice 
                WHERE "customerName" = :name
                """),
                {"name": customer_name}
            )
            row = result.fetchone()
            
            return CustomerStats(
                total_invoice=row[0],
                total_amount=float(row[1]) if row[1] else 0,
                first_invoice=str(row[2]),
                last_invoice=str(row[3]),
                statuses=row[5],
                currencies=row[6]
            )

    async def execute_query(self, sql: str) -> pd.DataFrame:
        async with self.async_session() as session:
            result = await session.execute(text(sql))
            rows = result.fetchall()
            columns = result.keys()
            
            df = pd.DataFrame(rows, columns=columns)
            
            # Convert UUID objects to strings
            for col in df.columns:
                if df[col].dtype == 'object':
                    if len(df) > 0 and str(df[col].iloc[0]).startswith('urn:uuid:'):
                        df[col] = df[col].astype(str)
            
            return df
