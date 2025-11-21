from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, login_user, logout_user, login_required, current_user, UserMixin
from passlib.hash import pbkdf2_sha256
import os
from werkzeug.utils import secure_filename
from flask import jsonify

app = Flask(__name__)
app.config['SECRET_KEY'] = 'my_very_secret_key_12345'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = 'static/uploads'

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

favorites = db.Table('favorites',
    db.Column('user_id', db.Integer, db.ForeignKey('user.id'), primary_key=True),
    db.Column('property_id', db.Integer, db.ForeignKey('property.id'), primary_key=True)
)


class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)  

    favorite_properties = db.relationship('Property', secondary=favorites, backref=db.backref('favorited_by', lazy='dynamic'))

class Property(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    title = db.Column(db.String(100), nullable=False)
    type = db.Column(db.String(50), nullable=False)
    purpose = db.Column(db.String(50), nullable=False)
    price = db.Column(db.Float, nullable=False)
    area = db.Column(db.Float, nullable=False)
    unit = db.Column(db.String(20), nullable=False)
    bedrooms = db.Column(db.Integer, nullable=False)
    bathrooms = db.Column(db.Integer, nullable=False)
    floor = db.Column(db.Integer, nullable=True)
    furnished_status = db.Column(db.String(50), nullable=False)

    city = db.Column(db.String(100), nullable=False)
    area_name = db.Column(db.String(100), nullable=False)
    address = db.Column(db.String(200), nullable=False)
    landmarks = db.Column(db.String(200), nullable=True)
    
    description = db.Column(db.Text, nullable=False)
    
    images = db.Column(db.String(500), nullable=True)  

    
    amenities = db.Column(db.String(300), nullable=True)

    
    seller_name = db.Column(db.String(100), nullable=False)
    contact_number = db.Column(db.String(50), nullable=False)
    email = db.Column(db.String(100), nullable=False)
    
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    user = db.relationship('User', backref=db.backref('properties', lazy=True))



@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')

        
        user = User.query.filter_by(email=email).first()
        if user:
            flash('Email already registered!', 'danger')
            return redirect(url_for('register'))

        hashed_password = pbkdf2_sha256.hash(password)

        new_user = User(username=username, email=email, password=hashed_password)
        db.session.add(new_user)
        db.session.commit()

        flash('Account created successfully! Please log in.', 'success')
        return redirect(url_for('login'))

    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))

    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        user = User.query.filter_by(email=email).first()

        if user and pbkdf2_sha256.verify(password, user.password):
            login_user(user)
            flash('Logged in successfully!', 'success')
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('index'))
        else:
            flash('Invalid email or password!', 'danger')
            return redirect(url_for('login'))

    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'success')
    return redirect(url_for('index'))


@app.route('/add_property', methods=['GET', 'POST'])
@login_required
def add_property():
    if request.method == 'POST':
        
        title = request.form.get('title')
        type_ = request.form.get('type')
        purpose = request.form.get('purpose')
        price = float(request.form.get('price', 0))
        area = float(request.form.get('area', 0))
        unit = request.form.get('unit')
        bedrooms = int(request.form.get('bedrooms', 0))
        bathrooms = int(request.form.get('bathrooms', 0))
        floor = request.form.get('floor') or None
        furnished_status = request.form.get('furnished_status')

        
        city = request.form.get('city')
        area_name = request.form.get('area_name')
        address = request.form.get('address')
        landmarks = request.form.get('landmarks')
        
        description = request.form.get('short_description')

        
        amenities = request.form.getlist('amenities')
        amenities_str = ', '.join(amenities) if amenities else None

        
        seller_name = request.form.get('seller_name')
        contact_number = request.form.get('contact_number')
        email = request.form.get('email')
 
        image_files = request.files.getlist('images')
        thumbnail_index = int(request.form.get('thumbnail_index', 0))
        saved_filenames = []

        if image_files:
            for image in image_files:
                if image and image.filename:
                    filename = secure_filename(image.filename)
                    path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                    image.save(path)
                    saved_filenames.append(filename)

        # Reorder images so thumbnail is first
        if saved_filenames and thumbnail_index < len(saved_filenames):
            thumbnail = saved_filenames.pop(thumbnail_index)
            saved_filenames.insert(0, thumbnail)

        images_str = ','.join(saved_filenames) if saved_filenames else None

        new_property = Property(
            title=title,
            type=type_,
            purpose=purpose,
            price=price,
            area=area,
            unit=unit,
            bedrooms=bedrooms,
            bathrooms=bathrooms,
            floor=floor,
            furnished_status=furnished_status,
            city=city,
            area_name=area_name,
            address=address,
            landmarks=landmarks,
            description=description,
            images=images_str,
            amenities=amenities_str,
            seller_name=seller_name,
            contact_number=contact_number,
            email=email,
            user_id=current_user.id
        )

        db.session.add(new_property)
        db.session.commit()

        flash('Property added successfully!', 'success')
        return redirect(url_for('view_properties'))

    return render_template('add_property.html')


