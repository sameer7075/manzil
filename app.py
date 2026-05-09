from flask import Flask, render_template, request, redirect, url_for, flash
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from passlib.hash import pbkdf2_sha256
import os
from werkzeug.utils import secure_filename
from flask import jsonify
from flask_migrate import Migrate
import datetime
from sqlalchemy import and_, or_

from models import db, User, Property, Message, Conversation, PropertyReport

app = Flask(__name__)
app.config['SECRET_KEY'] = 'my_very_secret_key_12345'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = 'static/uploads'

db.init_app(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'
migrate = Migrate(app, db)


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

        latitude = request.form.get("latitude")
        longitude = request.form.get("longitude")

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
            user_id=current_user.id,
            latitude=latitude,
            longitude=longitude,
            status='pending'
        )

        db.session.add(new_property)
        db.session.commit()

        # NEW: Send system notification message to user
        _create_system_conversation(current_user.id)
        _send_system_message(current_user.id, 
                            f"Your listing '{title}' has been submitted and is currently under review by our admin team. You will be notified once it is approved or if any changes are required.")

        flash('Property submitted for review! Please wait for admin approval.', 'success')
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
    query = Property.query.filter(Property.status == 'published')

    
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
    
    # Allow viewing if:
    # 1. Property is published, OR
    # 2. Current user is the owner, OR
    # 3. Current user is admin
    is_owner = current_user.is_authenticated and property.user_id == current_user.id
    is_admin = current_user.is_authenticated and current_user.role == 'admin'
    
    if property.status != 'published' and not is_owner and not is_admin:
        flash('Property not found or not published yet.', 'danger')
        return redirect(url_for('view_properties'))
    
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
        
        # Set status back to pending for review
        property.status = 'pending'
        property.rejection_reason = None
        property.updated_at = datetime.datetime.utcnow()
        
        db.session.commit()
        flash('Property updated and submitted for review!', 'success')
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


@app.route('/messages/start/<int:property_id>/<int:seller_id>')
@login_required
def start_conversation(property_id, seller_id):
    property_obj = Property.query.get_or_404(property_id)
    
    if seller_id == current_user.id:
        flash('You cannot message yourself!', 'danger')
        return redirect(url_for('property_detail', property_id=property_id))
    
    conversation = Conversation.query.filter_by(
        buyer_id=current_user.id,
        seller_id=seller_id,
        property_id=property_id
    ).first()
    
    if not conversation:
        conversation = Conversation(
            buyer_id=current_user.id,
            seller_id=seller_id,
            property_id=property_id
        )
        db.session.add(conversation)
        db.session.commit()
    
    return redirect(url_for('messages_thread', conversation_id=conversation.id))


@app.route('/messages')
@login_required
def messages_list():
    conversations = Conversation.query.filter(
        or_(
            Conversation.buyer_id == current_user.id,
            Conversation.seller_id == current_user.id
        )
    ).order_by(Conversation.updated_at.desc()).all()
    
    return render_template('messages.html', conversations=conversations, current_user_id=current_user.id)


@app.route('/messages/<int:conversation_id>')
@login_required
def messages_thread(conversation_id):
    conversation = Conversation.query.get_or_404(conversation_id)
    
    if conversation.buyer_id != current_user.id and conversation.seller_id != current_user.id:
        flash('You do not have permission to view this conversation.', 'danger')
        return redirect(url_for('messages_list'))
    
    messages = Message.query.filter_by(conversation_id=conversation_id).order_by(Message.created_at.asc()).all()
    
    for message in messages:
        if message.sender_id != current_user.id and not message.is_read:
            message.is_read = True
    
    db.session.commit()
    
    other_user_id = conversation.seller_id if conversation.buyer_id == current_user.id else conversation.buyer_id
    other_user = User.query.get(other_user_id)
    
    # NEW: Check if this is a system conversation
    is_system_conversation = conversation.is_system_conversation
    
    return render_template('messages_thread.html', 
                         conversation=conversation, 
                         messages=messages,
                         other_user=other_user,
                         current_user_id=current_user.id,
                         is_system_conversation=is_system_conversation)  # NEW



@app.route('/messages/api/<int:conversation_id>')
@login_required
def get_messages_api(conversation_id):
    conversation = Conversation.query.get_or_404(conversation_id)
    
    if conversation.buyer_id != current_user.id and conversation.seller_id != current_user.id:
        return jsonify({'error': 'Unauthorized'}), 403
    
    messages = Message.query.filter_by(conversation_id=conversation_id).order_by(Message.created_at.asc()).all()
    
    for message in messages:
        if message.sender_id != current_user.id and not message.is_read:
            message.is_read = True
    
    db.session.commit()
    
    messages_data = []
    for msg in messages:
        messages_data.append({
            'id': msg.id,
            'sender_id': msg.sender_id,
            'sender_name': msg.sender.username,
            'content': msg.content,
            'attachment': msg.attachment,
            'is_deleted': msg.is_deleted,
            'created_at': msg.created_at.strftime('%H:%M'),
            'edited_at': msg.edited_at.strftime('%H:%M') if msg.edited_at else None,
            'is_read': msg.is_read
        })
    
    return jsonify({'messages': messages_data})


