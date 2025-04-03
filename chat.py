import os
import uuid
import logging
import json
from flask import Blueprint, render_template, request, redirect, url_for, jsonify, flash, current_app
from flask_login import login_required, current_user
from flask_socketio import emit
from extensions import db, socketio
from models import User, ChatHistory, ChatMessage, Document

# Create Blueprint
chat_bp = Blueprint('chat', __name__)

# Set up logging
logger = logging.getLogger(__name__)

# Routes
@chat_bp.route('/dashboard')
@login_required
def dashboard():
    """Display user dashboard with chat sessions."""
    # Get active chat sessions
    active_sessions = ChatHistory.query.filter_by(
        user_id=current_user.id,
        is_active=True
    ).order_by(ChatHistory.updated_at.desc()).all()
    
    # Get user documents
    documents = Document.query.filter_by(
        user_id=current_user.id
    ).order_by(Document.upload_date.desc()).all()
    
    return render_template(
        'dashboard.html',
        active_sessions=active_sessions,
        documents=documents
    )

@chat_bp.route('/chat/<session_id>')
@login_required
def chat_page(session_id):
    """Load chat interface for specific session."""
    # Check if session exists and belongs to user
    chat_history = ChatHistory.query.filter_by(
        session_id=session_id,
        user_id=current_user.id
    ).first()
    
    # If session doesn't exist, create it
    if not chat_history:
        chat_history = ChatHistory(
            session_id=session_id,
            user_id=current_user.id
        )
        db.session.add(chat_history)
        db.session.commit()
    
    # Get messages for this session
    messages = ChatMessage.query.filter_by(
        chat_history_id=chat_history.id
    ).order_by(ChatMessage.timestamp).all()
    
    # Get user documents for upload section
    documents = Document.query.filter_by(
        user_id=current_user.id
    ).order_by(Document.upload_date.desc()).all()
    
    return render_template(
        'chat.html',
        session_id=session_id,
        chat_history=chat_history,
        messages=messages,
        documents=documents
    )

@chat_bp.route('/chat/new')
@login_required
def new_chat():
    """Create a new chat session."""
    # Generate a unique session ID
    session_id = str(uuid.uuid4())
    
    # Create new chat history
    chat_history = ChatHistory(
        session_id=session_id,
        user_id=current_user.id
    )
    db.session.add(chat_history)
    db.session.commit()
    
    return redirect(url_for('chat.chat_page', session_id=session_id))

@chat_bp.route('/documents', methods=['GET'])
@login_required
def documents_page():
    """Display user's documents."""
    documents = Document.query.filter_by(
        user_id=current_user.id
    ).order_by(Document.upload_date.desc()).all()
    
    return render_template('documents.html', documents=documents)

@chat_bp.route('/documents/upload', methods=['POST'])
@login_required
def upload_document():
    """Handle document upload."""
    if 'document' not in request.files:
        flash('No file selected', 'danger')
        return redirect(request.referrer or url_for('chat.documents_page'))
    
    file = request.files['document']
    if file.filename == '':
        flash('No file selected', 'danger')
        return redirect(request.referrer or url_for('chat.documents_page'))
    
    # Process the uploaded file
    result = current_app.document_processor.process_uploaded_file(file, current_user.id)
    
    if result['success']:
        flash(f'Document "{result["document_name"]}" uploaded and processed successfully', 'success')
    else:
        flash(f'Error processing document: {result.get("error", "Unknown error")}', 'danger')
    
    # Return to referring page or documents page
    return redirect(request.referrer or url_for('chat.documents_page'))

@chat_bp.route('/documents/delete/<int:document_id>', methods=['POST'])
@login_required
def delete_document(document_id):
    """Delete a document."""
    document = Document.query.filter_by(id=document_id, user_id=current_user.id).first()
    
    if not document:
        flash('Document not found', 'danger')
        return redirect(url_for('chat.documents_page'))
    
    try:
        # Delete file from disk if it exists
        file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], document.filename)
        if os.path.exists(file_path):
            os.remove(file_path)
        
        # Delete document from database
        db.session.delete(document)
        db.session.commit()
        
        flash('Document deleted successfully', 'success')
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error deleting document: {str(e)}", exc_info=True)
        flash(f'Error deleting document: {str(e)}', 'danger')
    
    return redirect(url_for('chat.documents_page'))

