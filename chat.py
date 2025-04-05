import os
import uuid
import logging
import json
from flask import Blueprint, render_template, request, redirect, url_for, jsonify, flash, current_app
from flask_login import login_required, current_user
from flask_socketio import emit
from app import db, socketio
from models import ChatHistory, ChatMessage, Document, DocumentChunk, User
from rag_engine import RAGEngine
from document_processor import DocumentProcessor

# Create Blueprint
chat_bp = Blueprint('chat', __name__)

# Initialize services
rag_engine = RAGEngine()
document_processor = DocumentProcessor()
logger = logging.getLogger(__name__)

# Routes
@chat_bp.route('/dashboard')
@login_required
def dashboard():
    """Display user dashboard with chat sessions."""
    # Get active chat sessions - limit to recent sessions for dashboard
    active_sessions = ChatHistory.query.filter_by(
        user_id=current_user.id,
        is_active=True
    ).order_by(ChatHistory.updated_at.desc()).limit(5).all()

    # Get recent messages for each session
    for session in active_sessions:
        session.recent_messages = ChatMessage.query.filter_by(
            chat_history_id=session.id
        ).order_by(ChatMessage.timestamp.desc()).limit(3).all()
        # Reverse to show in chronological order
        session.recent_messages.reverse()

    # Get most recent user documents for dashboard
    recent_documents = Document.query.filter_by(
        user_id=current_user.id
    ).order_by(Document.upload_date.desc()).limit(5).all()

    # Get all documents for reference
    all_documents = Document.query.filter_by(
        user_id=current_user.id
    ).order_by(Document.upload_date.desc()).all()

    # Generate statistics for dashboard
    total_documents = len(all_documents)
    total_conversations = ChatHistory.query.filter_by(user_id=current_user.id).count()
    last_activity = None

    # Get last activity time (from either document upload or chat)
    latest_doc = Document.query.filter_by(user_id=current_user.id).order_by(Document.upload_date.desc()).first()
    latest_chat = ChatHistory.query.filter_by(user_id=current_user.id).order_by(ChatHistory.updated_at.desc()).first()

    if latest_doc and latest_chat:
        last_activity = max(latest_doc.upload_date, latest_chat.updated_at)
    elif latest_doc:
        last_activity = latest_doc.upload_date
    elif latest_chat:
        last_activity = latest_chat.updated_at

    return render_template(
        'dashboard.html',
        active_sessions=active_sessions,
        recent_documents=recent_documents,
        all_documents=all_documents,
        total_documents=total_documents,
        total_conversations=total_conversations,
        last_activity=last_activity
    )

