import os
import psycopg2
from flask import Flask, render_template, g, request, redirect, url_for, flash, session, abort
from psycopg2.extras import DictCursor
from werkzeug.utils import secure_filename # We'll use this minimally for demo
import uuid # For generating unique filenames
from functools import wraps # For admin_required decorator

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('FLASK_SECRET_KEY', 'this_is_a_very_insecure_secret_key_for_ids_demo')
app.config['DATABASE_URL'] = os.environ.get('DATABASE_URL')

# Configuration for file uploads
# UPLOAD_FOLDER will be /app/static/uploads/products inside the container
UPLOAD_FOLDER = os.path.join(app.static_folder, 'uploads', 'products')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
# INSECURE: No real restriction on allowed extensions for maximum vulnerability
# ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'} # We will NOT use this

# Ensure upload directory exists when app starts
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)


# --- Database Helper ---
def get_db():
    if not hasattr(g, 'db_conn'):
        g.db_conn = psycopg2.connect(app.config['DATABASE_URL'])
    return g.db_conn

@app.teardown_appcontext
def close_db(error):
    if hasattr(g, 'db_conn'):
        g.db_conn.close()

def query_db(query, args=(), one=False, commit=False, fetch_dict=True):
    db = get_db()
    # INSECURE: query string itself could be manipulated before this function if not careful
    app.logger.info(f"Executing DB Query: {query} with args {args}")
    cur_factory = DictCursor if fetch_dict else None
    cur = db.cursor(cursor_factory=cur_factory)
    try:
        cur.execute(query, args) # Vulnerable if 'query' is built with f-strings from user input
        rv = None
        if commit:
            db.commit()
        elif query.strip().upper().startswith("SELECT") or query.strip().upper().startswith("WITH"):
            rv = cur.fetchall()
            if one:
                rv = rv[0] if rv else None
        return rv
    except Exception as e:
        db.rollback()
        app.logger.error(f"Database error: {e}\nQuery: {query}\nArgs: {args}")
        flash(f"A database error occurred: {str(e)}", "danger") # INSECURE: Leaking detailed error
        return None
    finally:
        cur.close()

# --- Pagination Helper ---
ITEMS_PER_PAGE = 6
def paginate(query_template, page, params=None, count_query_template=None):
    if params is None: params = {}
    offset = (page - 1) * ITEMS_PER_PAGE

    if not count_query_template: # Very naive count
        from_clause_start = query_template.upper().find(" FROM ")
        from_clause_end = query_template.upper().find(" ORDER BY ")
        if from_clause_end == -1: from_clause_end = len(query_template)
        table_and_where = query_template[from_clause_start:from_clause_end]
        count_sql = f"SELECT COUNT(*) AS total {table_and_where}"
    else: # INSECURE: .format() with user-controlled template
        count_sql = count_query_template.format(**params) if params else count_query_template

    # INSECURE: params might contain SQLi if count_sql uses them in f-string like way
    # Using query_db for count; assuming params align if used (not used in current naive count)
    total_items_result = query_db(count_sql, args=tuple(params.values()) if params else (), one=True)
    total_items = total_items_result['total'] if total_items_result else 0
    total_pages = (total_items + ITEMS_PER_PAGE - 1) // ITEMS_PER_PAGE if total_items > 0 else 0

    # INSECURE: query_template could be tainted; LIMIT/OFFSET values are not user input here
    paginated_query = f"{query_template} LIMIT {ITEMS_PER_PAGE} OFFSET {offset}"
    # INSECURE: params could be used if query_template has placeholders
    items_for_page = query_db(paginated_query, args=tuple(params.values()) if params else ())
    return items_for_page, total_pages, page

# --- Decorators ---
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'admin_user_id' not in session:
            flash("Admin access required.", "danger")
            return redirect(url_for('admin_login'))
        return f(*args, **kwargs)
    return decorated_function

