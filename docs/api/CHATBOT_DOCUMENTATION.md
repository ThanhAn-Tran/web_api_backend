# AI Chatbot Documentation

## Overview

This AI-powered chatbot system integrates ChatGPT-3.5 Turbo with your e-commerce backend to provide intelligent product consultation and shopping assistance. The chatbot can understand natural language queries, search for products, and perform actions like adding items to cart.

## Features

- **Natural Language Processing**: Powered by OpenAI GPT-3.5 Turbo
- **Product Search**: Intelligent product discovery based on user descriptions
- **Shopping Actions**: Add products to cart, view cart contents
- **Conversation Context**: Maintains chat history for personalized interactions
- **Intent Recognition**: Automatically detects user intentions (search, purchase, etc.)
- **Restricted Domain**: Focused only on shop-related conversations

## Setup

### 1. Install Dependencies

```bash
pip install openai==1.12.0
```

### 2. Configure OpenAI API Key

Edit `config.py` and replace the placeholder with your actual OpenAI API key:

```python
OPENAI_API_KEY = "sk-your-actual-openai-api-key-here"
```

### 3. Database Schema

The chatbot uses the existing `Conversations` table:

```sql
CREATE TABLE Conversations (
    ConversationID INT IDENTITY(1,1) PRIMARY KEY,
    UserID INT FOREIGN KEY REFERENCES Users(UserID),
    Role INT NOT NULL, -- 1: User, 2: Assistant
    Message NVARCHAR(MAX) NOT NULL,
    CreatedAt DATETIME DEFAULT GETDATE()
);
```

## API Endpoints

### 1. Main Chat Endpoint

**POST** `/chatbot/chat`

Send a message to the AI chatbot and get a response with product recommendations.

**Request:**
```json
{
  "message": "I'm looking for a pair of black pants around 100k, something with a cool style"
}
```

**Response:**
```json
{
  "response": "I'd be happy to help you find black pants! Based on your budget of around 100k and preference for cool style, here are some great options...",
  "products": [
    {
      "product_id": 1,
      "name": "Cool Black Cargo Pants",
      "description": "Trendy black cargo pants with modern fit",
      "price": 95000.00,
      "color": "Black",
      "style": "Cool",
      "stock": 25
    }
  ],
  "actions_performed": ["product_search"],
  "conversation_id": 123
}
```

### 2. Conversation History

**GET** `/chatbot/history?limit=20`

Get conversation history for the current user.

**Response:**
```json
{
  "conversation_history": [
    {
      "conversation_id": 1,
      "role": "user",
      "message": "I'm looking for black pants",
      "timestamp": "2024-01-15 10:30:00"
    },
    {
      "conversation_id": 2,
      "role": "assistant", 
      "message": "I found some great black pants for you...",
      "timestamp": "2024-01-15 10:30:05"
    }
  ],
  "total_messages": 2,
  "user_id": 1
}
```

### 3. Product Search

**POST** `/chatbot/product-search`

Search products using natural language without full conversation context.

**Request:**
```json
{
  "message": "modern white sneakers for summer"
}
```

**Response:**
```json
{
  "query": "modern white sneakers for summer",
  "parsed_parameters": {
    "min_price": null,
    "max_price": null,
    "colors": ["White"],
    "styles": ["Modern", "Summer"],
    "product_types": ["sneakers"],
    "keywords": ["white", "sneakers", "summer"]
  },
  "products": [...],
  "total_found": 5
}
```

### 4. Add to Cart

**POST** `/chatbot/add-to-cart/{product_id}`

Add a specific product to the user's cart via chatbot interface.

### 5. View Cart

**GET** `/chatbot/cart-contents`

Get current cart contents via chatbot interface.

### 6. Quick Chat

**POST** `/chatbot/quick-chat`

Simplified chat without full conversation context (for testing).

## Natural Language Understanding

### Intent Recognition

The chatbot automatically recognizes these intents:

1. **search_products**: User wants to find products
   - Keywords: "looking for", "want", "need", "find", "search", "show me"
   - Example: "I'm looking for black pants"

2. **add_to_cart**: User wants to add items to cart
   - Keywords: "add to cart", "buy", "purchase", "I'll take"
   - Example: "Add product 123 to my cart"

3. **view_cart**: User wants to see cart contents
   - Keywords: "cart", "my cart", "what's in my cart"
   - Example: "Show me my cart"

4. **general_conversation**: General questions about the shop
   - Example: "What types of products do you sell?"

### Product Search Parameters

The system can extract these parameters from natural language:

- **Price Range**: "around 100k", "under 200k", "100k-150k"
- **Colors**: "black", "white", "red", "blue", etc.
- **Styles**: "cool", "trendy", "modern", "classic", "casual", etc.
- **Product Types**: "pants", "shirt", "shoes", "dress", etc.
- **Keywords**: General search terms

### Example Queries

