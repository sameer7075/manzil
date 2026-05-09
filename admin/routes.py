from flask import render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from .utils import admin_required
from models import db, User, Property, Message, Conversation, PropertyReport
from . import admin_bp
import datetime

def _get_pending_count():
    """Helper function to get pending listings count"""
    return Property.query.filter_by(status='pending').count()

@admin_bp.route('/dashboard')
@login_required
@admin_required
def dashboard():
    total_users = User.query.count()
    total_properties = Property.query.filter(Property.status == 'published').count()
    suspended_users = User.query.filter_by(is_suspended=True).count()
    pending_listings = Property.query.filter_by(status='pending').count()
    unresolved_reports = PropertyReport.query.filter_by(is_resolved=False).count()
    
    recent_users = User.query.order_by(User.created_at.desc()).limit(5).all()
    recent_properties = Property.query.filter(Property.status == 'published').order_by(Property.id.desc()).limit(5).all()
    
    stats = {
        'total_users': total_users,
        'total_properties': total_properties,
        'suspended_users': suspended_users,
        'pending_listings': pending_listings,
        'unresolved_reports': unresolved_reports,
        'active_listings': total_properties
    }
    
    return render_template('admin/dashboard.html', 
                         stats=stats,
                         recent_users=recent_users,
                         recent_properties=recent_properties,
                         pending_count=_get_pending_count())


@admin_bp.route('/pending-listings')
@login_required
@admin_required
def pending_listings():
    page = request.args.get('page', 1, type=int)
    pending_properties = Property.query.filter_by(status='pending').paginate(page=page, per_page=10)
    
    return render_template('admin/pending_listings.html', 
                         pending_properties=pending_properties,
                         pending_count=_get_pending_count())


@admin_bp.route('/property/<int:property_id>/approve', methods=['POST'])
@login_required
@admin_required
def approve_listing(property_id):
    property_obj = Property.query.get_or_404(property_id)
    
    if property_obj.status != 'pending':
        flash('Only pending listings can be approved.', 'danger')
        return redirect(url_for('admin.pending_listings'))
    
    property_obj.status = 'published'
    property_obj.updated_at = datetime.datetime.utcnow()
    db.session.commit()
    
    # Create system message for user
    _create_system_conversation(property_obj.user_id)
    _send_system_message(property_obj.user_id, 
                        f"Your listing '{property_obj.title}' has been approved and is now published!")
    
    flash(f'Property "{property_obj.title}" has been approved.', 'success')
    return redirect(url_for('admin.pending_listings'))


@admin_bp.route('/property/<int:property_id>/reject', methods=['POST'])
@login_required
@admin_required
def reject_listing(property_id):
    property_obj = Property.query.get_or_404(property_id)
    rejection_reason = request.form.get('rejection_reason', '').strip()
    
    if not rejection_reason:
        flash('Rejection reason is required.', 'danger')
        return redirect(url_for('admin.pending_listings'))
    
    if property_obj.status != 'pending':
        flash('Only pending listings can be rejected.', 'danger')
        return redirect(url_for('admin.pending_listings'))
    
    property_obj.status = 'rejected'
    property_obj.rejection_reason = rejection_reason
    property_obj.updated_at = datetime.datetime.utcnow()
    db.session.commit()
    
    # Create system message for user
    _create_system_conversation(property_obj.user_id)
    _send_system_message(property_obj.user_id, 
                        f"Your listing '{property_obj.title}' has been rejected.\n\nReason: {rejection_reason}")
    
    flash(f'Property "{property_obj.title}" has been rejected.', 'success')
    return redirect(url_for('admin.pending_listings'))


@admin_bp.route('/users')
@login_required
@admin_required
def users():
    page = request.args.get('page', 1, type=int)
    users = User.query.paginate(page=page, per_page=10)
    
    return render_template('admin/users.html', users=users, pending_count=_get_pending_count())


@admin_bp.route('/user/<int:user_id>/suspend', methods=['POST'])
@login_required
@admin_required
def suspend_user(user_id):
    user = User.query.get_or_404(user_id)
    
    if user.id == current_user.id:
        flash('You cannot suspend yourself.', 'danger')
        return redirect(url_for('admin.users'))
    
    user.is_suspended = True
    db.session.commit()
    
    flash(f'User {user.username} has been suspended.', 'success')
    return redirect(url_for('admin.users'))


@admin_bp.route('/user/<int:user_id>/unsuspend', methods=['POST'])
@login_required
@admin_required
def unsuspend_user(user_id):
    user = User.query.get_or_404(user_id)
    user.is_suspended = False
    db.session.commit()
    
    flash(f'User {user.username} has been unsuspended.', 'success')
    return redirect(url_for('admin.users'))