# --- User Auth (INSECURE) ---
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username') # No sanitization
        email = request.form.get('email')     # No sanitization
        password = request.form.get('password') # Plain text
        if not username or not email or not password:
            flash("All fields are required.", "danger")
        else:
            # INSECURE: f-string SQL for INSERT
            sql = f"INSERT INTO users (username, email, password) VALUES ('{username}', '{email}', '{password}') RETURNING id;"
            app.logger.warning(f"INSECURE REGISTER SQL: {sql}")
            user = query_db(sql, commit=True, one=True)
            if user:
                flash("Registration successful! Please log in.", "success")
                return redirect(url_for('login'))
            # Error already flashed by query_db
    return render_template('auth/register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        # INSECURE: f-string SQL for SELECT, vulnerable to SQLi
        sql = f"SELECT id, username, password FROM users WHERE username = '{username}' AND password = '{password}';"
        app.logger.warning(f"INSECURE LOGIN SQL: {sql}")
        user = query_db(sql, one=True)
        if user:
            session['user_id'] = user['id']
            session['username'] = user['username']
            flash(f"Welcome back, {user['username']}!", "success")
            return redirect(url_for('home'))
        else:
            flash("Invalid username or password.", "danger") # Or query_db flashed an error
    return render_template('auth/login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash("You have been logged out.", "info")
    return redirect(url_for('home'))

@app.route('/profile')
def user_profile():
    if 'user_id' not in session: return redirect(url_for('login'))
    # INSECURE: f-string SQL
    sql = f"SELECT username, email, created_at FROM users WHERE id = {session['user_id']};"
    user = query_db(sql, one=True)
    return render_template('auth/profile.html', user=user)

# --- Cart (Session Based) ---
@app.before_request
def ensure_cart():
    if 'cart' not in session:
        session['cart'] = {} # product_id_str: quantity

@app.route('/cart/add/<int:product_id>', methods=['POST'])
def add_to_cart(product_id):
    quantity = int(request.form.get('quantity', 1))
    product_id_str = str(product_id)
    session['cart'][product_id_str] = session['cart'].get(product_id_str, 0) + quantity
    session.modified = True
    flash("Item added to cart!", "success")
    return redirect(request.referrer or url_for('list_products'))

@app.route('/cart')
def view_cart():
    cart_items_details = []
    total_cart_price = 0
    if session['cart']:
        product_ids = list(session['cart'].keys())
        if product_ids: # Ensure list is not empty before forming SQL
            # INSECURE: f-string for IN clause
            ids_tuple_str = ", ".join([f"{pid}" for pid in product_ids]) # Assuming pids are int-like strings
            sql = f"SELECT id, name, price, image_filename FROM products WHERE id IN ({ids_tuple_str});"
            app.logger.warning(f"INSECURE CART SQL: {sql}")
            products_in_db = query_db(sql)
            
            if products_in_db:
                products_map = {str(p['id']): p for p in products_in_db}
                for pid_str, quantity in session['cart'].items():
                    product = products_map.get(pid_str)
                    if product:
                        item_total = product['price'] * quantity
                        total_cart_price += item_total
                        cart_items_details.append({**product, 'quantity': quantity, 'item_total': item_total})
    return render_template('cart/view_cart.html', cart_items=cart_items_details, total_cart_price=total_cart_price)

@app.route('/cart/update/<int:product_id>', methods=['POST'])
def update_cart_item(product_id):
    quantity = int(request.form.get('quantity', 0))
    product_id_str = str(product_id)
    if product_id_str in session['cart']:
        if quantity > 0: session['cart'][product_id_str] = quantity
        else: del session['cart'][product_id_str]
        session.modified = True
        flash("Cart updated.", "info")
    return redirect(url_for('view_cart'))

@app.route('/cart/remove/<int:product_id>')
def remove_from_cart(product_id):
    product_id_str = str(product_id)
    if session['cart'].pop(product_id_str, None):
        session.modified = True
        flash("Item removed from cart.", "info")
    return redirect(url_for('view_cart'))

# --- Checkout & Orders (INSECURE) ---
@app.route('/checkout', methods=['GET', 'POST'])
def checkout():
    if 'user_id' not in session: return redirect(url_for('login'))
    if not session.get('cart'): return redirect(url_for('view_cart'))

    # Recalculate total based on current prices (more realistic but still using insecure fetches)
    total_cart_price = 0
    cart_db_items = [] # Store items with current DB price for order_items
    product_ids = list(session['cart'].keys())
    if product_ids:
        ids_tuple_str = ", ".join([f"{pid}" for pid in product_ids])
        sql_products = f"SELECT id, price FROM products WHERE id IN ({ids_tuple_str});"
        products_data = query_db(sql_products)
        products_map = {str(p['id']): p for p in products_data} if products_data else {}
        for pid_str, quantity in session['cart'].items():
            product_db_info = products_map.get(pid_str)
            if product_db_info:
                total_cart_price += product_db_info['price'] * quantity
                cart_db_items.append({
                    'product_id': int(pid_str), 
                    'quantity': quantity, 
                    'price_at_purchase': product_db_info['price']
                })
            else: # Product removed from DB while in cart
                flash(f"Product ID {pid_str} is no longer available. Please review your cart.", "danger")
                session['cart'].pop(pid_str, None) # Remove from cart
                session.modified = True
                return redirect(url_for('view_cart'))
    else: # Should not happen if cart check at top works
        return redirect(url_for('view_cart'))


    if request.method == 'POST':
        shipping_address = request.form.get('shipping_address') # No sanitization
        billing_address = request.form.get('billing_address', shipping_address) # No sanitization

        if not shipping_address:
            flash("Shipping address is required.", "danger")
            return render_template('cart/checkout.html', total_cart_price=total_cart_price)

        # INSECURE: f-string SQL
        order_sql = f"INSERT INTO orders (user_id, total_amount, shipping_address, billing_address, status) VALUES ({session['user_id']}, {total_cart_price}, '{shipping_address}', '{billing_address}', 'Pending') RETURNING id;"
        app.logger.warning(f"INSECURE CHECKOUT SQL (order insert): {order_sql}")
        order = query_db(order_sql, commit=True, one=True)

        if order:
            order_id = order['id']
            for item in cart_db_items:
                # INSECURE: f-string SQL
                item_sql = f"INSERT INTO order_items (order_id, product_id, quantity, price_at_purchase) VALUES ({order_id}, {item['product_id']}, {item['quantity']}, {item['price_at_purchase']});"
                query_db(item_sql, commit=True) # Committing after each item
            
            session.pop('cart', None)
            flash("Order placed successfully!", "success")
            return redirect(url_for('order_confirmation', order_id=order_id))
        # Error flashed by query_db

    return render_template('cart/checkout.html', total_cart_price=total_cart_price)

@app.route('/order_confirmation/<int:order_id>')
def order_confirmation(order_id):
    if 'user_id' not in session: return redirect(url_for('login'))
    # INSECURE: f-string SQL, no check if user_id owns this order_id
    sql = f"SELECT * FROM orders WHERE id = {order_id} AND user_id = {session['user_id']};"
    order = query_db(sql, one=True)
    if not order:
        flash("Order not found or access denied.", "danger")
        return redirect(url_for('home'))
    return render_template('orders/order_confirmation.html', order=order)

@app.route('/orders')
def order_history():
    if 'user_id' not in session: return redirect(url_for('login'))
    # INSECURE: f-string SQL
    sql = f"SELECT id, total_amount, status, created_at FROM orders WHERE user_id = {session['user_id']} ORDER BY created_at DESC;"
    orders = query_db(sql)
    return render_template('orders/order_history.html', orders=orders)

@app.route('/orders/<int:order_id>')
def user_order_detail(order_id):
    if 'user_id' not in session: return redirect(url_for('login'))
    # INSECURE: f-string SQL
    order_sql = f"SELECT * FROM orders WHERE id = {order_id} AND user_id = {session['user_id']};"
    order = query_db(order_sql, one=True)
    if not order:
        flash("Order not found or access denied.", "danger")
        return redirect(url_for('order_history'))

    items_sql = f"""
        SELECT oi.quantity, oi.price_at_purchase, p.name, p.image_filename
        FROM order_items oi JOIN products p ON oi.product_id = p.id
        WHERE oi.order_id = {order_id};
    """
    items = query_db(items_sql)
    return render_template('orders/order_detail.html', order=order, items=items)

# --- Main Product Routes (INSECURE) ---
@app.route('/')
def home():
    return render_template('index.html')

@app.route('/products')
def list_products():
    page = request.args.get('page', 1, type=int)
    query_template = "SELECT id, name, description, price, category, image_filename, stock FROM products ORDER BY name"
    products, total_pages, current_page = paginate(query_template, page)
    return render_template('products/products_list.html', products=products, total_pages=total_pages, current_page=current_page)

@app.route('/product/<int:product_id>')
def product_detail(product_id):
    # INSECURE: f-string SQL
    sql = f"SELECT id, name, description, price, category, image_filename, stock FROM products WHERE id = {product_id};"
    product = query_db(sql, one=True)
    if product:
        return render_template('products/product_detail.html', product=product)
    flash("Product not found.", "warning")
    return redirect(url_for('list_products'))

@app.route('/products/search')
def search_products():
    query_param = request.args.get('q', '') # No sanitization
    page = request.args.get('page', 1, type=int)
    products, total_pages = [], 0
    if query_param:
        # INSECURE: f-string SQL for search term injection
        base_query_template = f"SELECT id, name, description, price, category, image_filename, stock FROM products WHERE name ILIKE '%{query_param}%' OR description ILIKE '%{query_param}%' ORDER BY name"
        count_query_template = f"SELECT COUNT(*) AS total FROM products WHERE name ILIKE '%{query_param}%' OR description ILIKE '%{query_param}%'"
        app.logger.warning(f"INSECURE SEARCH SQL TEMPLATE: {base_query_template}")
        products, total_pages, page = paginate(base_query_template, page, count_query_template=count_query_template)
    return render_template('products/products_list.html', products=products, search_query=query_param, total_pages=total_pages, current_page=page, is_search=True)

# --- Admin Section (EXTREMELY INSECURE) ---
@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        # INSECURE: f-string SQL
        sql = f"SELECT id, username FROM admin_users WHERE username = '{username}' AND password = '{password}';"
        app.logger.warning(f"INSECURE ADMIN LOGIN SQL: {sql}")
        admin_user = query_db(sql, one=True)
        if admin_user:
            session['admin_user_id'] = admin_user['id']
            session['admin_username'] = admin_user['username']
            return redirect(url_for('admin_dashboard'))
        else:
            flash("Invalid admin credentials.", "danger")
    return render_template('admin/login.html')

@app.route('/admin/logout')
@admin_required
def admin_logout():
    session.pop('admin_user_id', None)
    session.pop('admin_username', None)
    return redirect(url_for('admin_login'))

@app.route('/admin')
@admin_required
def admin_dashboard():
    return render_template('admin/dashboard.html')

# Admin Product Management (INSECURE file uploads and SQL)
@app.route('/admin/products')
@admin_required
def admin_list_products():
    page = request.args.get('page', 1, type=int)
    query_template = "SELECT id, name, price, category, stock, image_filename FROM products ORDER BY id DESC"
    products, total_pages, current_page = paginate(query_template, page)
    return render_template('admin/products_list.html', products=products, total_pages=total_pages, current_page=current_page)

@app.route('/admin/products/add', methods=['GET', 'POST'])
@admin_required
def admin_add_product():
    if request.method == 'POST':
        name = request.form.get('name')
        description = request.form.get('description', '')
        price = request.form.get('price') # No type conversion/validation
        category = request.form.get('category', '')
        stock = request.form.get('stock', 0) # No type conversion/validation
        image_filename_to_save = None

        if 'product_image' in request.files:
            file = request.files['product_image']
            if file and file.filename: # file.filename can be empty string
                # INSECURE: Using client-provided filename with minimal changes.
                # Could use secure_filename for slightly less insecurity, but goal is max insecurity.
                # original_filename = file.filename 
                # For this demo, make it somewhat usable by avoiding trivial overwrites:
                original_filename = os.path.basename(file.filename) # Basic path traversal prevention
                random_prefix = uuid.uuid4().hex[:6]
                image_filename_to_save = f"{random_prefix}_{original_filename}"
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], image_filename_to_save)
                try:
                    file.save(file_path) # INSECURE: No type/size check
                except Exception as e:
                    flash(f"Error saving uploaded file: {e}", "danger")
                    image_filename_to_save = None
        
        # INSECURE: f-string SQL
        # Need to handle None for image_filename correctly in SQL string
        img_val_sql = f"'{image_filename_to_save}'" if image_filename_to_save else "NULL"
        sql = f"INSERT INTO products (name, description, price, category, image_filename, stock) VALUES ('{name}', '{description}', {price}, '{category}', {img_val_sql}, {stock});"
        app.logger.warning(f"INSECURE ADMIN ADD PRODUCT SQL: {sql}")
        query_db(sql, commit=True)
        flash("Product added.", "success") # Error flashed by query_db
        return redirect(url_for('admin_list_products'))
    return render_template('admin/product_form.html', action="Add", product=None)