@chat_bp.route('/chat/end/<session_id>', methods=['POST'])
@login_required
def end_chat(session_id):
    """End a chat session and generate summary."""
    chat_history = ChatHistory.query.filter_by(
        session_id=session_id,
        user_id=current_user.id
    ).first()
    
    if not chat_history:
        flash('Chat session not found', 'danger')
        return redirect(url_for('chat.dashboard'))
    
    try:
        # Generate session summary
        summary = current_app.rag_engine.generate_session_summary(session_id)
        
        # Update chat history
        chat_history.is_active = False
        chat_history.summary = summary
        db.session.commit()
        
        flash('Chat session ended and summarized', 'success')
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error ending chat session: {str(e)}", exc_info=True)
        flash(f'Error ending chat session: {str(e)}', 'danger')
    
    return redirect(url_for('chat.dashboard'))

# Socket.IO event handlers
@socketio.on('send_message')
def handle_message(data):
    """Handle incoming chat messages via Socket.IO."""
    user_id = current_user.id if current_user.is_authenticated else None
    
    if not user_id:
        emit('error', {'message': 'Authentication required'})
        return
    
    session_id = data.get('session_id')
    message = data.get('message', '').strip()
    
    if not session_id or not message:
        emit('error', {'message': 'Missing session ID or message'})
        return
    
    try:
        # Get chat history
        chat_history = ChatHistory.query.filter_by(
            session_id=session_id,
            user_id=user_id
        ).first()
        
        if not chat_history:
            # Create new chat history if not found
            chat_history = ChatHistory(
                session_id=session_id,
                user_id=user_id
            )
            db.session.add(chat_history)
            db.session.flush()
        
        # Save user message
        user_msg = ChatMessage(
            chat_history_id=chat_history.id,
            content=message,
            is_user=True
        )
        db.session.add(user_msg)
        db.session.flush()
        
        # Get recent messages for context
        recent_messages = ChatMessage.query.filter_by(
            chat_history_id=chat_history.id
        ).order_by(ChatMessage.timestamp).all()
        
        context = []
        for msg in recent_messages[-10:]:  # Last 10 messages
            context.append({
                'content': msg.content,
                'is_user': msg.is_user,
                'timestamp': msg.timestamp.isoformat()
            })
        
        # Process query with RAG engine
        response = current_app.rag_engine.process_query(
            query=message,
            user_id=user_id,
            session_id=session_id,
            chat_context=context
        )
        
        # Save AI response
        ai_msg = ChatMessage(
            chat_history_id=chat_history.id,
            content=response['answer'],
            is_user=False,
            related_documents=json.dumps(response.get('metadata', {}).get('sources', []))
        )
        db.session.add(ai_msg)
        
        # Update chat history timestamp
        chat_history.updated_at = db.func.now()
        db.session.commit()
        
        # Emit response to client
        emit('receive_message', {
            'message': response['answer'],
            'sources': response.get('metadata', {}).get('sources', []),
            'user_message_id': user_msg.id,
            'ai_message_id': ai_msg.id
        })
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error processing message: {str(e)}", exc_info=True)
        emit('error', {'message': f'Error processing message: {str(e)}'})

@socketio.on('connect')
def handle_connect():
    if not current_user.is_authenticated:
        return False  # Reject connection if not authenticated

# Admin routes - restricted to admin users
@chat_bp.route('/admin')
@login_required
def admin():
    """Admin dashboard for system management."""
    if not current_user.has_role('admin'):
        flash('Access denied. Admin privileges required.', 'danger')
        return redirect(url_for('chat.dashboard'))
    
    # Get system statistics
    user_count = db.session.query(db.func.count('*').label('count')).select_from(User).scalar()
    document_count = db.session.query(db.func.count('*').label('count')).select_from(Document).scalar()
    active_chats = db.session.query(db.func.count('*').label('count')).select_from(ChatHistory).filter_by(is_active=True).scalar()
    
    return render_template(
        'admin.html',
        user_count=user_count,
        document_count=document_count,
        active_chats=active_chats
    )