@admin_bp.route('/user/<int:user_id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_user(user_id):
    user = User.query.get_or_404(user_id)
    
    if user.id == current_user.id:
        flash('You cannot delete your own account.', 'danger')
        return redirect(url_for('admin.users'))
    
    username = user.username
    
    Property.query.filter_by(user_id=user_id).delete()
    Message.query.filter_by(sender_id=user_id).delete()
    Conversation.query.filter(
        (Conversation.buyer_id == user_id) | (Conversation.seller_id == user_id)
    ).delete()
    
    db.session.delete(user)
    db.session.commit()
    
    flash(f'User {username} and all associated data has been deleted.', 'success')
    return redirect(url_for('admin.users'))


@admin_bp.route('/properties')
@login_required
@admin_required
def properties():
    page = request.args.get('page', 1, type=int)
    filter_type = request.args.get('filter', 'all')
    
    query = Property.query.filter(Property.status == 'published')
    
    if filter_type == 'sale':
        query = query.filter_by(purpose='For Sale')
    elif filter_type == 'rent':
        query = query.filter_by(purpose='For Rent')
    
    properties = query.paginate(page=page, per_page=10)
    
    return render_template('admin/properties.html', properties=properties, filter_type=filter_type, pending_count=_get_pending_count())


@admin_bp.route('/property/<int:property_id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_property(property_id):
    property_obj = Property.query.get_or_404(property_id)
    title = property_obj.title
    
    Conversation.query.filter_by(property_id=property_id).delete()
    PropertyReport.query.filter_by(property_id=property_id).delete()
    
    db.session.delete(property_obj)
    db.session.commit()
    
    flash(f'Property "{title}" has been deleted.', 'success')
    return redirect(url_for('admin.properties'))


@admin_bp.route('/reports')
@login_required
@admin_required
def reports():
    page = request.args.get('page', 1, type=int)
    status = request.args.get('status', 'unresolved')
    
    query = PropertyReport.query
    
    if status == 'resolved':
        query = query.filter_by(is_resolved=True)
    else:
        query = query.filter_by(is_resolved=False)
    
    reports = query.paginate(page=page, per_page=10)
    
    return render_template('admin/reports.html', reports=reports, status=status, pending_count=_get_pending_count())


@admin_bp.route('/report/<int:report_id>/resolve', methods=['POST'])
@login_required
@admin_required
def resolve_report(report_id):
    report = PropertyReport.query.get_or_404(report_id)
    title = report.property.title
    
    report.is_resolved = True
    db.session.commit()
    
    flash(f'Report for property "{title}" has been marked as resolved.', 'success')
    return redirect(url_for('admin.reports'))


@admin_bp.route('/report/<int:report_id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_report(report_id):
    report = PropertyReport.query.get_or_404(report_id)
    db.session.delete(report)
    db.session.commit()
    
    flash('Report has been deleted.', 'success')
    return redirect(url_for('admin.reports'))


@admin_bp.route('/stats/json')
@login_required
@admin_required
def stats_json():
    """API endpoint for dashboard statistics"""
    total_users = User.query.count()
    total_properties = Property.query.filter(Property.status == 'published').count()
    unresolved_reports = PropertyReport.query.filter_by(is_resolved=False).count()
    pending_listings = Property.query.filter_by(status='pending').count()
    
    admin_users = User.query.filter_by(role='admin').count()
    regular_users = User.query.filter_by(role='user').count()
    
    for_sale = Property.query.filter(Property.status == 'published', Property.purpose == 'For Sale').count()
    for_rent = Property.query.filter(Property.status == 'published', Property.purpose == 'For Rent').count()
    
    return jsonify({
        'total_users': total_users,
        'total_properties': total_properties,
        'unresolved_reports': unresolved_reports,
        'pending_listings': pending_listings,
        'admin_users': admin_users,
        'regular_users': regular_users,
        'for_sale': for_sale,
        'for_rent': for_rent
    })


# ...existing code...

def _create_system_conversation(user_id):
    """Create or get system conversation for user"""
    system_user = User.query.filter_by(username='system').first()
    if not system_user:
        return None
    
    conversation = Conversation.query.filter_by(
        buyer_id=user_id,
        seller_id=system_user.id,
        property_id=None,
        is_system_conversation=True  # NEW: Only get system conversations
    ).first()
    
    if not conversation:
        conversation = Conversation(
            buyer_id=user_id,
            seller_id=system_user.id,
            property_id=None,
            is_system_conversation=True  # NEW: Mark as system conversation
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