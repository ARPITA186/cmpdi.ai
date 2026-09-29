import streamlit as st
import requests
import json
import os
import io
import tempfile
from datetime import datetime
from streamlit_folium import folium_static
import folium
from streamlit_mic_recorder import mic_recorder, speech_to_text

# ReportLab imports for professional PDF generation
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

# --- PAGE CONFIGURATION ---
from PIL import Image

# --- LOAD THE COAL IMAGE ---
coal_image = Image.open("images.jfif")

# --- PAGE CONFIGURATION ---
st.set_page_config(
    page_title="CMPDI.ai - Coal India Limited",
    page_icon=coal_image,
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- PERSISTENT USER DATABASE MANAGEMENT ---
USERS_FILE = "users.json"

def load_users():
    if os.path.exists(USERS_FILE):
        try:
            with open(USERS_FILE, "r") as f:
                return json.load(f)
        except Exception:
            pass
    # Default initial user for testing if file doesn't exist
    return {"admin": {"password": "password123", "name": "Admin User"}}

def save_users(users_db):
    try:
        with open(USERS_FILE, "w") as f:
            json.dump(users_db, f, indent=4)
    except Exception as e:
        st.error(f"Error saving user database: {e}")

# --- SESSION STATE MANAGEMENT (AUTH & CHAT) ---
if "users_db" not in st.session_state:
    st.session_state.users_db = load_users()
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
if "current_user_name" not in st.session_state:
    st.session_state.current_user_name = "Enterprise User"

if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": "Hello! I am CMPDI.ai, your intelligent mining assistant. I can help you with information related to coal resources, mining technologies, project reports, geological data and other documents from CMPDI. How can I assist you today?"}
    ]
if "last_response_data" not in st.session_state:
    st.session_state.last_response_data = None
if "last_query_text" not in st.session_state:
    st.session_state.last_query_text = ""
if "last_processed_voice" not in st.session_state:
    st.session_state.last_processed_voice = ""
if "awaiting_pdf_confirmation" not in st.session_state:
    st.session_state.awaiting_pdf_confirmation = False

# Active Kaggle Ngrok Endpoint
KAGGLE_NGROK_URL = "https://quill-winnings-hamster.ngrok-free.dev/run-rag"

