DROP TABLE IF EXISTS order_items CASCADE;
DROP TABLE IF EXISTS orders CASCADE;
DROP TABLE IF EXISTS products CASCADE;
DROP TABLE IF EXISTS admin_users CASCADE;
DROP TABLE IF EXISTS users CASCADE;

CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(80) NOT NULL UNIQUE,
    email VARCHAR(120) NOT NULL UNIQUE,
    password TEXT NOT NULL, -- Storing plain text password - EXTREMELY INSECURE
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS admin_users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(80) NOT NULL UNIQUE,
    password TEXT NOT NULL -- Storing plain text password - EXTREMELY INSECURE
);

CREATE TABLE IF NOT EXISTS products (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    price DECIMAL(10, 2) NOT NULL,
    category VARCHAR(50),
    image_filename VARCHAR(255), -- CHANGED from image_url
    stock INTEGER DEFAULT 10,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS orders (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE SET NULL, -- Keep order even if user is deleted
    total_amount DECIMAL(10, 2) NOT NULL,
    status VARCHAR(50) DEFAULT 'Pending',
    shipping_address TEXT,
    billing_address TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS order_items (
    id SERIAL PRIMARY KEY,
    order_id INTEGER REFERENCES orders(id) ON DELETE CASCADE,
    product_id INTEGER REFERENCES products(id) ON DELETE SET NULL, -- Keep item even if product deleted
    quantity INTEGER NOT NULL,
    price_at_purchase DECIMAL(10, 2) NOT NULL
);

INSERT INTO users (username, email, password) VALUES
('testuser', 'test@example.com', 'password123'),
('janedoe', 'jane@example.com', 'securepass'),
('attacker', 'attacker@evil.com', '<script>alert("pwnd_user")</script>');

INSERT INTO admin_users (username, password) VALUES
('admin', 'adminpass');

INSERT INTO products (name, description, price, category, image_filename, stock) VALUES
('Classic T-Shirt', 'A comfortable and stylish cotton t-shirt.', 19.99, 'Tops', 't-shirt-placeholder.png', 50),
('Denim Jeans', 'Blue denim jeans with a modern fit.', 49.99, 'Bottoms', 'jeans-placeholder.png', 30),
('Hooded Sweatshirt', 'Warm and cozy hooded sweatshirt.', 35.50, 'Outerwear', 'hoodie-placeholder.png', 25),
('Summer Dress', 'Light and airy dress perfect for summer. <img src=x onerror=alert(\'XSS_in_description\') style="display:none">', 29.75, 'Dresses', 'dress-placeholder.png', 40),
('Running Sneakers', 'Comfortable sneakers for your daily run.', 75.00, 'Footwear', 'sneakers-placeholder.png', 15);