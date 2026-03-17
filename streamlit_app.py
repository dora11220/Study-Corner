import streamlit as st
import time
import base64
import pandas as pd
import io
from datetime import datetime, timedelta, timezone

st.set_page_config(layout="wide")

# --- 0. GMT+7 TIME LOGIC ---
def get_now_gmt7():
    return datetime.now(timezone.utc) + timedelta(hours=7)

# --- 1. SESSION STATE INITIALIZATION ---
if "last_heard_global_bell" not in st.session_state: st.session_state.last_heard_global_bell = 0.0
if "alarm_trigger" not in st.session_state: st.session_state.alarm_trigger = None

# --- 2. AUDIO ENGINE (With Safety) ---
def get_audio_html(file_name, play_twice=False):
    try:
        with open(file_name, "rb") as f:
            data = f.read()
            b64 = base64.b64encode(data).decode()
            
        if play_twice:
            return f"""
            <audio id="alarmAudio" autoplay style="display:none;">
                <source src="data:audio/mp3;base64,{b64}" type="audio/mp3">
            </audio>
            <script>
                var aud = document.getElementById("alarmAudio");
                aud.volume = 1.0; 
                var playCount = 1;
                aud.onended = function() {{
                    if (playCount < 2) {{
                        playCount++;
                        aud.play();
                    }}
                }};
            </script>
            """
        else:
            return f'<audio autoplay style="display:none;"><source src="data:audio/mp3;base64,{b64}" type="audio/mp3"></audio>'
    except:
        return '<div style="display:none;">Audio file error</div>'

# --- 3. SHARED GLOBAL DATA ---
@st.cache_resource
def get_global_data():
    return {
        "timers": {
            "Phồng Tôm": {"remaining": 0.0, "status": "gray", "last_tick": time.time(), "is_break": False, "start_time": None, "initial_minutes": 0},
            "Phồng Rơm": {"remaining": 0.0, "status": "gray", "last_tick": time.time(), "is_break": False, "start_time": None, "initial_minutes": 0},
            "Thanh Độ":  {"remaining": 0.0, "status": "gray", "last_tick": time.time(), "is_break": False, "start_time": None, "initial_minutes": 0},
            "黄明":     {"remaining": 0.0, "status": "gray", "last_tick": time.time(), "is_break": False, "start_time": None, "initial_minutes": 0}
        },
        "history": [],
        "last_global_bell_trigger": 0.0 
    }

data = get_global_data()
timers = data["timers"]

# Tick logic
current_time = time.time()
for name, t_data in timers.items():
    if t_data["status"] == "red":
        elapsed = current_time - t_data["last_tick"]
        t_data["remaining"] -= elapsed
        
        if t_data["remaining"] <= 0:
            if t_data["start_time"]:
                data["history"].append({
                    "User": name, "Date": get_now_gmt7().strftime("%Y-%m-%d"), 
                    "Start": t_data["start_time"], "End": get_now_gmt7().strftime("%H:%M:%S"), 
                    "Duration": f"{t_data['initial_minutes']} min", "IsBreak": t_data["is_break"]
                })
            st.session_state.alarm_trigger = "break" if t_data["is_break"] else "study"
            t_data["remaining"], t_data["status"], t_data["start_time"] = 0, "gray", None
    t_data["last_tick"] = current_time

# --- 4. STYLES & LAYOUT ---
def get_styles(name):
    t = timers[name]
    if t["is_break"]: return {"bg": "#4682B4", "text": "white"}
    if t["status"] == "red": return {"bg": "#FFB3B3", "text": "#31333F"}
    if t["status"] == "yellow": return {"bg": "#FFFFE0", "text": "#31333F"}
    return {"bg": "#F0F2F6", "text": "#31333F"}

s1, s2, s3, s4 = get_styles("Phồng Tôm"), get_styles("Phồng Rơm"), get_styles("Thanh Độ"), get_styles("黄明")