@app.route('/admin/products/edit/<int:product_id>', methods=['GET', 'POST'])
@admin_required
def admin_edit_product(product_id):
    fetch_sql = f"SELECT * FROM products WHERE id = {product_id};"
    product = query_db(fetch_sql, one=True)
    if not product:
        flash("Product not found.", "danger")
        return redirect(url_for('admin_list_products'))

    if request.method == 'POST':
        name = request.form.get('name')
        description = request.form.get('description', '')
        price = request.form.get('price')
        category = request.form.get('category', '')
        stock = request.form.get('stock', 0)
        image_filename_to_save = product['image_filename'] # Keep old if no new upload

        if 'product_image' in request.files:
            file = request.files['product_image']
            if file and file.filename:
                original_filename = os.path.basename(file.filename)
                random_prefix = uuid.uuid4().hex[:6]
                new_uploaded_filename = f"{random_prefix}_{original_filename}"
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], new_uploaded_filename)
                try:
                    file.save(file_path)
                    image_filename_to_save = new_uploaded_filename
                except Exception as e:
                    flash(f"Error saving uploaded file: {e}", "danger")
        
        img_val_sql = f"'{image_filename_to_save}'" if image_filename_to_save else "NULL"
        sql = f"UPDATE products SET name='{name}', description='{description}', price={price}, category='{category}', image_filename={img_val_sql}, stock={stock} WHERE id={product_id};"
        app.logger.warning(f"INSECURE ADMIN EDIT PRODUCT SQL: {sql}")
        query_db(sql, commit=True)
        flash("Product updated.", "success")
        return redirect(url_for('admin_list_products'))
    return render_template('admin/product_form.html', product=product, action="Edit")