| User Input | Extracted Parameters |
|------------|---------------------|
| "I'm looking for a pair of black pants around 100k, something with a cool style" | Type: pants, Color: black, Price: 80k-120k, Style: cool |
| "Show me red dresses under 200k for a party" | Type: dress, Color: red, Price: <200k, Style: party |
| "I need casual white sneakers" | Type: sneakers, Color: white, Style: casual |

## System Architecture

### Components

1. **ChatbotService**: Main service handling OpenAI integration
2. **ProductSearchService**: Natural language product search
3. **ChatbotRouter**: API endpoints
4. **Models**: Pydantic models for requests/responses

### Data Flow

```
User Message → Intent Analysis → Product Search → OpenAI Response → Format Output → Save Conversation
```

### Context Management

- Maintains last 5 conversation messages for context
- Stores all conversations in database
- Provides personalized responses based on history

## Configuration

### OpenAI Settings (config.py)

```python
OPENAI_API_KEY = "your-api-key"
OPENAI_MODEL = "gpt-3.5-turbo"
OPENAI_MAX_TOKENS = 1000
OPENAI_TEMPERATURE = 0.7
```

### System Prompt

The chatbot is configured with a system prompt that:
- Defines it as a product consultant
- Restricts conversations to shop-related topics
- Provides guidelines for helpful responses
- Lists available actions

## Testing

### Running Tests

```bash
python test_chatbot.py
```

### Test Scenarios

1. **Product Search Tests**
   - Search for specific products
   - Price-based filtering
   - Color and style preferences

2. **Conversation Flow**
   - Multi-turn conversations
   - Context preservation
   - Intent switching

3. **Cart Operations**
   - Adding products via chat
   - Viewing cart contents
   - Product recommendations

### Interactive Testing

The test script provides an interactive chat mode:

```bash
python test_chatbot.py
# Choose option 2 for interactive chat
```

## Integration Examples

### Flutter Integration

```dart
class ChatbotService {
  static const String baseUrl = 'http://your-api-url';
  
  static Future<ChatResponse> sendMessage(String message, String token) async {
    final response = await http.post(
      Uri.parse('$baseUrl/chatbot/chat'),
      headers: {
        'Content-Type': 'application/json',
        'Authorization': 'Bearer $token',
      },
      body: jsonEncode({'message': message}),
    );
    
    if (response.statusCode == 200) {
      return ChatResponse.fromJson(jsonDecode(response.body));
    }
    throw Exception('Failed to send message');
  }
}
```

### React Integration

```javascript
const chatbotService = {
  async sendMessage(message, token) {
    const response = await fetch('/chatbot/chat', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`,
      },
      body: JSON.stringify({ message }),
    });
    
    if (!response.ok) {
      throw new Error('Failed to send message');
    }
    
    return response.json();
  }
};
```

## Error Handling

### Common Issues

1. **OpenAI API Key Missing/Invalid**
   - Error: Authentication failed
   - Solution: Check OPENAI_API_KEY in config.py

2. **No Products Found**
   - Error: Empty product list
   - Solution: Add sample products to database

3. **Database Connection Issues**
   - Error: Database connection failed
   - Solution: Check SQL Server connection

### Error Responses

```json
{
  "detail": "Error processing chat message: OpenAI API key not configured"
}
```

## Best Practices

### For Users
- Be specific about product requirements
- Use natural language (the system is designed for it)
- Ask follow-up questions for clarification

### For Developers
- Monitor OpenAI API usage and costs
- Regularly update the system prompt based on user feedback
- Add more product attributes for better search
- Implement conversation memory limitations

## Security Considerations

1. **Authentication Required**: All endpoints require valid JWT tokens
2. **Input Validation**: All user inputs are validated
3. **Rate Limiting**: Consider implementing rate limits for API calls
4. **API Key Security**: Store OpenAI API key securely

## Monitoring and Analytics

### Metrics to Track
- Conversation volume
- Intent recognition accuracy
- Product search success rate
- User satisfaction (implement feedback system)
- OpenAI API usage and costs

### Logging
The system logs:
- User messages and bot responses
- Intent recognition results
- Product search queries
- Error conditions

## Future Enhancements

1. **Advanced Features**
   - Product recommendations based on purchase history
   - Multi-language support
   - Voice integration
   - Image-based product search

2. **Personalization**
   - User preference learning
   - Personalized product recommendations
   - Shopping behavior analysis

3. **Business Intelligence**
   - Conversation analytics
   - Popular product trends
   - Customer insights

## Troubleshooting

### Common Problems

**Problem**: Chatbot not responding
- Check OpenAI API key configuration
- Verify internet connection
- Check API quota limits

**Problem**: Product search not working
- Verify database connection
- Check if products exist in database
- Review search parameters extraction

**Problem**: Authentication errors
- Ensure user is logged in
- Check JWT token validity
- Verify user permissions

### Debug Mode

Enable debug logging:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

This will show detailed information about:
- Intent recognition process
- Product search queries
- OpenAI API calls
- Database operations 