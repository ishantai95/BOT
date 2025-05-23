SQL_TEMPLATE = """
Convert this natural language query to SQL. 
Context: {schema}
Customer: {customer_name}

Chat History:
{chat_history}

Rules:
1. ALWAYS filter by customerName = '{customer_name}'
2. Use proper PostgreSQL syntax with quoted column names
3. Return ONLY the SQL query, no explanations
4. For date operations use PostgreSQL date functions

Query: {query}
SQL:"""

RESPONSE_TEMPLATE = """
Format this data as a natural language response to: "{query}"

Chat History:
{chat_history}

Data: {data}

Rules:
1. Be concise and informative
2. Highlight key information
3. Format numbers and dates nicely
4. Max 3-4 sentences
5. Consider the conversation context

Response:"""

SCHEMA_CONTEXT = """
Table: invoice
Columns: invoiceId (UUID), invoiceNumber, issueDate, dueDate, status, 
currency, customerName, customerEmail, customerAddress, customerPhone, 
items, subTotal, tax, discount, totalAmount
"""
