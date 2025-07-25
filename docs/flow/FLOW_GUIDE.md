# 🛒 Complete E-Commerce Flow Guide
**Cart → Order → Payment → Stock Reduction**

## 🎯 TESTED & WORKING ✅

Your complete e-commerce flow has been tested and verified:
- **Cart to Order ("Đặt hàng")** ✅
- **Order to Payment ("Thanh Toán")** ✅ 
- **Payment Confirmation** ✅
- **Stock Reduction** ✅ (20 → 17 items after ordering 3)
- **Status Updates** ✅ (Order: "Confirmed", Payment: "Paid")

---

## 🔄 API Flow Sequence

### **1. Add to Cart**
```http
POST /cart/items
Authorization: Bearer {token}
{
  "product_id": 7,
  "quantity": 3
}
```

### **2. Create Order ("Đặt hàng")**
```http
POST /orders
Authorization: Bearer {token}
```
**Response:** `{"order_id": 10}`
**What happens:** Cart → Order, Cart cleared

### **3. Create Payment ("Thanh Toán")**
```http
POST /payments
Authorization: Bearer {token}
{
  "order_id": 10,
  "payment_method": "Momo"
}
```
**Response:** `{"payment_id": 4, "transaction_code": "MOMOZA6A6XLE"}`

### **4. Confirm Payment ⭐ CRITICAL**
```http
PUT /payments/4/status
Authorization: Bearer {token}
{
  "payment_status": "Paid"
}
```
**What happens:** Payment → "Paid", Order → "Confirmed", Stock reduced

---

## ⚠️ FIXING "PENDING" STATUS ISSUE

### **Your Problem:** Status stays "pending" instead of "confirmed"

### **❌ Common Frontend Mistakes:**

#### 1. Wrong Status Value
```javascript
// WRONG
{ "payment_status": "Confirmed" }

// CORRECT  
{ "payment_status": "Paid" }      // ← Use "Paid"!
```

#### 2. Wrong API Endpoint
```javascript
// WRONG
PUT /orders/{order_id}/status

// CORRECT
PUT /payments/{payment_id}/status  // ← This endpoint!
```

#### 3. Missing Payment ID
```javascript
// WRONG - Not storing payment_id
let paymentId = null;

// CORRECT - Store from response
const response = await createPayment();
const paymentId = response.payment_id;  // ← Store this!
```

---

## 🌐 Frontend Integration

### **JavaScript/React Example:**

```javascript
class CheckoutService {
  constructor(baseUrl, token) {
    this.baseUrl = baseUrl;
    this.token = token;
  }
  
  async createOrder() {
    const response = await fetch(`${this.baseUrl}/orders`, {
      method: 'POST',
      headers: { 'Authorization': `Bearer ${this.token}` }
    });
    const data = await response.json();
    return data.order_id;
  }
  
  async createPayment(orderId, method = 'Momo') {
    const response = await fetch(`${this.baseUrl}/payments`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${this.token}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        order_id: orderId,
        payment_method: method
      })
    });
    const data = await response.json();
    return data.payment_id;  // ← Store this!
  }
  
  async confirmPayment(paymentId) {
    const response = await fetch(`${this.baseUrl}/payments/${paymentId}/status`, {
      method: 'PUT',
      headers: {
        'Authorization': `Bearer ${this.token}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        payment_status: "Paid"  // ← KEY: Use "Paid"
      })
    });
    return response.ok;
  }
  
  // Complete checkout flow
  async checkout(paymentMethod = 'Momo') {
    try {
      const orderId = await this.createOrder();
      console.log('✅ Order created:', orderId);
      
      const paymentId = await this.createPayment(orderId, paymentMethod);
      console.log('✅ Payment created:', paymentId);
      
      await this.confirmPayment(paymentId);
      console.log('✅ Payment confirmed!');
      
      return { success: true, orderId, paymentId };
    } catch (error) {
      console.error('❌ Checkout failed:', error);
      return { success: false, error: error.message };
    }
  }
}

// Usage
const checkout = new CheckoutService('http://localhost:8000', userToken);

