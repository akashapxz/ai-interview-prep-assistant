"""
Page 07 — Voice Interview Mode
Speech-to-text interview with filler word detection, confidence analysis, and voice report.
"""

import streamlit as st
import sys, os, time
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from src.auth.supabase_auth import is_authenticated, get_current_user, get_current_profile, sign_out
from src.components.ui_components import (
    inject_global_css, page_header, render_sidebar_nav,
    render_ai_provider_selector, empty_state, feedback_card, badge
)
from src.database.supabase_client import db_insert, award_xp
from src.ai.gemini_client import generate_technical_questions, generate_hr_questions, analyze_voice_transcript

st.markdown('<!-- ' + st.get_option('theme.primaryColor') + ' -->' if False else '') # st.set_page_config commented out for navigation
inject_global_css()

if not is_authenticated():
    st.switch_page("app.py")

user = get_current_user()
profile = get_current_profile()
user_id = user["id"]

page_header("Voice Interview Mode", "Practice speaking your answers aloud — AI analyzes your communication quality", "mic")

# ── Browser Speech Recognition JS ────────────────────────────────────────────
st.markdown("""
<div style="background:rgba(99,102,241,0.08);border:1px solid rgba(99,102,241,0.2);
     border-radius:14px;padding:1.25rem;margin-bottom:1.5rem;">
    <div style="color:#818cf8;font-weight:700;margin-bottom:0.5rem;">🎙️ How Voice Interview Works</div>
    <div style="display:grid;grid-template-columns:repeat(4,1fr);gap:0.75rem;">
        <div style="text-align:center;"><div style="font-size:1.5rem;">📋</div><div style="color:var(--text-primary);font-size:0.85rem;margin-top:0.3rem;">AI generates question</div></div>
        <div style="text-align:center;"><div style="font-size:1.5rem;">🎙️</div><div style="color:var(--text-primary);font-size:0.85rem;margin-top:0.3rem;">Click mic & speak</div></div>
        <div style="text-align:center;"><div style="font-size:1.5rem;">📝</div><div style="color:var(--text-primary);font-size:0.85rem;margin-top:0.3rem;">Speech converted to text</div></div>
        <div style="text-align:center;"><div style="font-size:1.5rem;">📊</div><div style="color:var(--text-primary);font-size:0.85rem;margin-top:0.3rem;">AI analyzes speech quality</div></div>
    </div>
</div>
""", unsafe_allow_html=True)

