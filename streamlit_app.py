import streamlit as st
import streamlit.components.v1 as components
import time
import base64
import pandas as pd
import io
from datetime import datetime, timedelta, timezone

st.set_page_config(layout="wide")

# --- 0. TIME & SESSION ---
def get_now_gmt7():
    return datetime.now(timezone.utc) + timedelta(hours=7)

if "last_bell_time" not in st.session_state: st.session_state.last_bell_time = 0.0
if "heard_bell" not in st.session_state: st.session_state.heard_bell = 0.0
if "alarm_trigger" not in st.session_state: st.session_state.alarm_trigger = None

# --- 1. THE STATIC ASSETS (Loads ONLY ONCE) ---
@st.cache_data
def get_base64(file_path):
    try:
        with open(file_path, "rb") as f:
            return base64.b64encode(f.read()).decode()
    except: return ""

BELL_B64 = get_base64("bellButton.mp3")
STUDY_B64 = get_base64("studyEnd.mp3")
BREAK_B64 = get_base64("breakEnd.mp3")
BG_B64 = get_base64("background.jpg")

def inject_audio_manager():
    components.html(f"""
        <div id="audio-container" style="display:none;">
            <audio id="bell_snd"><source src="data:audio/mp3;base64,{BELL_B64}"></audio>
            <audio id="study_snd"><source src="data:audio/mp3;base64,{STUDY_B64}"></audio>
            <audio id="break_snd"><source src="data:audio/mp3;base64,{BREAK_B64}"></audio>
        </div>
        <script>
            window.parent.playSnd = function(type) {{
                var s = document.getElementById(type + "_snd");
                if(s) {{
                    s.currentTime = 0;
                    s.play().catch(e => console.log("Audio play blocked"));
                    if(type !== 'bell') {{
                        s.onended = function() {{ this.onended = null; this.play(); }};
                    }}
                }}
            }};
        </script>
    """, height=0)

@st.cache_resource
def get_global_data():
    return {
        "timers": {
            "Phồng Tôm": {"remaining": 0.0, "status": "gray", "last_tick": time.time(), "is_break": False, "start_time": None, "initial_minutes": 0},
            "Phồng Rơm": {"remaining": 0.0, "status": "gray", "last_tick": time.time(), "is_break": False, "start_time": None, "initial_minutes": 0},
            "Thanh Độ":  {"remaining": 0.0, "status": "gray", "last_tick": time.time(), "is_break": False, "start_time": None, "initial_minutes": 0},
            "黄明":      {"remaining": 0.0, "status": "gray", "last_tick": time.time(), "is_break": False, "start_time": None, "initial_minutes": 0}
        },
        "history": [],
        "last_bell_ringer": None,
        "last_bell_time": 0.0
    }

data = get_global_data()

# --- 2. STATIC UI (Never refreshes) ---
inject_audio_manager() 
st.markdown(f"""
<style>
    [data-testid="stAppViewContainer"] {{
        background-image: url("data:image/jpg;base64,{BG_B64}");
        background-size: 130% 130%; background-attachment: fixed;
        animation: diagonalMove 40s ease-in-out infinite alternate;
    }}
    @keyframes diagonalMove {{ 0% {{ background-position: 0% 0%; }} 100% {{ background-position: 100% 100%; }} }}
    .stApp h1 {{ color: white !important; text-shadow: 3px 3px 6px rgba(0,0,0,0.7); }}
</style>
""", unsafe_allow_html=True)

st.title("⏱️ Góc học tập cute")

# --- 3. DYNAMIC DASHBOARD (Refreshes smoothly every 1 second) ---
@st.fragment(run_every=1)
def dashboard_ui():
    cur = time.time()
    
    # Timer Logic
    for name, t in data["timers"].items():
        if t["status"] == "red":
            t["remaining"] -= (cur - t["last_tick"])
            if t["remaining"] <= 0:
                if t["start_time"]:
                    data["history"].append({"User": name, "Date": get_now_gmt7().strftime("%Y-%m-%d"), "Start": t["start_time"], "End": get_now_gmt7().strftime("%H:%M:%S"), "Duration": f"{t['initial_minutes']} min", "IsBreak": t["is_break"]})
                st.session_state.alarm_trigger = "break" if t["is_break"] else "study"
                t.update({"remaining": 0, "status": "gray", "start_time": None})
        t["last_tick"] = cur

    # Dynamic Styles for Timer Boxes
    def get_styles(name):
        t = data["timers"][name]
        is_ringing = (data["last_bell_ringer"] == name and (time.time() - data["last_bell_time"] < 5))
        if is_ringing: return {"bg": "rgba(255, 250, 205, 0.95)", "text": "#31333F", "glow": "0px 0px 40px 20px rgba(255, 215, 0, 0.9)"}
        if t["is_break"]: return {"bg": "rgba(70, 130, 180, 0.85)", "text": "white", "glow": "none"}
        if t["status"] == "red": return {"bg": "rgba(255, 179, 179, 0.9)", "text": "#31333F", "glow": "none"}
        if t["
