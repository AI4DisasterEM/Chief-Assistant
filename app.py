"""CHIEF Assistant - Streamlit Dashboard"""
import streamlit as st
import sys
sys.path.insert(0, '.')

from datetime import datetime

# Page config
st.set_page_config(
    page_title="CHIEF Assistant",
    page_icon="🔥",
    layout="wide"
)

# Initialize session state
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []

# Sidebar
st.sidebar.title("🔥 CHIEF")
st.sidebar.caption("Contextual Helper for Integrated Executive Functions")

page = st.sidebar.radio("Navigate", [
    "💬 Chat",
    "📅 Calendar", 
    "✅ Actions",
    "📚 Credentials",
    "👥 Contacts",
    "📄 Documents",
    "🎤 Voice Notes"
])

st.sidebar.markdown("---")
st.sidebar.caption(f"🕐 {datetime.now().strftime('%I:%M %p')}")
st.sidebar.caption(f"📆 {datetime.now().strftime('%A, %B %d')}")

# Main content
if page == "💬 Chat":
    st.title("💬 Chat with CHIEF")
    
    # Display chat history
    for msg in st.session_state.chat_history:
        with st.chat_message(msg["role"]):
            st.write(msg["content"])
    
    # Chat input
    if prompt := st.chat_input("Ask CHIEF anything..."):
        st.session_state.chat_history.append({"role": "user", "content": prompt})
        
        with st.chat_message("user"):
            st.write(prompt)
        
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                try:
                    from src.agent.orchestrator import process_message
                    response = process_message(prompt)
                except Exception as e:
                    response = f"Error: {str(e)}"
                
                st.write(response)
                st.session_state.chat_history.append({"role": "assistant", "content": response})

elif page == "📅 Calendar":
    st.title("📅 Calendar")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("Today's Events")
        try:
            from src.calendar.google_calendar import get_todays_events, format_events_for_display
            events = get_todays_events()
            if events:
                for event in events:
                    start = event['start'].get('dateTime', event['start'].get('date'))
                    if 'T' in start:
                        dt = datetime.fromisoformat(start.replace('Z', '+00:00'))
                        time_str = dt.strftime('%I:%M %p')
                    else:
                        time_str = 'All day'
                    
                    with st.container():
                        st.markdown(f"**{time_str}** - {event.get('summary', 'No title')}")
                        if event.get('location'):
                            st.caption(f"📍 {event['location']}")
            else:
                st.info("No events scheduled for today.")
        except Exception as e:
            st.error(f"Error loading calendar: {e}")
    
    with col2:
        st.subheader("This Week")
        try:
            from src.calendar.google_calendar import get_upcoming_events
            upcoming = get_upcoming_events(days=7)
            st.metric("Events", len(upcoming))
        except:
            st.metric("Events", "—")

elif page == "✅ Actions":
    st.title("✅ Pending Actions")
    
    try:
        from src.notes.note_manager import NoteSession
        notes = NoteSession()
        actions = notes.get_pending_actions()
        
        if actions:
            for action in actions:
                col1, col2, col3 = st.columns([3, 1, 1])
                with col1:
                    st.checkbox(action['description'], key=action['PK'])
                with col2:
                    st.caption(action.get('due_date', 'No due date'))
                with col3:
                    priority = action.get('priority', 'medium')
                    if priority == 'high':
                        st.markdown("🔴 High")
                    elif priority == 'medium':
                        st.markdown("🟡 Medium")
                    else:
                        st.markdown("🟢 Low")
        else:
            st.success("No pending actions! 🎉")
    except Exception as e:
        st.error(f"Error loading actions: {e}")
    
    st.markdown("---")
    st.subheader("Quick Add")
    new_action = st.text_input("New action item")
    if st.button("Add Action"):
        if new_action:
            st.success(f"Added: {new_action}")