@chat_bp.route('/chat/new_session', methods=['POST'])
@login_required
def new_chat_session():
    try:
        # Create a new session
        from datetime import datetime
        session_id = str(uuid.uuid4())
        new_chat = ChatHistory(
            session_id=session_id,
            user_id=current_user.id,
            is_active=True,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        db.session.add(new_chat)
        db.session.commit()
        logger.info(f"Created new chat session: {session_id} for user {current_user.id}")
        return jsonify({'success': True, 'session_id': session_id})
    except Exception as e:
        logger.error(f"Error creating new chat session: {str(e)}", exc_info=True)
        return jsonify({'success': False, 'error': str(e)})

@chat_bp.route('/chat/<session_id>')
@login_required
def chat_page(session_id):
    """Load chat interface for specific session."""
    # Check if session exists and belongs to user
    chat_history = ChatHistory.query.filter_by(
        session_id=session_id,
        user_id=current_user.id
    ).first()

    messages = []

    # If session exists, get messages
    if chat_history:
        messages = ChatMessage.query.filter_by(
            chat_history_id=chat_history.id
        ).order_by(ChatMessage.timestamp).all()

    # Get user documents for upload section
    documents = Document.query.filter_by(
        user_id=current_user.id
    ).order_by(Document.upload_date.desc()).all()

    return redirect(url_for('main.dashboard', session_id=session_id))

@chat_bp.route('/chat/new')
@login_required
def new_chat():
    """Create a new chat session."""
    # Generate a unique session ID
    session_id = str(uuid.uuid4())

    # Create the session object in memory but don't commit it yet
    # We'll only save it after the first message is sent
    chat_history = ChatHistory(
        session_id=session_id,
        user_id=current_user.id
    )

    # Store session_id in session to be able to detect abandoned chats
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
    result = document_processor.process_uploaded_file(file, current_user.id)

    if result['success']:
        flash(f'Document "{result["document_name"]}" uploaded and processed successfully', 'success')
    else:
        flash(f'Error processing document: {result.get("error", "Unknown error")}', 'danger')

    # Return to referring page or documents page
    return redirect(request.referrer or url_for('chat.documents_page'))

@chat_bp.route('/documents/preview/<int:document_id>')
@login_required
def preview_document(document_id):
    """Preview document content."""
    document = Document.query.filter_by(id=document_id, user_id=current_user.id).first()

    if not document:
        return jsonify({'success': False, 'error': 'Document not found'}), 404

    # Get the first few chunks to preview
    chunks = DocumentChunk.query.filter_by(document_id=document.id).order_by(DocumentChunk.chunk_index).limit(3).all()

    preview_text = ""
    for chunk in chunks:
        preview_text += chunk.chunk_text + "\n\n"

    # Truncate if too long
    if len(preview_text) > 1000:
        preview_text = preview_text[:1000] + "...\n\n(Preview truncated. Document contains more content.)"

    return jsonify({
        'success': True,
        'content': preview_text,
        'filename': document.original_filename,
        'file_type': document.file_type,
        'file_size': document.file_size,
        'upload_date': document.upload_date.strftime('%Y-%m-%d %H:%M')
    })

@chat_bp.route('/documents/delete/<int:document_id>', methods=['GET', 'POST'])
@login_required
def delete_document(document_id):
    """Delete a document."""
    document = Document.query.filter_by(id=document_id, user_id=current_user.id).first()

    if not document:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({'success': False, 'error': 'Document not found'})
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

        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({'success': True})

        flash('Document deleted successfully', 'success')
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error deleting document: {str(e)}", exc_info=True)

        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({'success': False, 'error': str(e)})

        flash(f'Error deleting document: {str(e)}', 'danger')

    return redirect(url_for('chat.documents_page'))


@chat_bp.route('/delete-chat/<int:chat_id>', methods=['POST'])
@login_required
def delete_chat(chat_id):
    """Delete a chat session."""
    chat = ChatHistory.query.filter_by(id=chat_id, user_id=current_user.id).first_or_404()

    try:
        # Delete all messages in the chat
        ChatMessage.query.filter_by(chat_history_id=chat.id).delete()

        # Delete the chat history record
        db.session.delete(chat)
        db.session.commit()

        return jsonify({"success": True, "message": "Chat deleted successfully"})
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error deleting chat: {str(e)}")
        return jsonify({"success": False, "message": str(e)}), 500


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

    if not message:
        emit('error', {'message': 'Message cannot be empty'})
        return
        
    if not session_id or session_id.strip() == '':
        # Create a new session ID if not provided
        session_id = str(uuid.uuid4())
        logger.info(f"Created new session ID in message handler: {session_id}")

    try:
        # Get chat history or create a new one
        chat_history = ChatHistory.query.filter_by(
            session_id=session_id,
            user_id=user_id
        ).first()

        if not chat_history:
            # Create new chat history if not found
            from datetime import datetime
            chat_history = ChatHistory(
                session_id=session_id,
                user_id=user_id,
                is_active=True,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            db.session.add(chat_history)
            db.session.flush()  # Get the ID without committing yet
            logger.info(f"Created new chat history for session {session_id}, user {user_id}")

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
        response = rag_engine.process_query(
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

        # Update chat history timestamp and ensure it's active
        chat_history.is_active = True
        chat_history.updated_at = db.func.now()
        db.session.commit()

        # Emit response to client
        emit('receive_message', {
            'message': response['answer'],
            'sources': response.get('metadata', {}).get('sources', []),
            'user_message_id': user_msg.id,
            'ai_message_id': ai_msg.id,
            'session_id': session_id  # Send back the session ID
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

@chat_bp.route('/chat/messages/<session_id>')
@login_required
def get_chat_messages(session_id):
    """Load chat messages."""
    try:
        chat_history = ChatHistory.query.filter_by(
            session_id=session_id,
            user_id=current_user.id
        ).first()

        if not chat_history:
            return jsonify({
                'success': False,
                'message': 'Chat history not found'
            }), 404

        messages = ChatMessage.query.filter_by(
            chat_history_id=chat_history.id
        ).order_by(ChatMessage.timestamp).all()

        messages_data = [{
            'content': msg.content,
            'is_user': msg.is_user,
            'timestamp': msg.timestamp.strftime('%H:%M')
        } for msg in messages]

        return jsonify({
            'success': True,
            'messages': messages_data
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@chat_bp.route('/documents/more')
@login_required
def load_more_documents():
    """Load more documents for pagination."""
    try:
        offset = int(request.args.get('offset', 0))
        limit = int(request.args.get('limit', 5))
        
        # Get additional documents
        documents = Document.query.filter_by(
            user_id=current_user.id
        ).order_by(Document.upload_date.desc()).offset(offset).limit(limit+1).all()
        
        # Check if there are more documents beyond this batch
        has_more = len(documents) > limit
        if has_more:
            documents = documents[:limit]  # Remove the extra document we fetched
        
        # Format document data
        documents_data = []
        for doc in documents:
            documents_data.append({
                'id': doc.id,
                'original_filename': doc.original_filename,
                'file_type': doc.file_type,
                'file_size': doc.file_size,
                'upload_date': doc.upload_date.strftime('%Y-%m-%d %H:%M')
            })
        
        return jsonify({
            'success': True,
            'documents': documents_data,
            'has_more': has_more
        })
    except Exception as e:
        logger.error(f"Error loading more documents: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@chat_bp.route('/chat/more_conversations')
@login_required
def load_more_conversations():
    """Load more conversations for pagination."""
    try:
        offset = int(request.args.get('offset', 0))
        limit = int(request.args.get('limit', 5))
        
        # Get additional conversations
        conversations = ChatHistory.query.filter_by(
            user_id=current_user.id,
            is_active=True
        ).order_by(ChatHistory.updated_at.desc()).offset(offset).limit(limit+1).all()
        
        # Check if there are more conversations beyond this batch
        has_more = len(conversations) > limit
        if has_more:
            conversations = conversations[:limit]  # Remove the extra conversation we fetched
        
        # Format conversation data
        conversations_data = []
        for convo in conversations:
            # Get the most recent message
            recent_message = ChatMessage.query.filter_by(
                chat_history_id=convo.id
            ).order_by(ChatMessage.timestamp.desc()).first()
            
            message_content = recent_message.content if recent_message else ""
            
            conversations_data.append({
                'id': convo.id,
                'session_id': convo.session_id,
                'date': convo.updated_at.strftime('%d %b'),
                'time': convo.updated_at.strftime('%H:%M'),
                'recent_message': message_content
            })
        
        return jsonify({
            'success': True,
            'conversations': conversations_data,
            'has_more': has_more
        })
    except Exception as e:
        logger.error(f"Error loading more conversations: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500