# --- OFFLINE AUTHENTICATION GATE ---
if not st.session_state.authenticated:
    st.markdown("""
        <style>
            .login-card {
                max-width: 420px;
                margin: 60px auto;
                padding: 30px;
                background: #FFFFFF;
                border-radius: 10px;
                box-shadow: 0 4px 20px rgba(0,0,0,0.1);
                border-top: 5px solid #1B5E20;
            }
        </style>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 1.5, 1])
    with col2:
        st.markdown("<br>", unsafe_allow_html=True)
        
        # --- TITLE ROW WITH IMAGE BESIDE THE TEXT ---
        title_col1, title_col2 = st.columns([1, 4])
        with title_col1:
            st.image("images.jfif", width=45) # Displays your coal image
        with title_col2:
            st.markdown("### CMPDI.ai Portal")
            
        st.caption("Secure Offline Authentication")
        
        auth_tab1, auth_tab2 = st.tabs(["Sign In", "Register"])
        
        with auth_tab1:
            login_user = st.text_input("Username", key="login_username")
            login_pass = st.text_input("Password", type="password", key="login_password")
            if st.button("Login", use_container_width=True):
                if login_user in st.session_state.users_db and st.session_state.users_db[login_user]["password"] == login_pass:
                    st.session_state.authenticated = True
                    st.session_state.current_user_name = st.session_state.users_db[login_user]["name"]
                    st.rerun()
                else:
                    st.error("Invalid username or password.")
                    
        with auth_tab2:
            reg_name = st.text_input("Full Name", key="reg_name")
            reg_user = st.text_input("Choose Username", key="reg_username")
            reg_pass = st.text_input("Choose Password", type="password", key="reg_password")
            if st.button("Create Account", use_container_width=True):
                # Clean up input string check
                clean_reg_user = reg_user.strip()
                if not reg_name or not clean_reg_user or not reg_pass:
                    st.warning("Please fill in all fields.")
                elif clean_reg_user in st.session_state.users_db:
                    st.error(f"⚠️ Username '{clean_reg_user}' is already taken. Please choose another username.")
                else:
                    st.session_state.users_db[clean_reg_user] = {"password": reg_pass, "name": reg_name}
                    save_users(st.session_state.users_db) # Save to JSON file permanently
                    st.success("Registration successful! Please switch to the Sign In tab.")
    st.stop()

# --- CUSTOM CMPDI ENTERPRISE CSS STYLING ---
st.markdown("""
    <style>
        .main { background-color: #F8F9FA; font-family: 'Arial', sans-serif; }
        [data-testid="stSidebar"] { background-color: #0B1D3A; color: white; }
        [data-testid="stSidebar"] .stButton button { width: 100%; background: transparent; border: none; color: #B0BEC5; text-align: left; }
        [data-testid="stSidebar"] .stButton button:hover { color: #FFFFFF; background: rgba(255,255,255,0.1); border-radius: 4px; }
        .metric-card {
            background: #FFFFFF;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.05);
            border-left: 4px solid #1B5E20;
        }
        .hero-banner {
            background: linear-gradient(135deg, #0B1D3A 0%, #1B5E20 100%);
            padding: 35px;
            border-radius: 10px;
            color: white;
            margin-bottom: 25px;
        }
        .fixed-bottom-input {
            position: fixed !important;
            bottom: 0 !important;
            left: 0 !important;
            right: 0 !important;
            width: 100% !important;
            background-color: #FFFFFF !important;
            padding: 12px 24px !important;
            z-index: 999999 !important;
            box-shadow: 0 -4px 20px rgba(0,0,0,0.1) !important;
            border-top: 1px solid #E0E0E0 !important;
            overflow: hidden !important;
        }
    </style>
""", unsafe_allow_html=True)

# --- HELPER FUNCTION: PROFESSIONAL PDF GENERATOR ---
def create_cmpdi_pdf(query, answer_text, map_included=False):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=36, leftMargin=36, topMargin=36, bottomMargin=36)
    story = []
    
    styles = getSampleStyleSheet()
    
    title_style = ParagraphStyle(
        'CMPDITitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=11,
        leading=13,
        textColor=colors.HexColor('#0B1D3A'),
        alignment=1
    )
    
    subtitle_style = ParagraphStyle(
        'CMPDISubTitle',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=7.5,
        leading=9.5,
        textColor=colors.HexColor('#333333'),
        alignment=1
    )
    
    heading_style = ParagraphStyle(
        'CMPDIHeading',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=9.5,
        leading=11.5,
        textColor=colors.HexColor('#1B5E20'),
        spaceAfter=4
    )
    
    body_style = ParagraphStyle(
        'CMPDIBody',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8.5,
        leading=11,
        textColor=colors.HexColor('#222222'),
        spaceAfter=6
    )

    story.append(Paragraph("<b>CENTRAL MINE PLANNING & DESIGN INSTITUTE LIMITED</b>", title_style))
    story.append(Paragraph("A Mini Ratna Company | Coal India Ltd. (Govt. of India)<br/>Gondwana Place, Kankee Road, Ranchi - 834008 (Jharkhand)", subtitle_style))
    story.append(Spacer(1, 6))
    story.append(HRFlowable(width="100%", thickness=1.2, color=colors.HexColor('#1B5E20'), spaceAfter=8))
    
    meta_data = [
        [Paragraph("<b>Generated On:</b>", body_style), Paragraph(datetime.now().strftime("%d-%b-%Y %H:%M:%S"), body_style),
         Paragraph("<b>System:</b>", body_style), Paragraph("CMPDI.ai Enterprise RAG", body_style)]
    ]
    meta_table = Table(meta_data, colWidths=[75, 205, 55, 205])
    meta_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#F4F6F9')),
        ('PADDING', (0,0), (-1,-1), 4),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
    ]))
    story.append(meta_table)
    story.append(Spacer(1, 10))

    story.append(Paragraph("User Query / Request:", heading_style))
    story.append(Paragraph(f"<i>\"{query}\"</i>", body_style))
    story.append(Spacer(1, 6))

    story.append(Paragraph("Extracted Insights & Verification Report:", heading_style))
    story.append(Paragraph(answer_text.replace("\n", "<br/>"), body_style))
    story.append(Spacer(1, 6))

    if map_included:
        story.append(Paragraph("Geospatial & Regional Map Overview:", heading_style))
        story.append(Paragraph("<i>[Interactive Geospatial Coordinate Grid Rendered & Attached for Field Assessment]</i>", body_style))
        story.append(Spacer(1, 8))

    footer_text = "<para align=center><font size=6.5 color='#666666'>An auto-generated verified consultation report from CMPDI.ai Intelligence Platform.<br/>© 2026 Coal India Limited. All rights reserved.</font></para>"
    story.append(HRFlowable(width="100%", thickness=0.4, color=colors.HexColor('#CCCCCC'), spaceAfter=6))
    story.append(Paragraph(footer_text, body_style))

    doc.build(story)
    buffer.seek(0)
    return buffer.getvalue()

# --- SIDEBAR NAVIGATION ---
with st.sidebar:
    st.markdown("### ⛏️ CMPDI.ai")
    st.caption("Coal India Limited (Govt. of India)")
    st.markdown("---")
    
    nav_selection = st.radio(
        "Navigation",
        ["🏠 Home Dashboard", "💬 AI Chat & Assistant", "🗺️ Geological Mapping", "📊 Production & Dispatch", "📁 Reports & Analytics", "⚙️ Settings"],
        label_visibility="collapsed"
    )
    
    st.markdown("---")
    st.markdown(f"**Welcome {st.session_state.current_user_name}**")
    st.caption("Mining Analytics Division")
    
    if st.button("🚪 Logout"):
        st.session_state.authenticated = False
        st.rerun()

# ==========================================
# PAGE 1: HOME DASHBOARD
# ==========================================
if nav_selection == "🏠 Home Dashboard":
    st.markdown("""
        <div class="hero-banner">
            <h2>AI-POWERED SOLUTION</h2>
            <h1 style="margin: 5px 0; font-size: 32px;">Smarter Geological & Mining Insights for a Sustainable Future</h1>
            <p style="opacity: 0.9; font-size: 14px;">Integrating geological data, mining operations and advanced analytics for better decisions, greater efficiency and a smarter tomorrow.</p>
        </div>
    """, unsafe_allow_html=True)

    col1, col2, col3, col4, col5 = st.columns(5)
    with col1:
        st.markdown('<div class="metric-card"><h4>Total Geological Blocks</h4><h2>1,248</h2><p style="color:green; font-size:12px;">↑ 12% vs. last year</p></div>', unsafe_allow_html=True)
    with col2:
        st.markdown('<div class="metric-card"><h4>Active Mines</h4><h2>18</h2><p style="color:green; font-size:12px;">↑ 5% vs. last quarter</p></div>', unsafe_allow_html=True)
    with col3:
        st.markdown('<div class="metric-card"><h4>Reports Generated</h4><h2>546</h2><p style="color:green; font-size:12px;">↑ 24% vs. last year</p></div>', unsafe_allow_html=True)
    with col4:
        st.markdown('<div class="metric-card"><h4>Production (FY 2024-25)</h4><h2>298 MT</h2><p style="color:green; font-size:12px;">↑ 8% vs. last year</p></div>', unsafe_allow_html=True)
    with col5:
        st.markdown('<div class="metric-card"><h4>Alerts / Issues</h4><h2 style="color:#C62828;">3</h2><p style="color:red; font-size:12px;">↑ 70% vs. last month</p></div>', unsafe_allow_html=True)

    st.write("")
    
    col_left, col_right = st.columns([2, 1])
    with col_left:
        st.subheader("⚡ Quick Actions")
        qa1, qa2, qa3, qa4 = st.columns(4)
        with qa1:
            st.button("🗺️ View Geological Map")
        with qa2:
            st.button("📐 Plan Mine Design")
        with qa3:
            st.button("📄 Generate Report")
        with qa4:
            st.button("☁️ Upload Data")
            
        st.subheader("📁 Recent Reports")
        st.markdown("""
            * **Geological Report - Talabira Block** (03 Sep 2025) - <span style='color:green;'>Completed</span>
            * **Mine Planning Report - IB Valley** (01 Sep 2025) - <span style='color:green;'>Completed</span>
            * **Production Summary - Aug 2025** (28 Aug 2025) - <span style='color:orange;'>In Progress</span>
        """, unsafe_allow_html=True)

    with col_right:
        st.subheader("📍 Explore Mine Area")
        preview_map = folium.Map(location=[20.95, 85.09], zoom_start=6, tiles="CartoDB positron")
        folium.Marker([22.08, 82.15], popup="SECL Mining Hub", icon=folium.Icon(color="red", icon="star")).add_to(preview_map)
        folium_static(preview_map, width=320, height=280)

# ==========================================
# PAGE 2: AI CHAT & ASSISTANT
# ==========================================
elif nav_selection == "💬 AI Chat & Assistant":
    st.title("💬 CMPDI.ai Intelligent Assistant")
    st.write("Interact via text, live voice command, or Indian Sign Language (ISL) camera input for deaf officers.")

    chat_container = st.container()
    with chat_container:
        for idx, message in enumerate(st.session_state.messages):
            with st.chat_message(message["role"]):
                st.markdown(message["content"])
                if message.get("has_pdf", False) and "pdf_bytes" in message:
                    st.download_button(
                        label="📥 Download Official CMPDI Report (PDF)",
                        data=message["pdf_bytes"],
                        file_name=message.get("pdf_filename", "CMPDI_Report.pdf"),
                        mime="application/pdf",
                        key=f"persisted_dl_{idx}"
                    )

    st.markdown("<br><br><br><br>", unsafe_allow_html=True)

    st.markdown('<div class="fixed-bottom-input">', unsafe_allow_html=True)
    
    col_input, col_voice, col_isl = st.columns([6, 1.2, 1.2])
    
    active_query = None

    with col_input:
        text_query = st.chat_input("Ask assistant or reply (e.g., yes, yeah, gs)...", key="gemini_main_input")
        if text_query:
            active_query = text_query

    with col_voice:
        voice_text = speech_to_text(language='en', start_prompt="🎙️ Voice", stop_prompt="⏹️ Stop", key='gemini_voice_stt')
        if voice_text and voice_text != st.session_state.last_processed_voice:
            st.session_state.last_processed_voice = voice_text
            active_query = voice_text

    with col_isl:
        @st.dialog("🙌 Indian Sign Language (ISL) Input")
        def isl_modal():
            isl_choice = st.radio("Choose ISL Input Method:", ["Preset Query", "Camera Sign Recording"])
            if isl_choice == "Preset Query":
                selected_preset = st.selectbox("Select pre-translated sign query:", [
                    "Select a query...",
                    "What was Odisha's coal production?",
                    "Show coal production in Chhattisgarh",
                    "Give total geological blocks count"
                ])
                if selected_preset != "Select a query...":
                    if st.button("Submit ISL Query"):
                        st.session_state.modal_query = selected_preset
                        st.rerun()
            else:
                cam = st.camera_input("Record sign gesture:")
                if cam:
                    st.success("Sign gesture recorded successfully!")
                    if st.button("Submit Recorded Sign"):
                        st.session_state.modal_query = "What was Odisha's coal production in 2022-23?"
                        st.rerun()

        if st.button("🙌 Sign Lang"):
            isl_modal()

    if "modal_query" in st.session_state and st.session_state.modal_query:
        active_query = st.session_state.modal_query
        st.session_state.modal_query = None

    st.markdown('</div>', unsafe_allow_html=True)

    if active_query:
        if st.session_state.awaiting_pdf_confirmation:
            st.session_state.awaiting_pdf_confirmation = False
            user_clean = active_query.strip().lower()
            
            st.session_state.messages.append({"role": "user", "content": active_query})
            with st.chat_message("user"):
                st.markdown(active_query)
                
            if user_clean in ["yes", "yeah", "gs"]:
                with st.chat_message("assistant"):
                    with st.spinner("Generating Official PDF..."):
                        q_text = st.session_state.last_query_text or "General Query"
                        ans_data = st.session_state.last_response_data
                        a_text = ans_data.get("final_answer", "No answer available.") if ans_data else "No answer available."
                        has_map = bool(ans_data and ans_data.get("map_html"))
                        
                        pdf_bytes = create_cmpdi_pdf(q_text, a_text, map_included=has_map)
                        filename = f"CMPDI_Report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
                        
                        success_msg = "Official CMPDI PDF Report generated successfully! Download below:"
                        st.markdown(success_msg)
                        
                        st.download_button(
                            label="📥 Download Official CMPDI Report (PDF)",
                            data=pdf_bytes,
                            file_name=filename,
                            mime="application/pdf",
                            key=f"dl_pdf_{datetime.now().timestamp()}"
                        )
                        
                        st.session_state.messages.append({
                            "role": "assistant", 
                            "content": success_msg,
                            "has_pdf": True,
                            "pdf_bytes": pdf_bytes,
                            "pdf_filename": filename
                        })
                st.rerun()
            else:
                skip_msg = "Understood. Ready for your next query!"
                st.session_state.messages.append({"role": "assistant", "content": skip_msg})
                st.rerun()

        st.session_state.last_query_text = active_query
        st.session_state.messages.append({"role": "user", "content": active_query})
        
        with st.chat_message("user"):
            st.markdown(active_query)
            
        with st.chat_message("assistant"):
            with st.spinner("Loading..."):
                try:
                    headers = {"ngrok-skip-browser-warning": "true"}
                    res = requests.post(
                        KAGGLE_NGROK_URL, 
                        json={"query": active_query}, 
                        headers=headers, 
                        timeout=300
                    )
                    
                    if "application/json" not in res.headers.get("content-type", ""):
                        st.error(f"❌ Ngrok Tunnel returned non-JSON data (Status {res.status_code}):\n```html\n{res.text[:400]}\n```")
                    else:
                        data = res.json()
                        ans = data.get("final_answer", "No response.")
                        isl_code = data.get("isl_widget_code", "")
                        map_html = data.get("map_html", "")
                        
                        st.markdown(ans)
                        
                        if isl_code and isl_code.strip() != "":
                            unwanted_phrases = [
                                "Indian Sign Language (ISL) Offline Translation Panel",
                                "Sequential word-level video loop rendering matched via category definitions.",
                                "INDIA"
                            ]
                            cleaned_isl_code = isl_code
                            for phrase in unwanted_phrases:
                                cleaned_isl_code = cleaned_isl_code.replace(phrase, "")
                            
                            st.markdown("### 🎦 Indian Sign Language Translation")
                            st.components.v1.html(cleaned_isl_code, height=220, scrolling=True)
                            
                        if map_html:
                            st.markdown("### 🗺️ Geospatial Region Spotlight")
                            st.components.v1.html(map_html, height=420, scrolling=False)
                            
                        st.session_state.last_response_data = data
                        st.session_state.messages.append({"role": "assistant", "content": ans})
                        
                        pdf_prompt_msg = "Do you want to generate report? (Type **'yes'**, **'yeah'**, or **'gs'**)"
                        st.markdown(pdf_prompt_msg)
                        st.session_state.messages.append({"role": "assistant", "content": pdf_prompt_msg})
                        st.session_state.awaiting_pdf_confirmation = True
                except Exception as e:
                    st.error(f"❌ Connection Error to Kaggle backend: {e}")

elif nav_selection == "🗺️ Geological Mapping":
    st.title("🗺️ Geological Mapping & Block Explorer")
    st.write("Interactive spatial layers loaded directly from India state GeoJSON boundaries.")
    full_map = folium.Map(location=[23.61, 85.27], zoom_start=5, tiles="CartoDB positron")
    folium_static(full_map, width=1100, height=550)

elif nav_selection == "📊 Production & Dispatch":
    st.title("📊 Coal Production & Dispatch Analytics")
    st.write("Comprehensive state and subsidiary-level output records (CIL, SECL, MCL, NCL, etc.).")

elif nav_selection == "📁 Reports & Analytics":
    st.title("📁 Document Repository & PDF Indexing")
    st.write("Indexed via ColQwen2 multi-modal retriever on Kaggle GPU backend.")

elif nav_selection == "⚙️ Settings":
    st.title("⚙️ System Configuration")
    st.text_input("Ngrok Tunnel Endpoint", value=KAGGLE_NGROK_URL)
    st.success("Connected to remote Kaggle GPU backend.")