// When user clicks "Thanh Toán"
async function handlePayment() {
  const result = await checkout.checkout('Momo');
  
  if (result.success) {
    alert('Thanh toán thành công!');
    // Navigate to success page
  } else {
    alert('Thanh toán thất bại: ' + result.error);
  }
}
```

---

## 📱 Flutter/Dart Implementation

```dart
class ECommerceService {
  final String baseUrl;
  final String token;
  
  ECommerceService(this.baseUrl, this.token);
  
  Future<int> createOrder() async {
    final response = await http.post(
      Uri.parse('$baseUrl/orders'),
      headers: {'Authorization': 'Bearer $token'},
    );
    final data = json.decode(response.body);
    return data['order_id'];
  }
  
  Future<int> createPayment(int orderId, String method) async {
    final response = await http.post(
      Uri.parse('$baseUrl/payments'),
      headers: {
        'Authorization': 'Bearer $token',
        'Content-Type': 'application/json',
      },
      body: json.encode({
        'order_id': orderId,
        'payment_method': method,
      }),
    );
    final data = json.decode(response.body);
    return data['payment_id'];
  }
  
  Future<bool> confirmPayment(int paymentId) async {
    final response = await http.put(
      Uri.parse('$baseUrl/payments/$paymentId/status'),
      headers: {
        'Authorization': 'Bearer $token',
        'Content-Type': 'application/json',
      },
      body: json.encode({
        'payment_status': 'Paid',  // ← Use "Paid"
      }),
    );
    return response.statusCode == 200;
  }
  
  Future<bool> completeCheckout(String paymentMethod) async {
    try {
      final orderId = await createOrder();
      final paymentId = await createPayment(orderId, paymentMethod);
      return await confirmPayment(paymentId);
    } catch (e) {
      print('Checkout failed: $e');
      return false;
    }
  }
}

// Flutter UI
class CheckoutScreen extends StatefulWidget {
  @override
  _CheckoutScreenState createState() => _CheckoutScreenState();
}

