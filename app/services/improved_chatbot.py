import json
import re
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
from dataclasses import dataclass, field
from app.database import get_connection
from app.config import OPENAI_API_KEY, OPENAI_MODEL
from openai import OpenAI
import logging

logger = logging.getLogger(__name__)

@dataclass
class SlotFillingState:
    """Tracks the state of slot filling for product search"""
    category: Optional[str] = None
    style: Optional[str] = None
    color: Optional[str] = None
    price_range: Optional[Dict[str, Any]] = None
    additional_attributes: Dict[str, Any] = field(default_factory=dict)
    is_complete: bool = False

    def check_completeness(self) -> bool:
        """Check if we have minimum required slots filled"""
        # At least category and one other attribute
        return bool(self.category and (self.style or self.color))

@dataclass
class ConversationContext:
    """Maintains conversation context and memory"""
    user_id: int
    messages: List[Dict[str, str]] = field(default_factory=list)
    current_intent: Optional[str] = None
    slot_state: SlotFillingState = field(default_factory=SlotFillingState)
    last_products_shown: List[Dict] = field(default_factory=list)
    last_action: Optional[str] = None

class ImprovedChatbotService:
    """
    Enhanced chatbot service with:
    - Conversation memory and context awareness
    - OpenAI-based intent classification
    - Slot filling for product search
    - Better conversation flow management
    """
    
    def __init__(self):
        try:
            self.client = OpenAI(api_key=OPENAI_API_KEY)
        except Exception as e:
            logger.error(f"Failed to initialize OpenAI client: {e}")
            self.client = None
        
        # Store conversation contexts per user
        self.user_contexts: Dict[int, ConversationContext] = {}
        
        # Intent definitions for OpenAI
        self.intent_definitions = {
            "search_products": "User wants to search for or find products",
            "add_to_cart": "User wants to add a product to their shopping cart",
            "view_cart": "User wants to see what's in their shopping cart",
            "product_view": "User wants detailed information about a specific product",
            "remove_from_cart": "User wants to remove a product from their cart",
            "friendly_chat": "User is making general conversation or small talk"
        }
        
        # Category mappings
        self.category_mapping = {
            1: ['shirt', 'top', 'blouse', 'tee', 't-shirt', 'polo', 'tank'],
            2: ['pants', 'trousers', 'jeans', 'bottoms', 'shorts', 'skirt'],
            3: ['dress', 'gown', 'evening wear', 'sundress'],
            4: ['jacket', 'coat', 'blazer', 'hoodie', 'sweater', 'cardigan', 'outerwear'],
            5: ['shoes', 'sneakers', 'boots', 'heels', 'sandals', 'footwear'],
            6: ['bag', 'purse', 'handbag', 'backpack', 'watch', 'jewelry', 'accessories']
        }
        
        # Style options
        self.style_options = ['casual', 'formal', 'smart casual', 'trendy', 'classic', 'elegant', 'sport', 'basic']
        
        # Color options
        self.color_options = ['black', 'white', 'blue', 'red', 'green', 'gray', 'brown', 'pink', 'yellow', 'purple']

    def chat(self, user_id: int, message: str) -> Dict[str, Any]:
        """
        Main chat method with conversation memory and context awareness
        """
        try:
            # Get or create user context
            context = self._get_or_create_context(user_id)
            
            # Add user message to context
            context.messages.append({"role": "user", "content": message})
            
            # Load recent conversation history from database
            self._load_conversation_history(context)
            
            # Classify intent with conversation context
            intent_result = self._classify_intent_with_context(message, context)
            
            # Process based on intent
            if intent_result["intent"] == "search_products":
                result = self._handle_product_search_with_slots(message, context)
            elif intent_result["intent"] == "add_to_cart":
                result = self._handle_add_to_cart(message, context)
            elif intent_result["intent"] == "view_cart":
                result = self._handle_view_cart(context)
            elif intent_result["intent"] == "product_view":
                result = self._handle_product_view(message, context)
            elif intent_result["intent"] == "remove_from_cart":
                result = self._handle_remove_from_cart(message, context)
            else:
                result = self._handle_friendly_chat(message, context)
            
            # Update context
            context.current_intent = intent_result["intent"]
            context.last_action = result.get("actions_performed", ["friendly_chat"])[0]
            context.messages.append({"role": "assistant", "content": result["response"]})
            
            # Save conversation with metadata
            metadata = {
                "slot_state": context.slot_state.__dict__ if hasattr(context.slot_state, '__dict__') else None,
                "confidence": intent_result.get("confidence", 0)
            }
            conversation_id = self._save_conversation(
                user_id, 
                message, 
                result["response"], 
                intent=intent_result["intent"],
                metadata=metadata
            )
            result["conversation_id"] = conversation_id or 1
            
            return result
            
        except Exception as e:
            logger.error(f"Chat error: {e}")
            return {
                "response": "I apologize, but I encountered an error. Please try again.",
                "products": [],
                "actions_performed": ["error"],
                "conversation_id": 1,
                "intent": "error"
            }

    def _get_or_create_context(self, user_id: int) -> ConversationContext:
        """Get existing context or create new one"""
        if user_id not in self.user_contexts:
            self.user_contexts[user_id] = ConversationContext(user_id=user_id)
        return self.user_contexts[user_id]

    def _load_conversation_history(self, context: ConversationContext, limit: int = 5):
        """Load recent conversation history from database into context"""
        try:
            conn = get_connection()
            cursor = conn.cursor()
            
            # Get recent messages
            cursor.execute("""
                SELECT TOP (?) Role, Message, CreatedAt
                FROM Conversations 
                WHERE UserID = ? 
                ORDER BY CreatedAt DESC
            """, (limit * 2, context.user_id))  # *2 to get both user and bot messages
            
            results = cursor.fetchall()
            
            # Convert to message format and add to context if not already there
            history_messages = []
            for row in reversed(results):
                role = "user" if row[0] == 1 else "assistant"
                history_messages.append({"role": role, "content": row[1]})
            
            # Prepend history to current messages (avoiding duplicates)
            if len(context.messages) <= 2:  # Only current exchange
                context.messages = history_messages + context.messages
            
            conn.close()
            
        except Exception as e:
            logger.error(f"Error loading conversation history: {e}")

    def _classify_intent_with_context(self, message: str, context: ConversationContext) -> Dict[str, Any]:
        """Classify intent using OpenAI with conversation context"""
        if not self.client:
            return self._fallback_intent_classification(message)
        
        try:
            # Build context-aware prompt
            intent_list = ", ".join(self.intent_definitions.keys())
            
            # Include conversation history in the prompt
            conversation_context = "\n".join([
                f"{msg['role']}: {msg['content']}" 
                for msg in context.messages[-6:]  # Last 3 exchanges
            ])
            
            prompt = f"""You are an intent classifier for an e-commerce chatbot. 
            
Based on the conversation history and the current user message, classify the intent.

Available intents:
{chr(10).join([f"- {intent}: {desc}" for intent, desc in self.intent_definitions.items()])}

Conversation history:
{conversation_context}

Current user message: {message}

Respond with a JSON object containing:
- "intent": one of [{intent_list}]
- "confidence": a number between 0 and 1
- "entities": extracted entities like product_ids, colors, styles, categories, etc.

Examples:
User: "I want to buy a black shirt"
Response: {{"intent": "search_products", "confidence": 0.9, "entities": {{"color": "black", "category": "shirt"}}}}

User: "add product 123 to cart"
Response: {{"intent": "add_to_cart", "confidence": 0.95, "entities": {{"product_ids": [123]}}}}

User: "tell me more about product 456"
Response: {{"intent": "product_view", "confidence": 0.9, "entities": {{"product_ids": [456]}}}}
"""
            
            response = self.client.chat.completions.create(
                model=OPENAI_MODEL,
                messages=[
                    {"role": "system", "content": "You are a precise intent classifier. Always respond with valid JSON only, no additional text."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,  # Lower temperature for more consistent classification
                max_tokens=2000
            )
            
            response_text = response.choices[0].message.content.strip()
            # Try to extract JSON if wrapped in markdown code blocks
            if "```json" in response_text:
                response_text = response_text.split("```json")[1].split("```")[0].strip()
            elif "```" in response_text:
                response_text = response_text.split("```")[1].split("```")[0].strip()
            
            result = json.loads(response_text)
            return result
            
        except Exception as e:
            logger.error(f"OpenAI intent classification error: {e}")
            return self._fallback_intent_classification(message)

    def _fallback_intent_classification(self, message: str) -> Dict[str, Any]:
        """Fallback rule-based intent classification"""
        message_lower = message.lower()
        
        # Simple pattern matching
        if any(word in message_lower for word in ['cart', 'basket']):
            if any(word in message_lower for word in ['add', 'put']):
                return {"intent": "add_to_cart", "confidence": 0.8, "entities": {}}
            elif any(word in message_lower for word in ['remove', 'delete']):
                return {"intent": "remove_from_cart", "confidence": 0.8, "entities": {}}
            else:
                return {"intent": "view_cart", "confidence": 0.8, "entities": {}}
        elif any(word in message_lower for word in ['product', 'item']) and re.search(r'\d+', message):
            return {"intent": "product_view", "confidence": 0.8, "entities": {}}
        elif any(word in message_lower for word in ['find', 'search', 'looking', 'want', 'need', 'show']):
            return {"intent": "search_products", "confidence": 0.8, "entities": {}}
        else:
            return {"intent": "friendly_chat", "confidence": 0.7, "entities": {}}

    def _handle_product_search_with_slots(self, message: str, context: ConversationContext) -> Dict[str, Any]:
        """Handle product search with slot filling"""
        # Extract entities from message
        entities = self._extract_product_attributes(message, context)
        
        # Update slot state
        slot_state = context.slot_state
        if entities.get("category"):
            slot_state.category = entities["category"]
        if entities.get("style"):
            slot_state.style = entities["style"]
        if entities.get("color"):
            slot_state.color = entities["color"]
        if entities.get("price_range"):
            slot_state.price_range = entities["price_range"]
        
        # Check if we have enough information
        if not slot_state.check_completeness():
            # Ask for missing information
            missing_slots = self._get_missing_slots(slot_state)
            response = self._generate_slot_filling_question(missing_slots, context)
            # Determine which slot is missing (pick the first for simplicity)
            missing_slot = missing_slots[0] if missing_slots else None
            return {
                "response": response,
                "intent": "search_products",
                "actions_performed": [{
                    "type": "slot_filling",
                    "data": {
                        "slot": missing_slot,
                        "prompt": response
                    }
                }],
                "products": []
            }
        
        # We have enough information, perform search
        search_results = self._search_products_with_slots(slot_state)
        
        # Clear slot state after search
        context.slot_state = SlotFillingState()
        
        # Store products shown
        context.last_products_shown = search_results
        
        # Generate response
        if search_results:
            response = self._format_product_results(search_results, context)
        else:
            response = "I couldn't find any products matching your criteria. Would you like to try different specifications?"
        
        return {
            "response": response,
            "intent": "search_products",
            "actions_performed": ["search_products"],
            "products": search_results
        }

    def _extract_product_attributes(self, message: str, context: ConversationContext) -> Dict[str, Any]:
        """Extract product attributes using OpenAI"""
        if not self.client:
            return self._fallback_extract_attributes(message)
        
        try:
            prompt = f"""Extract product attributes from the user message.

Categories: {', '.join([cat for cats in self.category_mapping.values() for cat in cats])}
Styles: {', '.join(self.style_options)}
Colors: {', '.join(self.color_options)}

User message: {message}

Return a JSON object with any found attributes:
{{"category": "...", "style": "...", "color": "...", "price_range": {{"min": ..., "max": ...}}}}

Only include attributes that are explicitly mentioned."""

            response = self.client.chat.completions.create(
                model=OPENAI_MODEL,
                messages=[
                    {"role": "system", "content": "You are a product attribute extractor. Return only valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.2,
                max_tokens=150
            )
            
            return json.loads(response.choices[0].message.content.strip())
            
        except Exception as e:
            logger.error(f"Attribute extraction error: {e}")
            return self._fallback_extract_attributes(message)

    def _fallback_extract_attributes(self, message: str) -> Dict[str, Any]:
        """Fallback attribute extraction using patterns"""
        attributes = {}
        message_lower = message.lower()
        
        # Extract category
        for cat_id, keywords in self.category_mapping.items():
            for keyword in keywords:
                if keyword in message_lower:
                    attributes["category"] = keyword
                    break
        
        # Extract color
        for color in self.color_options:
            if color in message_lower:
                attributes["color"] = color
                break
        
        # Extract style  
        for style in self.style_options:
            if style in message_lower:
                attributes["style"] = style
                break
        
        # Extract price
        price_match = re.search(r'(\d+)k?', message_lower)
        if price_match:
            price = int(price_match.group(1))
            if 'k' in message_lower:
                price *= 1000
            attributes["price_range"] = {"min": price * 0.8, "max": price * 1.2}
        
        return attributes

    def _get_missing_slots(self, slot_state: SlotFillingState) -> List[str]:
        """Identify which slots are missing"""
        missing = []
        if not slot_state.category:
            missing.append("category")
        if not slot_state.style and not slot_state.color:
            missing.extend(["style", "color"])
        return missing

    def _generate_slot_filling_question(self, missing_slots: List[str], context: ConversationContext) -> str:
        """Generate a natural question to fill missing slots"""
        if not self.client:
            return self._fallback_slot_question(missing_slots)
        
        try:
            current_slots = {
                "category": context.slot_state.category,
                "style": context.slot_state.style,
                "color": context.slot_state.color
            }
            
            prompt = f"""Generate a natural, friendly question to ask for missing product information.

Current information: {current_slots}
Missing information: {missing_slots}

Generate a conversational question that asks for the missing information naturally.
Examples:
- "What type of product are you looking for?"
- "Do you have a preferred color or style in mind?"
- "What style would you prefer - casual, formal, or something else?"

Keep it brief and natural."""

            response = self.client.chat.completions.create(
                model=OPENAI_MODEL,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,
                max_tokens=100
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            logger.error(f"Slot question generation error: {e}")
            return self._fallback_slot_question(missing_slots)

    def _fallback_slot_question(self, missing_slots: List[str]) -> str:
        """Fallback slot filling questions"""
        if "category" in missing_slots:
            return "What type of product are you looking for? (shirt, pants, shoes, etc.)"
        elif "style" in missing_slots and "color" in missing_slots:
            return "Do you have a preferred style or color in mind?"
        elif "style" in missing_slots:
            return "What style would you prefer? (casual, formal, trendy, etc.)"
        elif "color" in missing_slots:
            return "What color would you like?"
        else:
            return "Could you provide more details about what you're looking for?"

    def _search_products_with_slots(self, slot_state: SlotFillingState) -> List[Dict[str, Any]]:
        """Search products based on filled slots"""
        try:
            conn = get_connection()
            cursor = conn.cursor()
            
            where_conditions = ["Stock > 0"]
            params = []
            
            # Category condition
            if slot_state.category:
                category_id = None
                for cat_id, keywords in self.category_mapping.items():
                    if slot_state.category.lower() in [k.lower() for k in keywords]:
                        category_id = cat_id
                        break
                if category_id:
                    where_conditions.append("CategoryID = ?")
                    params.append(category_id)
            
            # Color condition
            if slot_state.color:
                where_conditions.append("Color LIKE ?")
                params.append(f"%{slot_state.color}%")
            
            # Style condition
            if slot_state.style:
                where_conditions.append("Style LIKE ?")
                params.append(f"%{slot_state.style}%")
            
            # Price condition
            if slot_state.price_range:
                if slot_state.price_range.get("min"):
                    where_conditions.append("Price >= ?")
                    params.append(slot_state.price_range["min"])
                if slot_state.price_range.get("max"):
                    where_conditions.append("Price <= ?")
                    params.append(slot_state.price_range["max"])
            
            where_clause = " AND ".join(where_conditions)
            
            query = f"""
            SELECT TOP 10 ProductID, Name, Description, Price, Stock, Color, Style, CategoryID
            FROM Products
            WHERE {where_clause}
            ORDER BY ProductID DESC
            """
            
            cursor.execute(query, params)
            results = cursor.fetchall()
            
            products = []
            for row in results:
                products.append({
                    "ProductID": row[0],
                    "Name": row[1] or "Product",
                    "Description": row[2] or "",
                    "Price": float(row[3]) if row[3] else 0.0,
                    "Stock": row[4] or 0,
                    "Color": row[5] or "N/A",
                    "Style": row[6] or "N/A",
                    "CategoryID": row[7] or 1
                })
            
            conn.close()
            return products
            
        except Exception as e:
            logger.error(f"Product search error: {e}")
            return []

    def _format_product_results(self, products: List[Dict], context: ConversationContext) -> str:
        """Format product results with context awareness"""
        if not self.client:
            return self._simple_format_products(products)
        
        try:
            # Include conversation context
            recent_context = "\n".join([
                f"{msg['role']}: {msg['content']}" 
                for msg in context.messages[-4:]
            ])
            
            prompt = f"""Format these product search results conversationally based on the user's request.

Recent conversation:
{recent_context}

Products found:
{json.dumps(products[:5], indent=2)}

Create a natural, helpful response that:
1. Acknowledges what the user was looking for
2. Presents the products in an easy-to-read format
3. Mentions key details like price, color, and style
4. Suggests next actions (view details, add to cart)

Keep it concise but informative."""

            response = self.client.chat.completions.create(
                model=OPENAI_MODEL,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,
                max_tokens=300
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            logger.error(f"Product formatting error: {e}")
            return self._simple_format_products(products)

    def _simple_format_products(self, products: List[Dict]) -> str:
        """Simple fallback product formatting"""
        if not products:
            return "No products found matching your criteria."
        
        response = f"I found {len(products)} products for you:\n\n"
        for i, product in enumerate(products[:5], 1):
            response += f"{i}. {product['Name']} (ID: {product['ProductID']})\n"
            response += f"   💰 Price: ${product['Price']:.2f}\n"
            response += f"   🎨 Color: {product['Color']} | Style: {product['Style']}\n"
            response += f"   📦 Stock: {product['Stock']} available\n\n"
        
        return response + "Would you like to see more details or add any to your cart?"

    def _handle_add_to_cart(self, message: str, context: ConversationContext) -> Dict[str, Any]:
        """Handle add to cart with context awareness"""
        # Extract product IDs
        product_ids = self._extract_product_ids(message)
        
        # If no product IDs found, check if user is referring to previously shown products
        if not product_ids and context.last_products_shown:
            # Try to understand which product from context
            product_reference = self._resolve_product_reference(message, context)
            if product_reference:
                product_ids = [product_reference]
        
        if not product_ids:
            return {
                "response": "I'm not sure which product you want to add. Could you specify the product ID or describe it?",
                "intent": "add_to_cart",
                "actions_performed": ["add_to_cart"],
                "products": []
            }
        
        # Add to cart
        result = self._add_products_to_cart(product_ids, context.user_id)
        
        return {
            "response": result,
            "intent": "add_to_cart",
            "actions_performed": ["add_to_cart"],
            "products": []
        }

    def _extract_product_ids(self, message: str) -> List[int]:
        """Extract product IDs from message"""
        ids = []
        matches = re.findall(r'\b(\d+)\b', message)
        for match in matches:
            try:
                product_id = int(match)
                if product_id > 0 and product_id < 10000:  # Reasonable product ID range
                    ids.append(product_id)
            except:
                pass
        return ids

    def _resolve_product_reference(self, message: str, context: ConversationContext) -> Optional[int]:
        """Resolve product reference from context (e.g., 'the first one', 'the black shirt')"""
        if not context.last_products_shown:
            return None
        
        message_lower = message.lower()
        
        # Check for ordinal references
        ordinals = {
            'first': 0, '1st': 0,
            'second': 1, '2nd': 1,
            'third': 2, '3rd': 2,
            'fourth': 3, '4th': 3,
            'fifth': 4, '5th': 4
        }
        
        for word, index in ordinals.items():
            if word in message_lower and index < len(context.last_products_shown):
                return context.last_products_shown[index]['ProductID']
        
        # Check for specific product attributes
        for product in context.last_products_shown:
            if (product['Color'].lower() in message_lower or 
                product['Style'].lower() in message_lower):
                return product['ProductID']
        
        return None

    def _add_products_to_cart(self, product_ids: List[int], user_id: int) -> str:
        """Add products to cart"""
        try:
            conn = get_connection()
            cursor = conn.cursor()
            
            # Get or create cart for user
            cursor.execute("SELECT CartID FROM Cart WHERE UserID = ?", (user_id,))
            cart = cursor.fetchone()
            
            if not cart:
                cursor.execute("INSERT INTO Cart (UserID) VALUES (?)", (user_id,))
                conn.commit()
                cursor.execute("SELECT CartID FROM Cart WHERE UserID = ?", (user_id,))
                cart = cursor.fetchone()
            
            cart_id = cart[0]
            
            added_products = []
            for product_id in product_ids:
                # Check if product exists and has stock
                cursor.execute("""
                    SELECT Name, Price, Stock FROM Products 
                    WHERE ProductID = ? AND Stock > 0
                """, (product_id,))
                
                product = cursor.fetchone()
                if product:
                    # Check if item already exists in cart
                    cursor.execute("""
                        SELECT CartItemID, Quantity FROM CartItems 
                        WHERE CartID = ? AND ProductID = ?
                    """, (cart_id, product_id))
                    
                    existing_item = cursor.fetchone()
                    
                    if existing_item:
                        # Update quantity
                        new_quantity = existing_item[1] + 1
                        cursor.execute("""
                            UPDATE CartItems SET Quantity = ? 
                            WHERE CartItemID = ?
                        """, (new_quantity, existing_item[0]))
                    else:
                        # Add new item
                        cursor.execute("""
                            INSERT INTO CartItems (CartID, ProductID, Quantity) 
                            VALUES (?, ?, ?)
                        """, (cart_id, product_id, 1))
                    
                    added_products.append({
                        "id": product_id,
                        "name": product[0],
                        "price": product[1]
                    })
            
            conn.commit()
            conn.close()
            
            if added_products:
                if len(added_products) == 1:
                    return f"✅ Added {added_products[0]['name']} to your cart!"
                else:
                    names = ", ".join([p['name'] for p in added_products])
                    return f"✅ Added {len(added_products)} items to your cart: {names}"
            else:
                return "❌ Could not add products to cart. They may be out of stock."
                
        except Exception as e:
            logger.error(f"Add to cart error: {e}")
            return "Sorry, there was an error adding to your cart. Please try again."

    def _handle_view_cart(self, context: ConversationContext) -> Dict[str, Any]:
        """Handle view cart request"""
        try:
            conn = get_connection()
            cursor = conn.cursor()
            
            # Get user's cart
            cursor.execute("SELECT CartID FROM Cart WHERE UserID = ?", (context.user_id,))
            cart = cursor.fetchone()
            
            if not cart:
                return {
                    "response": "Your cart is empty. Would you like to browse some products?",
                    "intent": "view_cart",
                    "actions_performed": ["view_cart"],
                    "products": []
                }
            
            cart_id = cart[0]
            
            # Get cart items
            cursor.execute("""
                SELECT ci.CartItemID, ci.ProductID, p.Name, p.Price, ci.Quantity,
                       p.Color, p.Style, (p.Price * ci.Quantity) as Total
                FROM CartItems ci
                JOIN Products p ON ci.ProductID = p.ProductID
                WHERE ci.CartID = ?
            """, (cart_id,))
            
            items = cursor.fetchall()
            conn.close()
            
            if not items:
                return {
                    "response": "Your cart is empty. Would you like to browse some products?",
                    "intent": "view_cart",
                    "actions_performed": ["view_cart"],
                    "products": []
                }
            
            cart_items = []
            total = 0
            
            for item in items:
                cart_item = {
                    "CartItemID": item[0],
                    "ProductID": item[1],
                    "Name": item[2],
                    "Price": float(item[3]),
                    "Quantity": item[4],
                    "Color": item[5],
                    "Style": item[6],
                    "Total": float(item[7])
                }
                cart_items.append(cart_item)
                total += item[7]
            
            # Format response
            response = self._format_cart_contents(cart_items, total)
            
            return {
                "response": response,
                "intent": "view_cart",
                "actions_performed": ["view_cart"],
                "products": cart_items
            }
            
        except Exception as e:
            logger.error(f"View cart error: {e}")
            return {
                "response": "Sorry, I couldn't retrieve your cart. Please try again.",
                "intent": "view_cart",
                "actions_performed": ["view_cart"],
                "products": []
            }

    def _format_cart_contents(self, cart_items: List[Dict], total: float) -> str:
        """Format cart contents nicely"""
        response = f"🛒 Your cart has {len(cart_items)} item(s):\n\n"
        
        for i, item in enumerate(cart_items, 1):
            response += f"{i}. {item['Name']} (ID: {item['ProductID']})\n"
            response += f"   💰 ${item['Price']:.2f} x {item['Quantity']} = ${item['Price'] * item['Quantity']:.2f}\n"
            response += f"   🎨 {item['Color']} | {item['Style']}\n\n"
        
        response += f"📊 Total: ${total:.2f}\n\n"
        response += "Would you like to checkout or continue shopping?"
        
        return response

    def _handle_product_view(self, message: str, context: ConversationContext) -> Dict[str, Any]:
        """Handle product view request"""
        product_ids = self._extract_product_ids(message)
        
        if not product_ids:
            # Try to resolve from context
            product_id = self._resolve_product_reference(message, context)
            if product_id:
                product_ids = [product_id]
        
        if not product_ids:
            return {
                "response": "Please specify which product you'd like to see details for (e.g., 'show product 123').",
                "intent": "product_view",
                "actions_performed": ["product_view"],
                "products": []
            }
        
        try:
            conn = get_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT ProductID, Name, Description, Price, Stock, Color, Style, CategoryID
                FROM Products
                WHERE ProductID = ?
            """, (product_ids[0],))
            
            row = cursor.fetchone()
            conn.close()
            
            if row:
                product = {
                    "ProductID": row[0],
                    "Name": row[1],
                    "Description": row[2],
                    "Price": float(row[3]),
                    "Stock": row[4],
                    "Color": row[5],
                    "Style": row[6],
                    "CategoryID": row[7]
                }
                
                response = self._format_product_details(product)
                
                return {
                    "response": response,
                    "intent": "product_view",
                    "actions_performed": ["product_view"],
                    "products": [product]
                }
            else:
                return {
                    "response": f"I couldn't find product {product_ids[0]}. Please check the product ID.",
                    "intent": "product_view",
                    "actions_performed": ["product_view"],
                    "products": []
                }
                
        except Exception as e:
            logger.error(f"Product view error: {e}")
            return {
                "response": "Sorry, I couldn't retrieve product details. Please try again.",
                "intent": "product_view",
                "actions_performed": ["product_view"],
                "products": []
            }

    def _format_product_details(self, product: Dict) -> str:
        """Format detailed product information"""
        response = f"📦 **{product['Name']}** (ID: {product['ProductID']})\n\n"
        response += f"📝 {product['Description']}\n\n"
        response += f"💰 Price: ${product['Price']:.2f}\n"
        response += f"🎨 Color: {product['Color']}\n"
        response += f"👔 Style: {product['Style']}\n"
        response += f"📊 Stock: {product['Stock']} available\n\n"
        
        if product['Stock'] > 0:
            response += "Would you like to add this to your cart?"
        else:
            response += "⚠️ This product is currently out of stock."
        
        return response

    def _handle_remove_from_cart(self, message: str, context: ConversationContext) -> Dict[str, Any]:
        """Handle remove from cart request"""
        product_ids = self._extract_product_ids(message)
        
        if not product_ids:
            return {
                "response": "Please specify which product to remove (e.g., 'remove product 123').",
                "intent": "remove_from_cart",
                "actions_performed": ["remove_from_cart"],
                "products": []
            }
        
        try:
            conn = get_connection()
            cursor = conn.cursor()
            
            # Get user's cart
            cursor.execute("SELECT CartID FROM Cart WHERE UserID = ?", (context.user_id,))
            cart = cursor.fetchone()
            
            if not cart:
                return {
                    "response": "You don't have a cart yet. Try adding some products first!",
                    "intent": "remove_from_cart",
                    "actions_performed": ["remove_from_cart"],
                    "products": []
                }
            
            cart_id = cart[0]
            
            removed_items = []
            for product_id in product_ids:
                cursor.execute("""
                    DELETE FROM CartItems 
                    WHERE CartID = ? AND ProductID = ?
                """, (cart_id, product_id))
                
                if cursor.rowcount > 0:
                    removed_items.append(product_id)
            
            conn.commit()
            
            # Get updated cart
            cursor.execute("""
                SELECT ci.ProductID, p.Name, p.Price, ci.Quantity
                FROM CartItems ci
                JOIN Products p ON ci.ProductID = p.ProductID
                WHERE ci.CartID = ?
            """, (cart_id,))
            
            remaining_items = cursor.fetchall()
            conn.close()
            
            if removed_items:
                response = f"✅ Removed {len(removed_items)} item(s) from your cart.\n\n"
                if remaining_items:
                    response += f"You still have {len(remaining_items)} item(s) in your cart."
                else:
                    response += "Your cart is now empty."
            else:
                response = "❌ Could not find those items in your cart."
            
            return {
                "response": response,
                "intent": "remove_from_cart",
                "actions_performed": ["remove_from_cart"],
                "products": []
            }
            
        except Exception as e:
            logger.error(f"Remove from cart error: {e}")
            return {
                "response": "Sorry, there was an error removing items. Please try again.",
                "intent": "remove_from_cart",
                "actions_performed": ["remove_from_cart"],
                "products": []
            }

    def _handle_friendly_chat(self, message: str, context: ConversationContext) -> Dict[str, Any]:
        """Handle general conversation with context awareness"""
        if not self.client:
            return {
                "response": "Hello! I'm here to help you find products and manage your shopping. What can I do for you?",
                "intent": "friendly_chat",
                "actions_performed": ["friendly_chat"],
                "products": []
            }
        
        try:
            # Build context-aware conversation
            messages = [
                {"role": "system", "content": """You are a helpful e-commerce shopping assistant. 
                Keep responses concise and friendly. If the user asks about non-shopping topics, 
                gently redirect them to shopping-related topics. You can make small talk but 
                always try to be helpful with their shopping needs."""}
            ]
            
            # Add recent conversation history
            for msg in context.messages[-6:]:
                messages.append(msg)
            
            response = self.client.chat.completions.create(
                model=OPENAI_MODEL,
                messages=messages,
                temperature=0.7,
                max_tokens=200
            )
            
            return {
                "response": response.choices[0].message.content.strip(),
                "intent": "friendly_chat",
                "actions_performed": ["friendly_chat"],
                "products": []
            }
            
        except Exception as e:
            logger.error(f"Friendly chat error: {e}")
            return {
                "response": "I'm here to help with your shopping! Feel free to ask about products or your cart.",
                "intent": "friendly_chat",
                "actions_performed": ["friendly_chat"],
                "products": []
            }

    def _save_conversation(self, user_id: int, user_message: str, bot_response: str, intent: Optional[str] = None, metadata: Optional[Dict] = None) -> Optional[int]:
        """Save conversation to database with metadata"""
        try:
            conn = get_connection()
            cursor = conn.cursor()
            
            # Generate session ID if not exists - use None for now to avoid database issues
            session_id = None
            
            # Prepare metadata JSON
            metadata_json = json.dumps(metadata) if metadata else None
            
            # Save user message
            cursor.execute("""
                INSERT INTO Conversations (UserID, Role, Message, CreatedAt, Intent, SessionID, Metadata) 
                VALUES (?, ?, ?, GETDATE(), ?, ?, ?)
            """, (user_id, 1, user_message, intent, session_id, metadata_json))
            
            # Save bot response
            cursor.execute("""
                INSERT INTO Conversations (UserID, Role, Message, CreatedAt, Intent, SessionID, Metadata) 
                VALUES (?, ?, ?, GETDATE(), ?, ?, ?)
            """, (user_id, 2, bot_response, intent, session_id, metadata_json))
            
            cursor.execute("SELECT SCOPE_IDENTITY()")
            result = cursor.fetchone()
            conversation_id = result[0] if result else None
            
            conn.commit()
            conn.close()
            
            return conversation_id
            
        except Exception as e:
            logger.error(f"Save conversation error: {e}")
            # If metadata columns don't exist, fall back to basic save
            try:
                conn = get_connection()
                cursor = conn.cursor()
                
                # Save without metadata columns
                cursor.execute("""
                    INSERT INTO Conversations (UserID, Role, Message, CreatedAt) 
                    VALUES (?, ?, ?, GETDATE())
                """, (user_id, 1, user_message))
                
                cursor.execute("""
                    INSERT INTO Conversations (UserID, Role, Message, CreatedAt) 
                    VALUES (?, ?, ?, GETDATE())
                """, (user_id, 2, bot_response))
                
                cursor.execute("SELECT SCOPE_IDENTITY()")
                result = cursor.fetchone()
                conversation_id = result[0] if result else None
                
                conn.commit()
                conn.close()
                
                return conversation_id
            except Exception as e2:
                logger.error(f"Fallback save error: {e2}")
                return None 

    def reset_conversation(self, user_id: int) -> Dict[str, Any]:
        """
        Reset conversation state and context for a user
        
        Args:
            user_id: The user ID to reset conversation for
            
        Returns:
            Dict with reset confirmation and new session info
        """
        try:
            # Clear conversation context from memory
            if user_id in self.user_contexts:
                del self.user_contexts[user_id]
            
            logger.info(f"Reset conversation context for user {user_id}")
            
            # Save reset action to database
            reset_message = "Conversation reset requested"
            reset_response = "Sure! Let's start fresh. What kind of product are you looking for?"
            
            # Generate new session ID
            import uuid
            new_session_id = str(uuid.uuid4())[:8]
            
            metadata = {
                'action': 'conversation_reset',
                'session_id': new_session_id,
                'reset_timestamp': datetime.now().isoformat()
            }
            
            conversation_id = self._save_conversation(
                user_id=user_id,
                user_message=reset_message,
                bot_response=reset_response,
                intent="conversation_reset",
                metadata=metadata
            )
            
            return {
                "response": reset_response,
                "products": [],
                "actions_performed": ["conversation_reset"],
                "conversation_id": conversation_id,
                "session_id": new_session_id,
                "status": "reset_successful"
            }
            
        except Exception as e:
            logger.error(f"Error resetting conversation for user {user_id}: {str(e)}")
            return {
                "response": "I apologize, but I couldn't reset the conversation properly. Let's try starting fresh - what can I help you find today?",
                "products": [],
                "actions_performed": ["conversation_reset"],
                "conversation_id": None,
                "status": "reset_error"
            } 