# Speech Recognition JavaScript component
voice_js = """
<div id="voice-panel" style="background:var(--bg-card);border:1px solid var(--border);
     border-radius:16px;padding:1.5rem;text-align:center;">

    <div id="status-text" style="color:var(--text-muted);font-size:0.85rem;margin-bottom:1rem;">
        Click the microphone to start recording
    </div>

    <button id="mic-btn" onclick="toggleRecording()" style="
        width:80px;height:80px;border-radius:50%;border:none;cursor:pointer;
        background:linear-gradient(135deg,#6366f1,#8b5cf6);
        font-size:2rem;transition:all 0.3s ease;
        box-shadow:0 0 20px rgba(99,102,241,0.4);
    ">🎙️</button>

    <div id="recording-indicator" style="display:none;margin-top:0.75rem;">
        <span style="color:#ef4444;font-weight:600;animation:pulse-glow 1s infinite;">● Recording...</span>
    </div>

    <div id="transcript-box" style="
        margin-top:1rem;padding:1rem;
        background:rgba(0,0,0,0.3);border-radius:10px;
        color:var(--text-primary);min-height:80px;font-size:0.9rem;line-height:1.6;
        text-align:left;display:none;
    ">
        <div style="color:var(--text-muted);font-size:0.75rem;margin-bottom:0.3rem;">TRANSCRIPT</div>
        <div id="transcript-text"></div>
    </div>

    <div id="copy-section" style="display:none;margin-top:0.75rem;">
        <button onclick="copyTranscript()" style="
            background:rgba(99,102,241,0.2);border:1px solid rgba(99,102,241,0.4);
            color:#818cf8;border-radius:8px;padding:0.4rem 1rem;cursor:pointer;font-size:0.85rem;
        ">📋 Copy Transcript</button>
    </div>
</div>

<script>
let recognition = null;
let isRecording = false;
let fullTranscript = '';

function toggleRecording() {
    if (!('webkitSpeechRecognition' in window) && !('SpeechRecognition' in window)) {
        document.getElementById('status-text').innerHTML = '<span style="color:#ef4444;">❌ Browser does not support voice recognition. Use Chrome/Edge.</span>';
        return;
    }

    if (isRecording) {
        recognition.stop();
        isRecording = false;
    } else {
        startRecording();
    }
}

function startRecording() {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    recognition = new SpeechRecognition();
    recognition.continuous = true;
    recognition.interimResults = true;
    recognition.lang = 'en-US';

    recognition.onstart = function() {
        isRecording = true;
        document.getElementById('mic-btn').style.background = 'linear-gradient(135deg,#ef4444,#dc2626)';
        document.getElementById('mic-btn').innerHTML = '⏹️';
        document.getElementById('status-text').innerHTML = '<span style="color:#22c55e;">🔴 Recording... Speak now</span>';
        document.getElementById('recording-indicator').style.display = 'block';
        document.getElementById('transcript-box').style.display = 'block';
    };

    recognition.onresult = function(event) {
        let interim = '';
        let final = '';
        for (let i = event.resultIndex; i < event.results.length; i++) {
            if (event.results[i].isFinal) {
                final += event.results[i][0].transcript;
            } else {
                interim += event.results[i][0].transcript;
            }
        }
        fullTranscript += final;
        document.getElementById('transcript-text').innerHTML =
            '<span style="color:var(--text-primary);">' + fullTranscript + '</span>' +
            '<span style="color:var(--text-muted);">' + interim + '</span>';
        document.getElementById('copy-section').style.display = 'block';
    };

    recognition.onend = function() {
        isRecording = false;
        document.getElementById('mic-btn').style.background = 'linear-gradient(135deg,#6366f1,#8b5cf6)';
        document.getElementById('mic-btn').innerHTML = 'mic';
        document.getElementById('status-text').innerHTML = 'Recording stopped. <a onclick="startRecording()" style="color:#6366f1;cursor:pointer;">Record again</a>';
        document.getElementById('recording-indicator').style.display = 'none';
    };

    recognition.onerror = function(e) {
        document.getElementById('status-text').innerHTML = '<span style="color:#ef4444;">Error: ' + e.error + '</span>';
    };

    recognition.start();
}

function copyTranscript() {
    navigator.clipboard.writeText(fullTranscript).then(() => {
        alert('Transcript copied to clipboard! Paste it in the text box below.');
    });
}
</script>
"""

# ── Interview Setup ───────────────────────────────────────────────────────────
c1, c2 = st.columns(2)
with c1:
    voice_type = st.selectbox("Question Type", ["Technical", "HR Behavioral", "Mixed"], key="voice_type")
with c2:
    num_questions = st.slider("Questions", 3, 8, 5, key="voice_q_count")

gen_voice_btn = st.button("🎯 Generate Questions", type="primary", key="gen_voice_btn")

if gen_voice_btn:
    with st.spinner("Generating interview questions..."):
        if voice_type == "HR Behavioral":
            result = generate_hr_questions(
                name=profile.get("full_name", "Candidate") if profile else "Candidate",
                college=profile.get("college", "") if profile else "",
                branch=profile.get("branch", "") if profile else "",
                count=num_questions
            )
            q_list = [q.get("question", "") for q in (result.get("questions", []) if result else [])]
        else:
            result = generate_technical_questions("DSA", "medium", "conceptual", count=num_questions)
            q_list = [q.get("question", "") for q in (result.get("questions", []) if result else [])]

    if q_list:
        # Clear all previous session-specific voice keys
        keys_to_clear = [k for k in st.session_state.keys() if k.startswith("voice_") and k not in ["voice_type", "voice_q_count"]]
        for k in keys_to_clear:
            st.session_state.pop(k, None)
            
        st.session_state["voice_questions"] = q_list
        st.session_state["voice_current_q"] = 0
        st.session_state["voice_answers"] = []
        st.success(f"✅ {len(q_list)} questions ready!")
        st.rerun()
    else:
        st.error("Failed to generate questions.")

# ── Active Voice Session ──────────────────────────────────────────────────────
voice_questions = st.session_state.get("voice_questions", [])
current_q = st.session_state.get("voice_current_q", 0)

