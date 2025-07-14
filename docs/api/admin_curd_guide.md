# Admin CURD API Guide for Flutter UI

This comprehensive guide helps Flutter developers implement the admin product management interface using the Web Selling Chatbot API.

## 🚀 Quick Start

### API Base URL
```
http://127.0.0.1:8000
```

### Required Dependencies
Add these to your `pubspec.yaml`:
```yaml
dependencies:
  http: ^1.1.0
  image_picker: ^1.0.4
  shared_preferences: ^2.2.2
```

---

## 🔐 Authentication

### Step 1: Admin Login
**Endpoint:** `POST /auth/login`

**Flutter Implementation:**
```dart
Future<String?> adminLogin(String username, String password) async {
  final response = await http.post(
    Uri.parse('$baseUrl/auth/login'),
    headers: {'Content-Type': 'application/json'},
    body: jsonEncode({
      'username': username,
      'password': password,
    }),
  );

  if (response.statusCode == 200) {
    final data = jsonDecode(response.body);
    String token = data['access_token'];
    
    // Store token locally
    SharedPreferences prefs = await SharedPreferences.getInstance();
    await prefs.setString('admin_token', token);
    
    return token;
  }
  return null;
}
```

**Sample Credentials:**
- Username: `admin`
- Password: `admin123`

**Response:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "user": {
    "user_id": 1,
    "username": "admin",
    "email": "admin@shop.com", 
    "role": 3
  }
}
```

### Step 2: Authorization Headers
Include the token in all subsequent requests:
```dart
Map<String, String> getAuthHeaders() {
  return {
    'Authorization': 'Bearer $token',
    'Content-Type': 'application/json',
  };
}
```

---

## 📱 Admin CURD Operations

### 🆕 CREATE Product

**Endpoint:** `POST /products`
**Content-Type:** `multipart/form-data`

**Flutter Implementation:**
```dart
Future<Map<String, dynamic>?> createProduct({
  required String name,
  required String description,
  required double price,
  required int stock,
  required String color,
  required String style,
  required int categoryId,
  required List<File> images,
}) async {
  var request = http.MultipartRequest('POST', Uri.parse('$baseUrl/products'));
  
  // Add authorization header
  request.headers['Authorization'] = 'Bearer $token';
  
  // Add form fields
  request.fields['name'] = name;
  request.fields['description'] = description;
  request.fields['price'] = price.toString();
  request.fields['stock'] = stock.toString();
  request.fields['color'] = color;
  request.fields['style'] = style;
  request.fields['category_id'] = categoryId.toString();
  
  // Add image files
  for (File image in images) {
    request.files.add(await http.MultipartFile.fromPath(
      'files',
      image.path,
    ));
  }
  
  final response = await request.send();
  
  if (response.statusCode == 201) {
    final responseData = await response.stream.bytesToString();
    return jsonDecode(responseData);
  }
  return null;
}
```

**Image Picker Integration:**
```dart
Future<List<File>> pickImages() async {
  final ImagePicker picker = ImagePicker();
  final List<XFile> images = await picker.pickMultiImage();
  return images.map((xFile) => File(xFile.path)).toList();
}
```

**UI Example:**
```dart
class CreateProductScreen extends StatefulWidget {
  @override
  _CreateProductScreenState createState() => _CreateProductScreenState();
}

