import os
import json
import re
from typing import Dict, Any, List, Optional
from uuid import UUID

import pandas as pd
from langchain.memory import ConversationBufferWindowMemory
from langchain.schema import HumanMessage, AIMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.prompts import PromptTemplate
from langchain.schema.runnable import RunnablePassthrough

from ..models.chat import ChatSession, ChatResponse, CustomerStats
from ..utils.templates import SQL_TEMPLATE, RESPONSE_TEMPLATE, SCHEMA_CONTEXT
from .database import DatabaseService

class ChatbotService:
    def __init__(self, db_service: DatabaseService, api_key: str):
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-2.0-flash-exp",
            google_api_key=api_key,
            temperature=0.1
        )
        self.db = db_service
        self.sessions: Dict[str, ChatSession] = {}  # Store multiple sessions
        self.schema_context = SCHEMA_CONTEXT
        
        self.sql_chain = self._create_sql_chain()
        self.response_chain = self._create_response_chain()
    
    def _create_sql_chain(self):
        prompt = PromptTemplate(
            input_variables=["schema", "customer_name", "chat_history", "query"],
            template=SQL_TEMPLATE
        )
        return prompt | self.llm
    
    def _create_response_chain(self):
        prompt = PromptTemplate(
            input_variables=["query", "chat_history", "data"],
            template=RESPONSE_TEMPLATE
        )
        return prompt | self.llm
    
    async def authenticate(self, customer_name: str) -> bool:
        result = await self.db.check_customer_exists(customer_name)
        
        if result:
            if customer_name not in self.sessions:
                memory = ConversationBufferWindowMemory(
                    k=10,
                    return_messages=True,
                    memory_key="chat_history"
                )
                self.sessions[customer_name] = ChatSession(
                    customer_name=customer_name, 
                    memory=memory
                )
            self.session = self.sessions[customer_name]  # Set current session
            await self._update_context()
            return True
        return False
    
    async def _update_context(self) -> CustomerStats:
        customer_data = await self.db.get_customer_stats(self.session.customer_name)
        
        self.session.context = customer_data.dict()
        return customer_data
    
    def generate_suggestions(self) -> List[str]:
        if not self.session:
            return []
            
        ctx = self.session.context
        suggestions = [
            "Show me all my invoices",
            "What's my total outstanding amount?",
            f"Show invoices in {ctx['currencies'].split(',')[0].strip() if ctx['currencies'] else 'USD'}"
        ]
        
        if ctx['total_invoice'] > 5:
            suggestions.append("Show my last 5 invoices")
        
        if 'pending' in ctx['statuses'].lower():
            suggestions.append("Show all pending invoices")
        
        if ctx['total_invoice'] > 1:
            suggestions.extend([
                "What's my highest invoice amount?",
                "Show invoices from last month"
            ])
        
        recent_topics = self._get_recent_topics()
        if recent_topics:
            suggestions.append(f"Tell me more about {recent_topics[0]}")
        
        return suggestions[:6]
    
    def _get_recent_topics(self) -> List[str]:
        if not self.session or not self.session.memory.chat_memory.messages:
            return []
        
        topics = []
        for msg in self.session.memory.chat_memory.messages[-4:]:
            if isinstance(msg, HumanMessage):
                if "invoice" in msg.content.lower():
                    if "pending" in msg.content.lower():
                        topics.append("pending invoices")
                    elif "paid" in msg.content.lower():
                        topics.append("paid invoices")
        
        return list(set(topics))
    
    def _generate_sql(self, query: str) -> str:
        chat_history = self.session.memory.buffer_as_str
        
        response = self.sql_chain.invoke({
            "schema": self.schema_context,
            "customer_name": self.session.customer_name,
            "chat_history": chat_history,
            "query": query
        })
        
        sql = response.content.strip()
        sql = re.sub(r'```sql\s*|\s*```', '', sql).strip()
        
        if "customerName" not in sql:
            where_clause = f'"customerName" = \'{self.session.customer_name}\''
            if "WHERE" in sql.upper():
                sql = sql.replace("WHERE", f"WHERE {where_clause} AND", 1)
            else:
                sql = re.sub(r'(FROM\s+invoice)', r'\1 WHERE ' + where_clause, sql, flags=re.IGNORECASE)
        
        return sql
    
    async def _format_response(self, df: pd.DataFrame, query: str) -> str:
        if df.empty:
            return "No data found for your query."
        
        chat_history = self.session.memory.buffer_as_str
        data_dict = df.to_dict('records')[:10]
        
        response = self.response_chain.invoke({
            "query": query,
            "chat_history": chat_history,
            "data": json.dumps(data_dict, default=str)
        })
        
        return response.content.strip()
    
    async def chat(self, user_input: str) -> ChatResponse:
        if not self.session:
            return ChatResponse(
                response="Not authenticated",
                error="User not authenticated"
            )
        
        try:
            sql = self._generate_sql(user_input)
            df = await self.db.execute_query(sql)
            response = await self._format_response(df, user_input)
            
            # Save to the correct session's memory
            self.session.memory.save_context(
                {"input": user_input},
                {"output": response}
            )
            
            return ChatResponse(
                response=response,
                sql=sql,
                row_count=len(df),
                data=df.to_dict('records'),
                suggestions=self.generate_suggestions()
            )
            
        except Exception as e:
            error_msg = f"I couldn't process that query. Please try rephrasing."
            
            # Save error to memory too
            self.session.memory.save_context(
                {"input": user_input},
                {"output": error_msg}
            )
            
            return ChatResponse(
                response=error_msg,
                error=str(e),
                suggestions=self.generate_suggestions()
            )
    
    def get_conversation_history(self) -> List[Dict[str, str]]:
        if not self.session:
            return []
        
        history = []
        for msg in self.session.memory.chat_memory.messages:
            if isinstance(msg, HumanMessage):
                history.append({"role": "user", "content": msg.content})
            elif isinstance(msg, AIMessage):
                history.append({"role": "assistant", "content": msg.content})
        
        return history
    
    def clear_memory(self):
        if self.session:
            self.session.memory.clear()