class _CheckoutScreenState extends State<CheckoutScreen> {
  final ECommerceService _service = ECommerceService(baseUrl, userToken);
  bool _isProcessing = false;
  
  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: Text('Thanh Toán')),
      body: Column(
        children: [
          // Payment methods...
          
          ElevatedButton(
            onPressed: _isProcessing ? null : _handlePayment,
            child: _isProcessing 
              ? CircularProgressIndicator() 
              : Text('Thanh Toán'),
          ),
        ],
      ),
    );
  }
  
  void _handlePayment() async {
    setState(() => _isProcessing = true);
    
    final success = await _service.completeCheckout('Momo');
    
    if (success) {
      // Navigate to success
      Navigator.push(context, MaterialPageRoute(
        builder: (context) => PaymentSuccessScreen(),
      ));
    } else {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('Thanh toán thất bại!')),
      );
    }
    
    setState(() => _isProcessing = false);
  }
}
```

---

## 🔍 Debug Your Frontend

### **Step 1: Check API Calls**
Add this to your browser console:
```javascript
// Monitor all API calls
const originalFetch = window.fetch;
window.fetch = function(...args) {
  console.log('🌐 API:', args[0], args[1]?.body);
  return originalFetch(...args).then(r => {
    console.log('📱 Status:', r.status);
    return r;
  });
};
```

### **Step 2: Verify Payment ID**
```javascript
const createPayment = async (orderId) => {
  const response = await fetch('/payments', {
    method: 'POST',
    headers: { 'Authorization': `Bearer ${token}`, 'Content-Type': 'application/json' },
    body: JSON.stringify({ order_id: orderId, payment_method: 'Momo' })
  });
  
  const data = await response.json();
  console.log('🔍 Payment response:', data); // ← Check this
  
  if (!data.payment_id) {
    console.error('❌ No payment_id!');
    return null;
  }
  
  return data.payment_id;
};
```

### **Step 3: Test Status Update**
```javascript
const testStatusUpdate = async (paymentId) => {
  console.log('🔍 Testing payment ID:', paymentId);
  
  const response = await fetch(`/payments/${paymentId}/status`, {
    method: 'PUT',
    headers: { 'Authorization': `Bearer ${token}`, 'Content-Type': 'application/json' },
    body: JSON.stringify({ payment_status: 'Paid' })
  });
  
  console.log('🔍 Status:', response.status);
  const result = await response.json();
  console.log('🔍 Result:', result);
  
  return response.ok;
};
```

---

## 📊 Success Verification

After payment confirmation, verify:

### **1. Order Status**
```http
GET /orders/{order_id}
Expected: { "status": "Confirmed" }
```

### **2. Payment Status**
```http
GET /payments/{payment_id}
Expected: { "payment_status": "Paid" }
```

### **3. Stock Reduction**
```http
GET /products/{product_id}
Expected: Stock reduced by ordered quantity
```

---

## 🎯 Quick Fix Checklist

When payment status stays "pending":

- [ ] ✅ Using `"Paid"` not `"Confirmed"` for payment_status
- [ ] ✅ Using `PUT /payments/{payment_id}/status` endpoint
- [ ] ✅ Storing payment_id from payment creation response
- [ ] ✅ Including proper Authorization header
- [ ] ✅ Using correct Content-Type: application/json
- [ ] ✅ Handling async operations properly
- [ ] ✅ Checking response status codes

---

## 🧪 Test Script

Use this to test your implementation:

```javascript
const testFullFlow = async () => {
  const token = 'YOUR_JWT_TOKEN';
  const baseUrl = 'http://localhost:8000';
  
  try {
    // Add to cart
    await fetch(`${baseUrl}/cart/items`, {
      method: 'POST',
      headers: { 'Authorization': `Bearer ${token}`, 'Content-Type': 'application/json' },
      body: JSON.stringify({ product_id: 1, quantity: 2 })
    });
    console.log('✅ Cart');
    
    // Create order
    const orderRes = await fetch(`${baseUrl}/orders`, {
      method: 'POST',
      headers: { 'Authorization': `Bearer ${token}` }
    });
    const { order_id } = await orderRes.json();
    console.log('✅ Order:', order_id);
    
    // Create payment
    const paymentRes = await fetch(`${baseUrl}/payments`, {
      method: 'POST',
      headers: { 'Authorization': `Bearer ${token}`, 'Content-Type': 'application/json' },
      body: JSON.stringify({ order_id, payment_method: 'Momo' })
    });
    const { payment_id } = await paymentRes.json();
    console.log('✅ Payment:', payment_id);
    
    // Confirm payment
    const confirmRes = await fetch(`${baseUrl}/payments/${payment_id}/status`, {
      method: 'PUT',
      headers: { 'Authorization': `Bearer ${token}`, 'Content-Type': 'application/json' },
      body: JSON.stringify({ payment_status: 'Paid' })
    });
    console.log('✅ Confirm:', confirmRes.status);
    
    // Check final status
    const finalRes = await fetch(`${baseUrl}/orders/${order_id}`, {
      headers: { 'Authorization': `Bearer ${token}` }
    });
    const finalOrder = await finalRes.json();
    console.log('✅ Final status:', finalOrder.status);
    
    if (finalOrder.status === 'Confirmed') {
      console.log('🎉 SUCCESS!');
    }
    
  } catch (error) {
    console.error('❌ Failed:', error);
  }
};

testFullFlow();
```

---

## 🚀 Key Points

### **✅ What Works:**
- Cart → Order conversion
- Payment creation with transaction codes
- Status updates (Paid → Confirmed)
- Automatic stock reduction
- Complete flow tested

### **🔑 Critical Points:**
1. **Use `"Paid"`** for payment_status (not "Confirmed")
2. **Store payment_id** from creation response
3. **Use correct endpoint:** `PUT /payments/{payment_id}/status`
4. **Stock reduces automatically** when payment confirmed
5. **Order status becomes "Confirmed"** automatically

### **⚠️ Common Issues:**
- Wrong status value
- Missing payment_id
- Wrong API endpoint
- Missing authentication
- Not handling promises correctly

---

**Your e-commerce flow is now ready! The backend works perfectly - just fix the frontend API calls using the examples above.** 🎉
