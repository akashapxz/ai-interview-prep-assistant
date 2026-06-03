"""
Page 09 — RAG Knowledge Assistant
Upload PDFs/notes, build vector index, ask questions from your own materials.
"""

import streamlit as st
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from src.auth.supabase_auth import is_authenticated, get_current_user, get_current_profile, sign_out
from src.components.ui_components import (
    inject_global_css, page_header, badge, render_sidebar_nav,
    render_ai_provider_selector, empty_state
)
from src.database.supabase_client import db_insert, db_select, upload_file_to_storage
from src.ai.rag_engine import answer_from_rag, index_document, rebuild_user_index_from_db
from src.utils.pdf_processor import extract_text, validate_file
from src.utils.helpers import generate_session_id, time_ago

st.markdown('<!-- ' + st.get_option('theme.primaryColor') + ' -->' if False else '') # st.set_page_config commented out for navigation
inject_global_css()

if not is_authenticated():
    st.switch_page("app.py")

user = get_current_user()
profile = get_current_profile()
user_id = user["id"]

page_header("RAG Knowledge Assistant", "Upload your study materials and ask questions — AI answers from YOUR documents", "psychology")

tabs = st.tabs(["💬 Ask Questions", "📤 Upload Documents", "📋 Chat History"])

# ── TAB 1: Chat ───────────────────────────────────────────────────────────────
with tabs[0]:
    # Initialize session
    if "rag_session_id" not in st.session_state:
        st.session_state["rag_session_id"] = generate_session_id()
    if "rag_chat_history" not in st.session_state:
        st.session_state["rag_chat_history"] = []

    session_id = st.session_state["rag_session_id"]
    chat_history = st.session_state["rag_chat_history"]

    # Check if user has documents
    docs_indexed = db_select("uploaded_documents", {"user_id": user_id, "is_indexed": True})
    if not docs_indexed:
        st.markdown("""
        <div style="background:rgba(245,158,11,0.1);border:1px solid rgba(245,158,11,0.3);
             border-radius:12px;padding:1rem;margin-bottom:1rem;">
            <div style="color:#fbbf24;font-weight:600;">⚠️ No indexed documents found</div>
            <div style="color:var(--text-secondary);font-size:0.9rem;margin-top:0.3rem;">
                Upload and index your study materials in the "Upload Documents" tab first.
                The AI will answer questions from your uploaded materials.
            </div>
        </div>
        """, unsafe_allow_html=True)

    # Quick-start prompts
    quick_prompts = [
        "Explain the CAP theorem",
        "What is database normalization?",
        "Explain SOLID principles",
        "What is dynamic programming?",
        "Explain TCP vs UDP",
        "What are design patterns?",
    ]

    if not chat_history:
        st.markdown("**💡 Quick Start Prompts:**")
        qp_cols = st.columns(3)
        for i, qp in enumerate(quick_prompts):
            with qp_cols[i % 3]:
                if st.button(qp, key=f"qp_{i}", use_container_width=True):
                    st.session_state["rag_prefill"] = qp

    # Display chat history
    for msg in chat_history:
        role = msg.get("role", "user")
        content = msg.get("content", "")
        sources = msg.get("sources", [])
        if role == "user":
            st.markdown(f"""
            <div style="display:flex;justify-content:flex-end;margin-bottom:0.75rem;">
                <div style="background:rgba(99,102,241,0.15);border:1px solid rgba(99,102,241,0.25);
                     border-radius:16px 16px 4px 16px;padding:0.75rem 1rem;max-width:70%;">
                    <div style="color:var(--text-primary);line-height:1.6;">{content}</div>
                </div>
            </div>
            """, unsafe_allow_html=True)
        else:
            sources_html = ""
            if sources:
                sources_html = "<div style='margin-top:0.5rem;'>" + "".join([f'<span style="background:rgba(99,102,241,0.1);color:#818cf8;border-radius:99px;padding:0.15rem 0.5rem;font-size:0.72rem;margin:2px;display:inline-block;">📄 {s}</span>' for s in sources]) + "</div>"

            st.markdown(f"""
            <div style="display:flex;gap:0.75rem;margin-bottom:0.75rem;">
                <div style="width:36px;height:36px;border-radius:50%;background:linear-gradient(135deg,#6366f1,#06b6d4);
                     display:flex;align-items:center;justify-content:center;font-size:1rem;flex-shrink:0;">🧠</div>
                <div style="background:var(--bg-card);border:1px solid var(--border);
                     border-radius:4px 16px 16px 16px;padding:0.75rem 1rem;flex:1;">
                    <div style="color:#818cf8;font-size:0.72rem;font-weight:600;margin-bottom:0.3rem;">RAG ASSISTANT</div>
                    <div style="color:var(--text-primary);line-height:1.65;">{content}</div>
                    {sources_html}
                </div>
            </div>
            """, unsafe_allow_html=True)

    # Input
    user_input = st.chat_input(
        "Ask anything from your uploaded documents...",
    ) or st.session_state.pop("rag_prefill", None)

    if user_input:
        chat_history.append({"role": "user", "content": user_input})
        # Save to DB
        db_insert("chat_history", {
            "user_id": user_id,
            "session_id": session_id,
            "chat_type": "rag",
            "role": "user",
            "content": user_input,
        })

        with st.spinner("🧠 Searching your documents..."):
            result = answer_from_rag(user_id, user_input)

        answer = result.get("answer", "I couldn't find relevant information.")
        sources = result.get("sources", [])

        chat_history.append({"role": "assistant", "content": answer, "sources": sources})
        # Save to DB
        db_insert("chat_history", {
            "user_id": user_id,
            "session_id": session_id,
            "chat_type": "rag",
            "role": "assistant",
            "content": answer,
            "metadata": {"sources": sources, "chunks_used": result.get("chunks_used", 0)},
        })

        st.session_state["rag_chat_history"] = chat_history
        st.rerun()

    if chat_history:
        if st.button("🗑️ Clear Chat", key="clear_rag"):
            st.session_state["rag_chat_history"] = []
            st.session_state["rag_session_id"] = generate_session_id()
            st.rerun()

