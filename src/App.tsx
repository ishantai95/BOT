import React, { useState, useRef, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { FiSend, FiUser } from 'react-icons/fi';
import axios from 'axios';
import { Message, ChatResponse, AuthResponse } from './types';

const API_URL = 'http://localhost:8000/api';
const API_KEY = 'ishant';

function App() {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [customerName, setCustomerName] = useState('');
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [suggestions, setSuggestions] = useState<string[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleAuth = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    try {
      const response = await axios.post<AuthResponse>(
        `${API_URL}/authenticate`,
        { customer_name: customerName, message: '' },
        { headers: { 'X-API-Key': API_KEY } }
      );
      if (response.data.success) {
        setIsAuthenticated(true);
        setSuggestions(response.data.suggestions || []);
        setMessages([{ role: 'assistant', content: response.data.message }]);
      }
    } catch (error) {
      console.error('Authentication error:', error);
      setMessages([{ role: 'assistant', content: 'Authentication failed. Please try again.' }]);
    }
    setIsLoading(false);
  };

  const handleSend = async () => {
    if (!input.trim()) return;

    const userMessage = input.trim();
    setInput('');
    setMessages(prev => [...prev, { role: 'user', content: userMessage }]);
    setIsLoading(true);

    try {
      const response = await axios.post<ChatResponse>(
        `${API_URL}/chat`,
        { customer_name: customerName, message: userMessage },
        { headers: { 'X-API-Key': API_KEY } }
      );

      setMessages(prev => [...prev, { role: 'assistant', content: response.data.response }]);
      setSuggestions(response.data.suggestions || []);
    } catch (error) {
      console.error('Chat error:', error);
      setMessages(prev => [...prev, { role: 'assistant', content: 'Sorry, I encountered an error. Please try again.' }]);
    }
    setIsLoading(false);
  };

  if (!isAuthenticated) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-50 to-white flex items-center justify-center p-4">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="bg-white rounded-2xl shadow-lg p-8 w-full max-w-md"
        >
          <div className="flex items-center justify-center mb-8">
            <div className="bg-blue-100 p-4 rounded-full">
              <FiUser className="w-8 h-8 text-blue-600" />
            </div>
          </div>
          <h1 className="text-2xl font-semibold text-center mb-6 text-gray-800">
            Invoice Assistant
          </h1>
          <form onSubmit={handleAuth} className="space-y-4">
            <div>
              <label htmlFor="customerName" className="block text-sm font-medium text-gray-700 mb-1">
                Customer Name
              </label>
              <input
                id="customerName"
                type="text"
                value={customerName}
                onChange={(e) => setCustomerName(e.target.value)}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none transition-all"
                placeholder="Enter your name"
                required
              />
            </div>
            <button
              type="submit"
              disabled={isLoading}
              className="w-full bg-blue-600 text-white py-2 rounded-lg hover:bg-blue-700 transition-colors disabled:bg-blue-400"
            >
              {isLoading ? 'Connecting...' : 'Start Chat'}
            </button>
          </form>
        </motion.div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-white flex flex-col">
      <header className="bg-white shadow-sm p-4">
        <div className="max-w-4xl mx-auto flex items-center justify-between">
          <h1 className="text-xl font-semibold text-gray-800">Invoice Assistant</h1>
          <div className="flex items-center space-x-2">
            <div className="w-2 h-2 bg-green-500 rounded-full"></div>
            <span className="text-sm text-gray-600">{customerName}</span>
          </div>
        </div>
      </header>

      <main className="flex-1 max-w-4xl w-full mx-auto p-4 flex flex-col">
        <div className="flex-1 overflow-y-auto mb-4 space-y-4">
          <AnimatePresence>
            {messages.map((message, index) => (
              <motion.div
                key={index}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -20 }}
                className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}
              >
                <div
                  className={`max-w-[80%] rounded-lg p-4 ${
                    message.role === 'user'
                      ? 'bg-blue-600 text-white'
                      : 'bg-white shadow-md text-gray-800'
                  }`}
                >
                  {message.content}
                </div>
              </motion.div>
            ))}
          </AnimatePresence>
          <div ref={messagesEndRef} />
        </div>

        <div className="space-y-4">
          <div className="flex flex-wrap gap-2">
            <AnimatePresence>
              {suggestions.map((suggestion, index) => (
                <motion.button
                  key={suggestion}
                  initial={{ opacity: 0, scale: 0.8 }}
                  animate={{ opacity: 1, scale: 1 }}
                  exit={{ opacity: 0, scale: 0.8 }}
                  transition={{ delay: index * 0.1 }}
                  onClick={() => setInput(suggestion)}
                  className="bg-white shadow-sm px-4 py-2 rounded-full text-sm text-gray-700 hover:bg-blue-50 transition-colors"
                >
                  {suggestion}
                </motion.button>
              ))}
            </AnimatePresence>
          </div>

          <div className="flex items-center space-x-2">
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyPress={(e) => e.key === 'Enter' && handleSend()}
              placeholder="Type your message..."
              className="flex-1 px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none transition-all bg-white"
            />
            <motion.button
              whileTap={{ scale: 0.95 }}
              onClick={handleSend}
              disabled={isLoading}
              className="bg-blue-600 text-white p-2 rounded-lg hover:bg-blue-700 transition-colors disabled:bg-blue-400"
            >
              <FiSend className="w-5 h-5" />
            </motion.button>
          </div>
        </div>
      </main>
    </div>
  );
}

export default App;