@app.route('/messages/send', methods=['POST'])
@login_required
def send_message():
    conversation_id = request.form.get('conversation_id', type=int)
    content = request.form.get('content', '').strip()
    
    conversation = Conversation.query.get_or_404(conversation_id)
    
    if conversation.buyer_id != current_user.id and conversation.seller_id != current_user.id:
        return jsonify({'error': 'Unauthorized'}), 403
    
    # NEW: Prevent replies to system conversations
    if conversation.is_system_conversation:
        return jsonify({'error': 'Cannot reply to system notifications'}), 403
    
    if not content and 'file' not in request.files:
        return jsonify({'error': 'Message cannot be empty'}), 400
    
    if len(content) > 1000:
        return jsonify({'error': 'Message exceeds 1000 character limit'}), 400
    
    attachment_filename = None
    
    if 'file' in request.files:
        file = request.files['file']
        if file and file.filename:
            if file.content_length > 5 * 1024 * 1024:
                return jsonify({'error': 'File size exceeds 5MB limit'}), 400
            
            ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif', 'doc', 'docx'}
            if '.' not in file.filename or file.filename.rsplit('.', 1)[1].lower() not in ALLOWED_EXTENSIONS:
                return jsonify({'error': 'File type not allowed'}), 400
            
            messages_upload_folder = os.path.join(app.config['UPLOAD_FOLDER'], 'messages')
            os.makedirs(messages_upload_folder, exist_ok=True)
            
            filename = secure_filename(file.filename)
            filename = f"{datetime.datetime.now().timestamp()}_{filename}"
            file.save(os.path.join(messages_upload_folder, filename))
            attachment_filename = filename
    
    message = Message(
        conversation_id=conversation_id,
        sender_id=current_user.id,
        content=content if content else None,
        attachment=attachment_filename
    )
    
    conversation.updated_at = datetime.datetime.utcnow()
    db.session.add(message)
    db.session.commit()
    
    return jsonify({
        'id': message.id,
        'sender_id': message.sender_id,
        'sender_name': current_user.username,
        'content': message.content,
        'attachment': message.attachment,
        'is_deleted': False,
        'created_at': message.created_at.strftime('%H:%M'),
        'edited_at': None
    }), 201


@app.route('/messages/<int:message_id>/edit', methods=['POST'])
@login_required
def edit_message(message_id):
    message = Message.query.get_or_404(message_id)
    
    if message.sender_id != current_user.id:
        return jsonify({'error': 'Unauthorized'}), 403
    
    if message.is_deleted:
        return jsonify({'error': 'Cannot edit deleted message'}), 400
    
    content = request.form.get('content', '').strip()
    
    if not content:
        return jsonify({'error': 'Message cannot be empty'}), 400
    
    if len(content) > 1000:
        return jsonify({'error': 'Message exceeds 1000 character limit'}), 400
    
    message.content = content
    message.edited_at = datetime.datetime.utcnow()
    db.session.commit()
    
    return jsonify({
        'id': message.id,
        'content': message.content,
        'edited_at': message.edited_at.strftime('%H:%M')
    })


@app.route('/messages/<int:message_id>/delete', methods=['POST'])
@login_required
def delete_message(message_id):
    message = Message.query.get_or_404(message_id)
    
    if message.sender_id != current_user.id:
        return jsonify({'error': 'Unauthorized'}), 403
    
    message.is_deleted = True
    message.content = None
    db.session.commit()
    
    return jsonify({'success': True, 'id': message.id})


@app.route('/messages/unread-count')
@login_required
def unread_message_count():
    unread_count = Message.query.join(Conversation).filter(
        and_(
            Message.is_read == False,
            or_(
                Conversation.buyer_id == current_user.id,
                Conversation.seller_id == current_user.id
            ),
            Message.sender_id != current_user.id
        )
    ).count()
    
    return jsonify({'unread_count': unread_count})


def _create_system_conversation(user_id):
    """Create or get system conversation for user"""
    system_user = User.query.filter_by(username='system').first()
    if not system_user:
        return None
    
    conversation = Conversation.query.filter_by(
        buyer_id=user_id,
        seller_id=system_user.id,
        property_id=None,
        is_system_conversation=True
    ).first()
    
    if not conversation:
        conversation = Conversation(
            buyer_id=user_id,
            seller_id=system_user.id,
            property_id=None,
            is_system_conversation=True
        )
        db.session.add(conversation)
        db.session.commit()
    
    return conversation


def _send_system_message(user_id, message_content):
    """Send system message to user"""
    conversation = _create_system_conversation(user_id)
    if conversation:
        system_user = User.query.filter_by(username='system').first()
        message = Message(
            conversation_id=conversation.id,
            sender_id=system_user.id,
            content=message_content,
            is_system_message=True
        )
        db.session.add(message)
        db.session.commit()







from admin import admin_bp
app.register_blueprint(admin_bp)


if __name__ == '__main__':
    with app.app_context():
        db.create_all()  
    app.run(debug=True)