elif page == "📚 Credentials":
    st.title("📚 Professional Development")
    
    try:
        from src.agent.credentials_manager import CredentialsManager
        cm = CredentialsManager()
        
        # Summary metrics
        credentials = cm.get_all_credentials()
        active = len([c for c in credentials if c.get('status') == 'active'])
        in_progress = len([c for c in credentials if c.get('status') == 'in_progress'])
        
        col1, col2, col3 = st.columns(3)
        col1.metric("Active", active)
        col2.metric("In Progress", in_progress)
        col3.metric("Expiring Soon", len(cm.get_expiring_soon(90)))
        
        st.markdown("---")
        
        # CEU Progress
        st.subheader("CEU Progress")
        for ceu in cm.get_ceu_status():
            st.write(f"**{ceu['name']}**")
            st.progress(ceu['percent'] / 100)
            st.caption(f"{ceu['earned']}/{ceu['required']} CEUs ({ceu['remaining']} remaining)")
        
        st.markdown("---")
        
        # All credentials
        st.subheader("All Credentials")
        for cred in credentials:
            with st.expander(f"{cred['name']} ({cred['status']})"):
                st.write(f"**Type:** {cred['credential_type']}")
                st.write(f"**Issuer:** {cred.get('issuing_body', 'N/A')}")
                if cred.get('expiration_date'):
                    st.write(f"**Expires:** {cred['expiration_date']}")
                if cred.get('milestones'):
                    st.write("**Milestones:**")
                    for m in cred['milestones']:
                        st.write(f"  - {m['description']} ({m['date']})")
    except Exception as e:
        st.error(f"Error loading credentials: {e}")

elif page == "👥 Contacts":
    st.title("👥 Key Contacts")
    
    try:
        from src.agent.contacts_manager import ContactsManager, TONE_PROFILES
        contacts = ContactsManager()
        all_contacts = contacts.get_all_contacts()
        
        # Search
        search = st.text_input("🔍 Search contacts")
        
        if search:
            all_contacts = [c for c in all_contacts if search.lower() in c.get('name', '').lower() or search.lower() in c.get('organization', '').lower()]
        
        for contact in all_contacts:
            with st.expander(f"**{contact['name']}** - {contact['role']}"):
                st.write(f"**Organization:** {contact['organization']}")
                st.write(f"**Communication Style:** {contact['communication_style']}")
                
                # Show tone guidelines
                profile = TONE_PROFILES.get(contact['communication_style'], {})
                st.info(f"💡 {profile.get('guidelines', 'No guidelines')}")
                
                if contact.get('notes'):
                    st.write(f"**Notes:** {contact['notes']}")
                
                if contact.get('interactions'):
                    st.write("**Recent Interactions:**")
                    for i in contact['interactions'][-3:]:
                        st.caption(f"  {i['date']} - {i['type']}: {i['summary']}")
    except Exception as e:
        st.error(f"Error loading contacts: {e}")

elif page == "📄 Documents":
    st.title("📄 Document Search")
    
    try:
        from src.agent.document_rag import DocumentRAG
        rag = DocumentRAG()
        
        # List documents
        docs = rag.list_documents()
        st.caption(f"{len(docs)} documents indexed")
        
        # Search
        query = st.text_input("🔍 Search documents", placeholder="e.g., overtime policy, drone requirements")
        
        if query:
            with st.spinner("Searching..."):
                result = rag.query_with_answer(query)
            
            st.subheader("Answer")
            st.write(result['answer'])
            
            st.markdown("---")
            st.subheader("Sources")
            for c in result['citations'][:3]:
                with st.expander(f"[{c['rank']}] {c['title']} (score: {c['score']:.2f})"):
                    st.write(c['text'])
        
        st.markdown("---")
        st.subheader("Indexed Documents")
        for doc in docs:
            st.write(f"• {doc['title']} ({doc['doc_type']})")
    except Exception as e:
        st.error(f"Error loading documents: {e}")

elif page == "🎤 Voice Notes":
    st.title("🎤 Voice Notes")
    
    st.write("Upload an audio file to transcribe and extract action items.")
    
    uploaded_file = st.file_uploader("Choose an audio file", type=['mp3', 'm4a', 'wav', 'ogg'])
    
    if uploaded_file:
        st.audio(uploaded_file)
        
        if st.button("Transcribe & Process"):
            with st.spinner("Transcribing..."):
                try:
                    import tempfile
                    from src.notes.voice_transcription import VoiceTranscriber
                    
                    # Save uploaded file temporarily
                    with tempfile.NamedTemporaryFile(delete=False, suffix='.mp3') as tmp:
                        tmp.write(uploaded_file.read())
                        tmp_path = tmp.name
                    
                    transcriber = VoiceTranscriber()
                    result = transcriber.transcribe_and_process(tmp_path, source_type='file')
                    
                    st.subheader("Transcript")
                    st.write(result['transcript'])
                    
                    st.subheader("Actions Extracted")
                    if result['actions']:
                        for action in result['actions']:
                            st.write(f"• {action.get('task', action.get('description', 'Unknown'))}")
                    else:
                        st.info("No actions detected")
                    
                    st.subheader("Summary")
                    st.write(result['summary'])
                    
                except Exception as e:
                    st.error(f"Error: {e}")

# Footer
st.sidebar.markdown("---")
st.sidebar.caption("Built with ❤️ for Chief Steven")