class _CreateProductScreenState extends State<CreateProductScreen> {
  final _formKey = GlobalKey<FormState>();
  final _nameController = TextEditingController();
  final _descriptionController = TextEditingController();
  final _priceController = TextEditingController();
  final _stockController = TextEditingController();
  final _colorController = TextEditingController();
  final _styleController = TextEditingController();
  List<File> _selectedImages = [];

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: Text('Create Product')),
      body: Form(
        key: _formKey,
        child: Padding(
          padding: EdgeInsets.all(16.0),
          child: Column(
            children: [
              TextFormField(
                controller: _nameController,
                decoration: InputDecoration(labelText: 'Product Name'),
                validator: (value) => value?.isEmpty == true ? 'Required' : null,
              ),
              TextFormField(
                controller: _descriptionController,
                decoration: InputDecoration(labelText: 'Description'),
                maxLines: 3,
              ),
              TextFormField(
                controller: _priceController,
                decoration: InputDecoration(labelText: 'Price'),
                keyboardType: TextInputType.number,
              ),
              TextFormField(
                controller: _stockController,
                decoration: InputDecoration(labelText: 'Stock'),
                keyboardType: TextInputType.number,
              ),
              TextFormField(
                controller: _colorController,
                decoration: InputDecoration(labelText: 'Color'),
              ),
              TextFormField(
                controller: _styleController,
                decoration: InputDecoration(labelText: 'Style'),
              ),
              SizedBox(height: 20),
              ElevatedButton(
                onPressed: () async {
                  final images = await pickImages();
                  setState(() {
                    _selectedImages = images;
                  });
                },
                child: Text('Select Images (${_selectedImages.length})'),
              ),
              SizedBox(height: 20),
              ElevatedButton(
                onPressed: _submitForm,
                child: Text('Create Product'),
              ),
            ],
          ),
        ),
      ),
    );
  }

  void _submitForm() async {
    if (_formKey.currentState!.validate() && _selectedImages.isNotEmpty) {
      final result = await createProduct(
        name: _nameController.text,
        description: _descriptionController.text,
        price: double.parse(_priceController.text),
        stock: int.parse(_stockController.text),
        color: _colorController.text,
        style: _styleController.text,
        categoryId: 1, // You might want to make this selectable
        images: _selectedImages,
      );
      
      if (result != null) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Product created successfully!')),
        );
        Navigator.pop(context);
      }
    }
  }
}
```

---

### 📖 READ Products

#### Get All Products
**Endpoint:** `GET /products`

```dart
Future<List<Product>> getAllProducts() async {
  final response = await http.get(Uri.parse('$baseUrl/products'));
  
  if (response.statusCode == 200) {
    final List<dynamic> data = jsonDecode(response.body);
    return data.map((json) => Product.fromJson(json)).toList();
  }
  throw Exception('Failed to load products');
}
```

#### Get Single Product
**Endpoint:** `GET /products/{id}`

```dart
Future<Product?> getProduct(int productId) async {
  final response = await http.get(Uri.parse('$baseUrl/products/$productId'));
  
  if (response.statusCode == 200) {
    return Product.fromJson(jsonDecode(response.body));
  }
  return null;
}
```

**Product Model:**
```dart
class Product {
  final int productId;
  final String name;
  final String description;
  final double price;
  final int stock;
  final String color;
  final String style;
  final int categoryId;
  final bool isLocked;
  final String? imagePath;
  final List<ProductImage> images;
  final String createdAt;

  Product({
    required this.productId,
    required this.name,
    required this.description,
    required this.price,
    required this.stock,
    required this.color,
    required this.style,
    required this.categoryId,
    required this.isLocked,
    this.imagePath,
    required this.images,
    required this.createdAt,
  });

  factory Product.fromJson(Map<String, dynamic> json) {
    return Product(
      productId: json['product_id'],
      name: json['name'],
      description: json['description'],
      price: json['price'].toDouble(),
      stock: json['stock'],
      color: json['color'],
      style: json['style'],
      categoryId: json['category_id'],
      isLocked: json['is_locked'],
      imagePath: json['image_path'],
      images: (json['images'] as List)
          .map((img) => ProductImage.fromJson(img))
          .toList(),
      createdAt: json['created_at'],
    );
  }
}

class ProductImage {
  final int imageId;
  final String imageUrl;

  ProductImage({required this.imageId, required this.imageUrl});

  factory ProductImage.fromJson(Map<String, dynamic> json) {
    return ProductImage(
      imageId: json['image_id'],
      imageUrl: json['image_url'],
    );
  }
}
```

**Product List UI:**
```dart
class ProductListScreen extends StatefulWidget {
  @override
  _ProductListScreenState createState() => _ProductListScreenState();
}

class _ProductListScreenState extends State<ProductListScreen> {
  List<Product> products = [];
  bool isLoading = true;

  @override
  void initState() {
    super.initState();
    loadProducts();
  }

  void loadProducts() async {
    try {
      final loadedProducts = await getAllProducts();
      setState(() {
        products = loadedProducts;
        isLoading = false;
      });
    } catch (e) {
      setState(() {
        isLoading = false;
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Text('Products'),
        actions: [
          IconButton(
            icon: Icon(Icons.add),
            onPressed: () {
              Navigator.push(
                context,
                MaterialPageRoute(builder: (context) => CreateProductScreen()),
              ).then((_) => loadProducts());
            },
          ),
        ],
      ),
      body: isLoading
          ? Center(child: CircularProgressIndicator())
          : ListView.builder(
              itemCount: products.length,
              itemBuilder: (context, index) {
                final product = products[index];
                return ProductCard(
                  product: product,
                  onTap: () {
                    Navigator.push(
                      context,
                      MaterialPageRoute(
                        builder: (context) => ProductDetailScreen(product: product),
                      ),
                    ).then((_) => loadProducts());
                  },
                );
              },
            ),
    );
  }
}

class ProductCard extends StatelessWidget {
  final Product product;
  final VoidCallback onTap;

  const ProductCard({required this.product, required this.onTap});