if voice_questions and current_q < len(voice_questions):
    st.markdown("---")
    q_text = voice_questions[current_q]

    # Question display
    st.markdown(f"""
    <div style="background:rgba(99,102,241,0.1);border:1px solid rgba(99,102,241,0.3);
         border-radius:14px;padding:1.25rem;margin-bottom:1.5rem;">
        <div style="display:flex;align-items:center;gap:0.5rem;margin-bottom:0.5rem;">
            <span style="background:#6366f1;color:#fff;border-radius:6px;padding:0.2rem 0.6rem;font-size:0.75rem;font-weight:700;">Q{current_q+1}/{len(voice_questions)}</span>
            {badge(voice_type, '#8b5cf6')}
        </div>
        <div style="color:var(--text-primary);font-size:1rem;line-height:1.65;">{q_text}</div>
        <div style="color:var(--text-muted);font-size:0.8rem;margin-top:0.5rem;">💡 Speak your answer clearly and confidently</div>
    </div>
    """, unsafe_allow_html=True)

    # Speak the question aloud automatically
    try:
        from gtts import gTTS
        import io
        
        @st.cache_data(show_spinner=False)
        def get_tts_audio(text: str):
            tts = gTTS(text=text, lang='en')
            fp = io.BytesIO()
            tts.write_to_fp(fp)
            return fp.getvalue()

        audio_bytes_q = get_tts_audio(q_text)
        st.audio(audio_bytes_q, format="audio/mp3", autoplay=True)
    except Exception as e:
        pass

    # Native Voice recorder component
    audio_input = st.audio_input("🎙️ Record your answer", key=f"voice_audio_input_{current_q}")

    transcript_key = f"voice_auto_transcript_{current_q}"
    last_hash_key = f"voice_last_hash_{current_q}"

    if audio_input:
        audio_input.seek(0)
        audio_bytes = audio_input.read()
        # Calculate a simple hash based on length and first/last chunks of bytes to uniquely identify this recording
        audio_hash = f"{len(audio_bytes)}_{audio_bytes[:100]}_{audio_bytes[-100:]}"
        
        if st.session_state.get(last_hash_key) != audio_hash:
            with st.spinner("✍️ Transcribing your speech..."):
                from src.ai.gemini_client import transcribe_audio
                transcript = transcribe_audio(audio_bytes)
                st.session_state[transcript_key] = transcript or ""
                st.session_state[last_hash_key] = audio_hash
                st.session_state[f"voice_transcript_{current_q}"] = transcript or ""

    # Manual transcript input / edit area
    st.markdown("**📝 Your Answer Transcript:**")
    transcript_input = st.text_area(
        "Transcript",
        placeholder="Record your answer above to generate transcript, or type/paste it here...",
        key=f"voice_transcript_{current_q}",
        height=120,
        label_visibility="collapsed"
    )


    # Check if analysis has been run for this question
    analysis_key = f"voice_analysis_{current_q}"
    analysis = st.session_state.get(analysis_key)

    if not analysis:
        # If no analysis yet, show buttons to analyze or skip
        col_analyze, col_next = st.columns(2)
        with col_analyze:
            analyze_btn = st.button("📊 Analyze Voice Response", type="primary", use_container_width=True, key=f"analyze_voice_{current_q}")
        with col_next:
            skip_btn = st.button("⏭️ Skip to Next", use_container_width=True, key=f"skip_voice_{current_q}")

        if analyze_btn and transcript_input.strip():
            words = transcript_input.split()
            wpm = max(1, len(words))  # rough estimate
            with st.spinner("🤖 AI analyzing your speech..."):
                analysis = analyze_voice_transcript(transcript_input, wpm, 60)

            if analysis:
                st.session_state[analysis_key] = analysis
                st.session_state["voice_answers"].append({
                    "question": q_text,
                    "transcript": transcript_input,
                    "analysis": analysis,
                })

                # Save voice session to DB
                db_insert("voice_sessions", {
                    "user_id": user_id,
                    "transcript": transcript_input,
                    "speaking_speed": analysis.get("speaking_speed_wpm", wpm),
                    "filler_word_count": analysis.get("total_filler_count", 0),
                    "filler_words": analysis.get("filler_words", {}),
                    "confidence_score": analysis.get("confidence_score", 0),
                    "communication_score": analysis.get("communication_score", 0),
                    "clarity_score": analysis.get("clarity_score", 0),
                    "ai_analysis": analysis.get("detailed_feedback", ""),
                })
                award_xp(user_id, 20)
                st.rerun()

        if skip_btn:
            st.session_state["voice_current_q"] = current_q + 1
            st.rerun()
    else:
        # Show analysis results
        st.markdown("**📊 Voice Analysis Results:**")
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Confidence", f"{analysis.get('confidence_score',0):.0f}/100")
        m2.metric("Communication", f"{analysis.get('communication_score',0):.0f}/100")
        m3.metric("Clarity", f"{analysis.get('clarity_score',0):.0f}/100")
        m4.metric("Filler Words", analysis.get("total_filler_count", 0))

        speed_assess = analysis.get("speed_assessment", "ideal")
        speed_color = "#22c55e" if speed_assess == "ideal" else "#f59e0b"
        st.markdown(f'<div style="color:{speed_color};font-size:0.85rem;margin-bottom:1rem;">Speaking Speed: {analysis.get("speaking_speed_wpm",0):.0f} WPM — {speed_assess.replace("_"," ").upper()}</div>', unsafe_allow_html=True)

        if analysis.get("detailed_feedback"):
            st.markdown(f'<div style="background:var(--bg-card);border-radius:10px;padding:0.75rem;color:var(--text-primary);margin-top:0.5rem;margin-bottom:1rem;">{analysis["detailed_feedback"]}</div>', unsafe_allow_html=True)
            
            # Speak feedback aloud via TTS (limit to first two sentences)
            try:
                import re
                feedback_text = analysis["detailed_feedback"]
                sentences = re.split(r'(?<=[.!?])\s+', feedback_text)
                speak_text = " ".join(sentences[:2])
                audio_bytes_feedback = get_tts_audio("Here is your feedback: " + speak_text)
                st.audio(audio_bytes_feedback, format="audio/mp3", autoplay=True)
            except Exception as e:
                pass

        filler_words = analysis.get("filler_words", {})
        fillers_found = {k: v for k, v in filler_words.items() if v > 0}
        if fillers_found:
            st.markdown(f'<div style="color:#f87171;font-size:0.85rem;margin-bottom:1rem;">Filler words: {", ".join([f"{k}({v})" for k,v in fillers_found.items()])}</div>', unsafe_allow_html=True)

        if analysis.get("practice_tips"):
            with st.expander("💡 Practice Tips"):
                for tip in analysis["practice_tips"]:
                    st.markdown(f"• {tip}")

        if st.button("⏭️ Next Question", type="primary", use_container_width=True, key=f"next_voice_{current_q}"):
            st.session_state["voice_current_q"] = current_q + 1
            st.rerun()