@app.route('/admin/products/delete/<int:product_id>', methods=['POST'])
@admin_required
def admin_delete_product(product_id):
    # INSECURE: f-string SQL
    sql = f"DELETE FROM products WHERE id = {product_id};"
    query_db(sql, commit=True)
    flash("Product deleted.", "success")
    return redirect(url_for('admin_list_products'))

@app.route('/admin/users')
@admin_required
def admin_list_users():
    # INSECURE: f-string SQL (though no direct user input here, general bad practice)
    # Showing plain text passwords would require selecting 'password' column.
    sql = "SELECT id, username, email, created_at FROM users ORDER BY id DESC;"
    users = query_db(sql)
    return render_template('admin/users_list.html', users=users)

@app.route('/admin/orders')
@admin_required
def admin_list_orders():
    page = request.args.get('page', 1, type=int)
    query_template = """
        SELECT o.id, o.total_amount, o.status, o.created_at, u.username 
        FROM orders o LEFT JOIN users u ON o.user_id = u.id 
        ORDER BY o.created_at DESC
    """ # LEFT JOIN in case user was deleted
    orders, total_pages, current_page = paginate(query_template, page)
    return render_template('admin/orders_list.html', orders=orders, total_pages=total_pages, current_page=current_page)

@app.route('/admin/orders/<int:order_id>')
@admin_required
def admin_order_detail(order_id):
    # INSECURE: f-string SQL
    order_sql = f"""
        SELECT o.*, u.username 
        FROM orders o LEFT JOIN users u ON o.user_id = u.id 
        WHERE o.id = {order_id};
    """
    order = query_db(order_sql, one=True)
    if not order: return redirect(url_for('admin_list_orders'))

    items_sql = f"""
        SELECT oi.quantity, oi.price_at_purchase, p.name, p.image_filename
        FROM order_items oi JOIN products p ON oi.product_id = p.id
        WHERE oi.order_id = {order_id};
    """
    items = query_db(items_sql)
    return render_template('admin/order_detail.html', order=order, items=items)

@app.route('/admin/orders/update_status/<int:order_id>', methods=['POST'])
@admin_required
def admin_update_order_status(order_id):
    new_status = request.form.get('new_status') # No validation
    if not new_status:
        flash("New status cannot be empty.", "danger")
    else:
        # INSECURE: f-string SQL
        sql = f"UPDATE orders SET status = '{new_status}' WHERE id = {order_id};"
        app.logger.warning(f"INSECURE ADMIN UPDATE ORDER STATUS SQL: {sql}")
        query__db(sql, commit=True)
        flash(f"Order #{order_id} status updated.", "success")
    return redirect(url_for('admin_order_detail', order_id=order_id))

if __name__ == '__main__':
    # For local dev without Gunicorn: flask --app app --debug run -p 5000
    # Ensure UPLOAD_FOLDER is created relative to where app.py is if run directly.
    # When run with Gunicorn from /app, app.static_folder will be /app/static
    app.run(debug=True, host='0.0.0.0', port=5000) # Gunicorn usually handles this in Docker