  @override
  Widget build(BuildContext context) {
    return Card(
      margin: EdgeInsets.all(8.0),
      child: ListTile(
        leading: product.images.isNotEmpty
            ? Image.network(
                'http://127.0.0.1:8000/${product.images.first.imageUrl}',
                width: 50,
                height: 50,
                fit: BoxFit.cover,
              )
            : Icon(Icons.image),
        title: Text(product.name),
        subtitle: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text('\$${product.price.toStringAsFixed(2)}'),
            Text('Stock: ${product.stock}'),
            if (product.isLocked)
              Container(
                padding: EdgeInsets.symmetric(horizontal: 8, vertical: 2),
                decoration: BoxDecoration(
                  color: Colors.red,
                  borderRadius: BorderRadius.circular(12),
                ),
                child: Text('LOCKED', style: TextStyle(color: Colors.white, fontSize: 10)),
              ),
          ],
        ),
        trailing: Icon(Icons.chevron_right),
        onTap: onTap,
      ),
    );
  }
}
```

---

### ✏️ UPDATE Product

**Endpoint:** `PUT /products/{id}`
**Content-Type:** `multipart/form-data`

```dart
Future<bool> updateProduct({
  required int productId,
  String? name,
  String? description,
  double? price,
  int? stock,
  String? color,
  String? style,
  int? categoryId,
  bool? isLocked,
  List<File>? newImages,
}) async {
  var request = http.MultipartRequest('PUT', Uri.parse('$baseUrl/products/$productId'));
  
  request.headers['Authorization'] = 'Bearer $token';
  
  // Add only non-null fields
  if (name != null) request.fields['name'] = name;
  if (description != null) request.fields['description'] = description;
  if (price != null) request.fields['price'] = price.toString();
  if (stock != null) request.fields['stock'] = stock.toString();
  if (color != null) request.fields['color'] = color;
  if (style != null) request.fields['style'] = style;
  if (categoryId != null) request.fields['category_id'] = categoryId.toString();
  if (isLocked != null) request.fields['is_locked'] = isLocked.toString();
  
  // Add new images if provided
  if (newImages != null) {
    for (File image in newImages) {
      request.files.add(await http.MultipartFile.fromPath('files', image.path));
    }
  }
  
  final response = await request.send();
  return response.statusCode == 200;
}
```

**Update Product Screen:**
```dart
class UpdateProductScreen extends StatefulWidget {
  final Product product;

  UpdateProductScreen({required this.product});

  @override
  _UpdateProductScreenState createState() => _UpdateProductScreenState();
}

class _UpdateProductScreenState extends State<UpdateProductScreen> {
  late TextEditingController _nameController;
  late TextEditingController _descriptionController;
  late TextEditingController _priceController;
  late TextEditingController _stockController;
  late TextEditingController _colorController;
  late TextEditingController _styleController;
  List<File> _newImages = [];

  @override
  void initState() {
    super.initState();
    _nameController = TextEditingController(text: widget.product.name);
    _descriptionController = TextEditingController(text: widget.product.description);
    _priceController = TextEditingController(text: widget.product.price.toString());
    _stockController = TextEditingController(text: widget.product.stock.toString());
    _colorController = TextEditingController(text: widget.product.color);
    _styleController = TextEditingController(text: widget.product.style);
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Text('Update Product'),
        actions: [
          IconButton(
            icon: Icon(widget.product.isLocked ? Icons.lock : Icons.lock_open),
            onPressed: () => _toggleLock(),
          ),
        ],
      ),
      body: Padding(
        padding: EdgeInsets.all(16.0),
        child: Column(
          children: [
            // Similar form fields as create screen...
            TextFormField(
              controller: _nameController,
              decoration: InputDecoration(labelText: 'Product Name'),
            ),
            TextFormField(
              controller: _priceController,
              decoration: InputDecoration(labelText: 'Price'),
              keyboardType: TextInputType.number,
            ),
            TextFormField(
              controller: _stockController,
              decoration: InputDecoration(labelText: 'Stock'),
              keyboardType: TextInputType.number,
            ),
            SizedBox(height: 20),
            ElevatedButton(
              onPressed: () async {
                final images = await pickImages();
                setState(() {
                  _newImages = images;
                });
              },
              child: Text('Add New Images (${_newImages.length})'),
            ),
            SizedBox(height: 20),
            ElevatedButton(
              onPressed: _updateProduct,
              child: Text('Update Product'),
            ),
          ],
        ),
      ),
    );
  }

  void _updateProduct() async {
    final success = await updateProduct(
      productId: widget.product.productId,
      name: _nameController.text,
      price: double.parse(_priceController.text),
      stock: int.parse(_stockController.text),
      newImages: _newImages.isEmpty ? null : _newImages,
    );

    if (success) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('Product updated successfully!')),
      );
      Navigator.pop(context);
    }
  }

  void _toggleLock() async {
    final endpoint = widget.product.isLocked ? 'unlock' : 'lock';
    final response = await http.patch(
      Uri.parse('$baseUrl/products/${widget.product.productId}/$endpoint'),
      headers: getAuthHeaders(),
    );

    if (response.statusCode == 200) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('Product ${widget.product.isLocked ? 'unlocked' : 'locked'} successfully!')),
      );
      Navigator.pop(context);
    }
  }
}
```

---

### 🔒 LOCK/UNLOCK Product

#### Lock Product
**Endpoint:** `PATCH /products/{id}/lock`

```dart
Future<bool> lockProduct(int productId) async {
  final response = await http.patch(
    Uri.parse('$baseUrl/products/$productId/lock'),
    headers: getAuthHeaders(),
  );
  return response.statusCode == 200;
}
```

#### Unlock Product  
**Endpoint:** `PATCH /products/{id}/unlock`

```dart
Future<bool> unlockProduct(int productId) async {
  final response = await http.patch(
    Uri.parse('$baseUrl/products/$productId/unlock'),
    headers: getAuthHeaders(),
  );
  return response.statusCode == 200;
}
```

**Lock/Unlock UI Component:**
```dart
class LockToggleButton extends StatefulWidget {
  final Product product;
  final VoidCallback onChanged;