elif voice_questions and current_q >= len(voice_questions):
    answers = st.session_state.get("voice_answers", [])
    if answers:
        avg_conf = sum(a["analysis"].get("confidence_score", 0) for a in answers) / len(answers)
        avg_comm = sum(a["analysis"].get("communication_score", 0) for a in answers) / len(answers)
        avg_clarity = sum(a["analysis"].get("clarity_score", 0) for a in answers) / len(answers)

        st.markdown(f"""
        <div style="background:linear-gradient(135deg,rgba(99,102,241,0.15),rgba(6,182,212,0.1));
             border:1px solid rgba(99,102,241,0.3);border-radius:20px;padding:2rem;text-align:center;margin:1rem 0;">
            <div style="font-size:3rem;">🎙️</div>
            <h2 style="color:var(--text-primary);">Voice Session Complete!</h2>
            <div style="display:grid;grid-template-columns:repeat(3,1fr);gap:1rem;margin-top:1rem;">
                <div><div style="color:#6366f1;font-size:1.8rem;font-weight:800;">{avg_conf:.0f}</div><div style="color:var(--text-secondary);font-size:0.85rem;">Confidence</div></div>
                <div><div style="color:#8b5cf6;font-size:1.8rem;font-weight:800;">{avg_comm:.0f}</div><div style="color:var(--text-secondary);font-size:0.85rem;">Communication</div></div>
                <div><div style="color:#06b6d4;font-size:1.8rem;font-weight:800;">{avg_clarity:.0f}</div><div style="color:var(--text-secondary);font-size:0.85rem;">Clarity</div></div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        if st.button("🔄 Start New Session", use_container_width=True):
            keys_to_clear = [k for k in st.session_state.keys() if k.startswith("voice_")]
            for k in keys_to_clear:
                st.session_state.pop(k, None)
            st.rerun()
    else:
        empty_state("mic", "Session Complete", "No answers were recorded. Try again!")

elif not voice_questions:
    empty_state("mic", "Ready for Voice Interview", "Generate questions above and practice speaking your answers!", "← Select question type and count")