st.markdown(f"""
<style>
    div[data-testid="stColumn"]:has(.marker-1) {{ background-color: {s1['bg']} !important; padding: 15px; border-radius: 15px; min-height: 520px; }}
    div[data-testid="stColumn"]:has(.marker-2) {{ background-color: {s2['bg']} !important; padding: 15px; border-radius: 15px; min-height: 520px; }}
    div[data-testid="stColumn"]:has(.marker-3) {{ background-color: {s3['bg']} !important; padding: 15px; border-radius: 15px; min-height: 520px; }}
    div[data-testid="stColumn"]:has(.marker-4) {{ background-color: {s4['bg']} !important; padding: 15px; border-radius: 15px; min-height: 520px; }}
    button p {{ color: white !important; font-weight: bold !important; }}
</style>
""", unsafe_allow_html=True)

def add_time(name, minutes):
    if timers[name]["remaining"] <= 0:
        timers[name]["start_time"] = get_now_gmt7().strftime("%H:%M:%S")
        timers[name]["initial_minutes"] = minutes
    else:
        timers[name]["initial_minutes"] += minutes
    timers[name]["remaining"] += minutes * 60
    timers[name]["status"] = "red"

# --- 5. UI ---
col_title, col_bell = st.columns([10, 1])
with col_title: st.title("⏱️ Góc học tập cute")
with col_bell:
    st.write("<br>", unsafe_allow_html=True)
    if st.button("🔔", key="gbell"):
        data["last_global_bell_trigger"] = time.time()
        st.rerun()

col1, col2, col3, col4 = st.columns(4)
users = [
    {"id": 1, "name": "Phồng Tôm", "image": "ptom.jpg", "col": col1},
    {"id": 2, "name": "Phồng Rơm", "image": "prom.jpg", "col": col2},
    {"id": 3, "name": "Thanh Độ",  "image": "Thanh.jpg", "col": col3},
    {"id": 4, "name": "黄明",      "image": "hoang.jpg", "col": col4}
]

for user in users:
    n = user["name"]
    with user["col"]:
        st.markdown(f'<span class="marker-{user["id"]}"></span>', unsafe_allow_html=True)
        st.markdown(f"<h3>{'☕ Break!' if timers[n]['is_break'] else '&nbsp;'}</h3>", unsafe_allow_html=True)
        try: st.image(user["image"], width=80)
        except: st.write("👤")
        st.subheader(n)
        mm, ss = divmod(int(timers[n]["remaining"]), 60)
        st.markdown(f"<h1 style='text-align: center;'>{mm:02d}:{ss:02d}</h1>", unsafe_allow_html=True)
        st.button("+ 50p", key=f"50_{n}", on_click=add_time, args=(n, 50), use_container_width=True)
        ca, cb = st.columns(2)
        ca.button("+ 1p", key=f"1_{n}", on_click=add_time, args=(n, 1), use_container_width=True)
        cb.button("+ 5p", key=f"5_{n}", on_click=add_time, args=(n, 5), use_container_width=True)
        st.button("Giải lao ☕", key=f"b_{n}", on_click=lambda x=n: timers[x].update({"is_break": not timers[x]["is_break"]}), use_container_width=True)
        st.button("Stop/Go", key=f"p_{n}", on_click=lambda x=n: timers[x].update({"status": "yellow" if timers[x]["status"]=="red" else "red"}), use_container_width=True)
        st.button("Reset", key=f"r_{n}", on_click=lambda x=n: timers[x].update({"remaining": 0.0, "status": "gray", "is_break": False, "start_time": None}), use_container_width=True)

# --- 6. HISTORY ---
st.divider()
if data["history"]:
    st.header("📜 Lịch sử")
    df = pd.DataFrame(data["history"])
    st.table(df.iloc[::-1])
    h1, h2 = st.columns(2)
    with h1: 
        if st.button("Clear"): data["history"] = []; st.rerun()
    with h2:
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as wr: df.to_excel(wr, index=False)
        st.download_button("Excel", data=output.getvalue(), file_name="History.xlsx", mime="application/vnd.ms-excel")

# --- 7. AUDIO ---
audio_placeholder = st.empty()
if data["last_global_bell_trigger"] > st.session_state.last_heard_global_bell:
    audio_placeholder.html(get_audio_html("bellButton.mp3"))
    st.session_state.last_heard_global_bell = data["last_global_bell_trigger"]

if st.session_state.alarm_trigger:
    f = "breakEnd.mp3" if st.session_state.alarm_trigger == "break" else "studyEnd.mp3"
    audio_placeholder.html(get_audio_html(f, play_twice=True))
    st.session_state.alarm_trigger = None 

time.sleep(1)
st.rerun()