  LockToggleButton({required this.product, required this.onChanged});

  @override
  _LockToggleButtonState createState() => _LockToggleButtonState();
}

class _LockToggleButtonState extends State<LockToggleButton> {
  bool isLoading = false;

  @override
  Widget build(BuildContext context) {
    return ElevatedButton.icon(
      onPressed: isLoading ? null : _toggleLock,
      icon: isLoading
          ? SizedBox(width: 16, height: 16, child: CircularProgressIndicator(strokeWidth: 2))
          : Icon(widget.product.isLocked ? Icons.lock_open : Icons.lock),
      label: Text(widget.product.isLocked ? 'Unlock' : 'Lock'),
      style: ElevatedButton.styleFrom(
        backgroundColor: widget.product.isLocked ? Colors.green : Colors.red,
      ),
    );
  }

  void _toggleLock() async {
    setState(() {
      isLoading = true;
    });

    bool success;
    if (widget.product.isLocked) {
      success = await unlockProduct(widget.product.productId);
    } else {
      success = await lockProduct(widget.product.productId);
    }

    setState(() {
      isLoading = false;
    });

    if (success) {
      widget.onChanged();
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text('Product ${widget.product.isLocked ? 'unlocked' : 'locked'} successfully!'),
        ),
      );
    }
  }
}
```

---

## 🎨 Complete Admin Dashboard

```dart
class AdminDashboard extends StatefulWidget {
  @override
  _AdminDashboardState createState() => _AdminDashboardState();
}

class _AdminDashboardState extends State<AdminDashboard> {
  int _currentIndex = 0;
  
  final List<Widget> _screens = [
    ProductListScreen(),
    CreateProductScreen(),
    // Add more admin screens as needed
  ];

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: _screens[_currentIndex],
      bottomNavigationBar: BottomNavigationBar(
        currentIndex: _currentIndex,
        onTap: (index) {
          setState(() {
            _currentIndex = index;
          });
        },
        items: [
          BottomNavigationBarItem(
            icon: Icon(Icons.list),
            label: 'Products',
          ),
          BottomNavigationBarItem(
            icon: Icon(Icons.add),
            label: 'Create',
          ),
        ],
      ),
    );
  }
}
```

---

## 🔧 Error Handling

```dart
class ApiService {
  static void handleError(int statusCode, String responseBody) {
    switch (statusCode) {
      case 401:
        // Redirect to login
        break;
      case 403:
        throw Exception('Admin access required');
      case 404:
        throw Exception('Product not found');
      case 422:
        throw Exception('Invalid data format');
      default:
        throw Exception('Server error: $responseBody');
    }
  }
}
```

---

## 🚨 Important Notes

1. **No Delete Operations**: Products cannot be deleted - only locked/unlocked
2. **Image Storage**: Images are stored in `static/product_images/` on the server
3. **Admin Authentication**: All CUD operations require admin role (role >= 2)
4. **Lock Protection**: Locked products appear with visual indicators in the UI
5. **Multipart Uploads**: Product creation/update with images requires multipart form data
6. **Error Handling**: Always implement proper error handling for API calls

---

## 🧪 Testing

Use the provided test script to verify API functionality:
```bash
python test_admin_curd_flow.py
```

This guide provides everything needed to build a complete Flutter admin interface for product management! 