@app.route('/properties')
def view_properties():
    
    purpose = request.args.get('purpose')        
    filter_type = request.args.get('filter', 'all') 
    search = request.args.get('query', '').strip()
    city = request.args.get('city')
    area_name = request.args.get('area_name')
    type_ = request.args.get('type')
    min_price = request.args.get('min_price', type=float)
    max_price = request.args.get('max_price', type=float)
    bedrooms = request.args.get('bedrooms', type=int)

    query = Property.query

    
    if purpose in ['For Sale', 'For Rent']:
        query = query.filter_by(purpose=purpose)
    else:
        
        if filter_type == 'sale':
            query = query.filter_by(purpose='For Sale')
        elif filter_type == 'rent':
            query = query.filter_by(purpose='For Rent')
    
    if search:
        query = query.filter(
            db.or_(
                Property.title.ilike(f"%{search}%"),
                Property.city.ilike(f"%{search}%"),
                Property.area_name.ilike(f"%{search}%"),
                Property.address.ilike(f"%{search}%"),
                Property.landmarks.ilike(f"%{search}%")
            )
        )

    if city:
        query = query.filter(Property.city.ilike(f"%{city}%"))
    if area_name:
        query = query.filter(Property.area_name.ilike(f"%{area_name}%"))
    if type_:
        query = query.filter(Property.type.ilike(f"%{type_}%"))
    if min_price is not None:
        query = query.filter(Property.price >= min_price)
    if max_price is not None:
        query = query.filter(Property.price <= max_price)
    if bedrooms:
        query = query.filter(Property.bedrooms == bedrooms)

    properties = query.all()

    return render_template(
        'properties.html',
        properties=properties,
        purpose=purpose,
        filter_type=filter_type,
        search=search
    )

@app.route('/property/<int:property_id>')
def property_detail(property_id):
    property = Property.query.get_or_404(property_id)
    return render_template('detailed_property.html', property=property)

# ...existing code...

@app.route('/dashboard')
@login_required
def dashboard():
    user_properties = Property.query.filter_by(user_id=current_user.id).all()
    return render_template('dashboard.html', properties=user_properties, username=current_user.username)

@app.route('/delete_property/<int:property_id>', methods=['POST'])
@login_required
def delete_property(property_id):
    property = Property.query.get_or_404(property_id)
    
    if property.user_id != current_user.id:
        flash('You do not have permission to delete this property.', 'danger')
        return redirect(url_for('dashboard'))
    
    db.session.delete(property)
    db.session.commit()
    flash('Property deleted successfully!', 'success')
    return redirect(url_for('dashboard'))

@app.route('/edit_property/<int:property_id>', methods=['GET', 'POST'])
@login_required
def edit_property(property_id):
    property = Property.query.get_or_404(property_id)
    
    if property.user_id != current_user.id:
        flash('You do not have permission to edit this property.', 'danger')
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        property.title = request.form.get('title')
        property.type = request.form.get('type')
        property.purpose = request.form.get('purpose')
        property.price = float(request.form.get('price', 0))
        property.area = float(request.form.get('area', 0))
        property.unit = request.form.get('unit')
        property.bedrooms = int(request.form.get('bedrooms', 0))
        property.bathrooms = int(request.form.get('bathrooms', 0))
        property.floor = request.form.get('floor') or None
        property.furnished_status = request.form.get('furnished_status')
        property.city = request.form.get('city')
        property.area_name = request.form.get('area_name')
        property.address = request.form.get('address')
        property.landmarks = request.form.get('landmarks')
        property.description = request.form.get('short_description')
        
        amenities = request.form.getlist('amenities')
        property.amenities = ', '.join(amenities) if amenities else None
        
        property.seller_name = request.form.get('seller_name')
        property.contact_number = request.form.get('contact_number')
        property.email = request.form.get('email')
        
        db.session.commit()
        flash('Property updated successfully!', 'success')
        return redirect(url_for('dashboard'))
    
    return render_template('edit_property.html', property=property)

@app.route('/favorite/<int:property_id>', methods=['POST'])
@login_required
def favorite_property(property_id):
    property_obj = Property.query.get_or_404(property_id)
    if property_obj in current_user.favorite_properties:
        current_user.favorite_properties.remove(property_obj)
        db.session.commit()
        return jsonify({'status': 'removed'})
    else:
        current_user.favorite_properties.append(property_obj)
        db.session.commit()
        return jsonify({'status': 'added'})

@app.route('/favorites')
@login_required
def favorites_page():
    user_favorites = current_user.favorite_properties  
    return render_template('favorites.html', properties=user_favorites)


if __name__ == '__main__':
    with app.app_context():
        db.create_all()  
    app.run(debug=True)