# ── TAB 2: Upload Documents ───────────────────────────────────────────────────
with tabs[1]:
    st.markdown("### 📤 Upload Study Materials")
    st.markdown('<div style="color:var(--text-secondary);font-size:0.9rem;margin-bottom:1rem;">Upload PDFs, DOCX, or TXT files — placement notes, interview guides, textbooks, etc.</div>', unsafe_allow_html=True)

    doc_type = st.selectbox(
        "Document Type",
        ["placement_notes", "company_guide", "technical_doc", "interview_pdf", "general"],
        format_func=lambda x: {"placement_notes": "📝 Placement Notes", "company_guide": "🏢 Company Guide",
                                "technical_doc": "💻 Technical Documentation", "interview_pdf": "🎯 Interview PDF",
                                "general": "📄 General"}.get(x, x),
        key="doc_type_select"
    )

    uploaded_docs = st.file_uploader(
        "Upload Documents",
        type=["pdf", "docx", "txt"],
        accept_multiple_files=True,
        help="Upload multiple files at once. Max 10MB per file.",
        key="rag_file_uploader"
    )

    if uploaded_docs:
        upload_btn = st.button(f"📥 Index {len(uploaded_docs)} Document(s)", type="primary", key="upload_rag_btn")
        if upload_btn:
            progress = st.progress(0)
            for idx, f in enumerate(uploaded_docs):
                file_bytes = f.read()
                valid, msg = validate_file(file_bytes, f.name)
                if not valid:
                    st.error(f"❌ {f.name}: {msg}")
                    continue

                with st.spinner(f"Processing {f.name}..."):
                    # Extract text
                    text = extract_text(file_bytes, f.name)
                    if not text:
                        st.warning(f"⚠️ Could not extract text from {f.name}")
                        continue

                    # Upload to storage
                    storage_path = f"{user_id}/rag_docs/{f.name}"
                    file_url = upload_file_to_storage("documents", storage_path, file_bytes)

                    # Save to DB
                    doc_row = db_insert("uploaded_documents", {
                        "user_id": user_id,
                        "file_name": f.name,
                        "file_url": file_url or "",
                        "file_type": f.name.split(".")[-1].upper(),
                        "file_size": len(file_bytes),
                        "doc_type": doc_type,
                    })

                    if doc_row:
                        # Index the document
                        success = index_document(
                            user_id=user_id,
                            doc_id=doc_row["id"],
                            text=text,
                            file_name=f.name,
                            doc_type=doc_type,
                        )
                        if success:
                            st.success(f"✅ {f.name} indexed successfully!")
                        else:
                            st.error(f"Failed to index {f.name}")

                progress.progress((idx + 1) / len(uploaded_docs))
            st.success("🎉 All documents processed! Go to 'Ask Questions' tab to start chatting.")
            st.rerun()

    # Existing documents
    st.markdown("---\n### 📚 Your Indexed Documents")
    all_docs = db_select("uploaded_documents", {"user_id": user_id}, order="created_at.desc")
    if all_docs:
        for doc in all_docs:
            indexed = doc.get("is_indexed", False)
            chunks = doc.get("chunk_count", 0)
            doc_type_label = doc.get("doc_type", "general").replace("_", " ").title()
            st.markdown(f"""
            <div style="background:var(--bg-card);border:1px solid var(--border);
                 border-radius:12px;padding:0.75rem 1rem;margin-bottom:0.4rem;
                 display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:0.5rem;">
                <div>
                    <span style="color:var(--text-primary);font-weight:600;font-size:0.9rem;">📄 {doc['file_name']}</span>
                    <div style="color:var(--text-muted);font-size:0.78rem;">{doc_type_label} · {doc['file_type']} · {doc.get('file_size',0)//1024}KB</div>
                </div>
                <div style="display:flex;align-items:center;gap:0.75rem;">
                    <span style="color:var(--text-muted);font-size:0.78rem;">{chunks} chunks</span>
                    <span style="{'color:#22c55e' if indexed else 'color:#f59e0b'};font-size:0.82rem;font-weight:600;">{'✅ Indexed' if indexed else '⏳ Pending'}</span>
                </div>
            </div>
            """, unsafe_allow_html=True)
    else:
        empty_state("📚", "No documents yet", "Upload your study materials above to get started!")

# ── TAB 3: Chat History ───────────────────────────────────────────────────────
with tabs[2]:
    past_chats = db_select("chat_history", {"user_id": user_id, "chat_type": "rag"}, order="created_at.desc", limit=50)
    if past_chats:
        # Group by session
        sessions = {}
        for msg in past_chats:
            sid = msg.get("session_id", "unknown")
            if sid not in sessions:
                sessions[sid] = []
            sessions[sid].append(msg)

        for sid, msgs in list(sessions.items())[:5]:
            with st.expander(f"💬 Session — {msgs[-1].get('created_at','')[:16] if msgs else ''}"):
                for msg in msgs[:10]:
                    role = msg.get("role")
                    color = "#818cf8" if role == "user" else "#06b6d4"
                    label = "You" if role == "user" else "RAG Assistant"
                    st.markdown(f'<div style="color:{color};font-size:0.75rem;font-weight:600;">{label}:</div>', unsafe_allow_html=True)
                    st.markdown(f'<div style="color:var(--text-primary);font-size:0.88rem;margin-bottom:0.5rem;">{msg["content"][:200]}...</div>', unsafe_allow_html=True)
    else:
        empty_state("forum", "No chat history", "Start asking questions in the 'Ask Questions' tab!")
