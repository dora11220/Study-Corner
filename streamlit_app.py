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
        if t["status"] == "yellow": return {"bg": "rgba(255, 255, 224, 0.9)", "text": "#31333F", "glow": "none"}
        return {"bg": "rgba(240, 242, 246, 0.85)", "text": "#31333F", "glow": "none"}

    s = {n: get_styles(n) for n in data["timers"]}

    st.markdown(f"""
    <style>
        {" ".join([f'''
        div[data-testid="stColumn"]:has(.marker-{i+1}) {{ 
            background-color: {s[n]['bg']} !important; box-shadow: {s[n]['glow']};
            padding: 20px; border-radius: 20px; min-height: 600px; 
            transition: all 0.6s cubic-bezier(0.175, 0.885, 0.32, 1.275);
            backdrop-filter: blur(8px); border: 1px solid rgba(255,255,255,0.3);
        }}
        div[data-testid="stColumn"]:has(.marker-{i+1}) h1 {{ color: {s[n]['text']} !important; }}
        ''' for i, n in enumerate(data["timers"])])}
    </style>
    """, unsafe_allow_html=True)

    # Timer UI Columns
    cols = st.columns(4)
    users = [("Phồng Tôm", "ptom.jpg"), ("Phồng Rơm", "prom.jpg"), ("Thanh Độ", "Thanh.jpg"), ("黄明", "hoang.jpg")]

    def ring_bell(name):
        data["last_bell_ringer"] = name
        data["last_bell_time"] = time.time()

    for i, (n, img) in enumerate(users):
        with cols[i]:
            st.markdown(f'<span class="marker-{i+1}"></span>', unsafe_allow_html=True)
            if st.button("🔔 Rung chuông", key=f"bl_{n}", use_container_width=True): ring_bell(n)
            st.markdown(f"<h2>{'☕' if data['timers'][n]['is_break'] else '&nbsp;'}</h2>", unsafe_allow_html=True)
            try: st.image(img, width=100)
            except: st.write("👤")
            st.subheader(n)
            mm, ss = divmod(int(data["timers"][n]["remaining"]), 60)
            st.markdown(f"<h1 style='text-align: center;'>{mm:02d}:{ss:02d}</h1>", unsafe_allow_html=True)
            
            if st.button("+ 50p", key=f"50_{n}", use_container_width=True):
                t = data["timers"][n]
                if t["remaining"] <= 0: t["start_time"], t["initial_minutes"] = get_now_gmt7().strftime("%H:%M:%S"), 50
                else: t["initial_minutes"] += 50
                t["remaining"] += 3000
                t["status"] = "red"
            
            st.button("Giải lao ☕", key=f"b_{n}", on_click=lambda x=n: data["timers"][x].update({"is_break": not data["timers"][x]["is_break"]}), use_container_width=True)
            st.button("Stop/Go", key=f"p_{n}", on_click=lambda x=n: data["timers"][x].update({"status": "yellow" if data["timers"][x]["status"]=="red" else "red"}), use_container_width=True)
            st.button("Reset", key=f"r_{n}", on_click=lambda x=n: data["timers"][x].update({"remaining": 0.0, "status": "gray", "is_break": False, "start_time": None}), use_container_width=True)

    # History Table
    st.divider()
    st.markdown("<h2 style='color: white; text-shadow: 2px 2px 4px black;'>📜 Lịch sử học tập:</h2>", unsafe_allow_html=True)
    if data["history"]:
        table = '<table style="width:100%; border-collapse: collapse; background-color: rgba(30, 30, 30, 0.9); border-radius: 12px; overflow: hidden; color: white;">'
        table += '<tr style="border-bottom: 2px solid #555; background-color: rgba(0, 0, 0, 0.5); text-align: left;"><th style="padding: 12px;">User</th><th style="padding: 12px;">Date</th><th style="padding: 12px;">Start</th><th style="padding: 12px;">End</th><th style="padding: 12px;">Duration</th></tr>'
        for e in reversed(data["history"]):
            c = "#00BFFF" if e["IsBreak"] else "white"
            table += f'<tr style="color: {c}; border-bottom: 1px solid #444;"><td style="padding: 12px;">{e["User"]} {"☕" if e["IsBreak"] else "📚"}</td><td style="padding: 12px;">{e["Date"]}</td><td style="padding: 12px;">{e["Start"]}</td><td style="padding: 12px;">{e["End"]}</td><td style="padding: 12px;">{e["Duration"]}</td></tr>'
        st.markdown(table + '</table><br>', unsafe_allow_html=True)
        h1, h2 = st.columns(2)
        with h1: 
            if st.button("🗑️ Clear All History", use_container_width=True): data["history"].clear()
        with h2:
            df = pd.DataFrame(data["history"])
            out = io.BytesIO()
            with pd.ExcelWriter(out) as wr: df.to_excel(wr, index=False)
            st.download_button("📥 Tải file Excel", data=out.getvalue(), file_name="History.xlsx", use_container_width=True)

    # Trigger Audio Events natively within the fragment
    if data["last_bell_time"] > st.session_state.heard_bell:
        components.html(f"<script>window.parent.playSnd('bell');</script>", height=0)
        st.session_state.heard_bell = data["last_bell_time"]

    if st.session_state.alarm_trigger:
        components.html(f"<script>window.parent.playSnd('{st.session_state.alarm_trigger}');</script>", height=0)
        st.session_state.alarm_trigger = None

# Initialize the dynamic part
dashboard_ui()
