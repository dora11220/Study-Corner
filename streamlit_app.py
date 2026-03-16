import streamlit as st
import time
import base64
import pandas as pd
from datetime import datetime

st.set_page_config(layout="wide")

# 1. Shared Global Memory
@st.cache_resource
def get_global_data():
    return {
        "timers": {
            "Phồng Tôm": {"remaining": 0.0, "status": "gray", "last_tick": time.time(), "is_break": False, "start_time": None, "initial_minutes": 0, "chat_requested": False},
            "Phồng Rơm": {"remaining": 0.0, "status": "gray", "last_tick": time.time(), "is_break": False, "start_time": None, "initial_minutes": 0, "chat_requested": False},
            "Thành Đỗ":  {"remaining": 0.0, "status": "gray", "last_tick": time.time(), "is_break": False, "start_time": None, "initial_minutes": 0, "chat_requested": False}
        },
        "history": [] 
    }

data = get_global_data()
timers = data["timers"]

# 2. Local Audio Logic
def play_local_audio(file_path):
    try:
        with open(file_path, "rb") as f:
            audio_bytes = f.read()
            audio_base64 = base64.b64encode(audio_bytes).decode()
            audio_tag = f'<audio autoplay="true"><source src="data:audio/mp3;base64,{audio_base64}" type="audio/mp3"></audio>'
            st.components.v1.html(audio_tag, height=0)
    except FileNotFoundError:
        pass # Silently skip if file is missing

# 3. Timer Engine
current_time = time.time()
active_alarm = None

for name, t_data in timers.items():
    if t_data["status"] == "red":
        elapsed = current_time - t_data["last_tick"]
        t_data["remaining"] -= elapsed
        
        if t_data["remaining"] <= 0:
            active_alarm = "breakEnd.mp3" if t_data["is_break"] else "studyEnd.mp3"
            if t_data["start_time"]:
                data["history"].append({
                    "User": name,
                    "Date": datetime.now().strftime("%Y-%m-%d"),
                    "Start": t_data["start_time"],
                    "End": datetime.now().strftime("%H:%M:%S"),
                    "Duration": f"{t_data['initial_minutes']} min",
                    "Mode": "Break" if t_data["is_break"] else "Study"
                })
            t_data.update({"remaining": 0, "status": "gray", "start_time": None})
    t_data["last_tick"] = current_time

# 4. FIXED CSS (Surgical targeting & Growing Button)
def get_styles(name):
    t = timers[name]
    if t["is_break"]: return {"bg": "#4682B4", "text": "white"} # Steel Blue
    if t["status"] == "red": return {"bg": "#FFB3B3", "text": "#31333F"} # Soft Red
    return {"bg": "#F0F2F6", "text": "#31333F"} # Default Gray

s1, s2, s3 = get_styles("Phồng Tôm"), get_styles("Phồng Rơm"), get_styles("Thành Đỗ")

st.markdown(f"""
<style>
    /* 1. Target ONLY the 3 main top-level columns to prevent color bleeding */
    [data-testid="stMain"] [data-testid="stHorizontalBlock"]:first-of-type > div[data-testid="stColumn"]:nth-of-type(1) {{ background-color: {s1['bg']} !important; padding: 25px; border-radius: 20px; }}
    [data-testid="stMain"] [data-testid="stHorizontalBlock"]:first-of-type > div[data-testid="stColumn"]:nth-of-type(2) {{ background-color: {s2['bg']} !important; padding: 25px; border-radius: 20px; }}
    [data-testid="stMain"] [data-testid="stHorizontalBlock"]:first-of-type > div[data-testid="stColumn"]:nth-of-type(3) {{ background-color: {s3['bg']} !important; padding: 25px; border-radius: 20px; }}
    
    /* Dynamic Text Colors */
    [data-testid="stMain"] [data-testid="stHorizontalBlock"]:first-of-type > div[data-testid="stColumn"]:nth-of-type(1) :is(h1,h2,h3,p) {{ color: {s1['text']} !important; }}
    [data-testid="stMain"] [data-testid="stHorizontalBlock"]:first-of-type > div[data-testid="stColumn"]:nth-of-type(2) :is(h1,h2,h3,p) {{ color: {s2['text']} !important; }}
    [data-testid="stMain"] [data-testid="stHorizontalBlock"]:first-of-type > div[data-testid="stColumn"]:nth-of-type(3) :is(h1,h2,h3,p) {{ color: {s3['text']} !important; }}

    /* 2. Chat Button Styling (GROW EFFECT & BRIGHT BLUE) */
    button[key*="chat_"] {{
        transition: all 0.3s ease-in-out !important;
        border: none !important;
    }}
    
    /* This makes the active chat button bigger and brighter */
    .chat-active button {{
        background-color: #00EAFF !important; /* Neon Bright Blue */
        transform: scale(1.15) !important;   /* Grows in size */
        box-shadow: 0px 0px 15px #00EAFF !important;
        color: black !important;
    }}

    /* Global button text */
    button p {{ color: white !important; font-weight: bold !important; }}
</style>
""", unsafe_allow_html=True)

if active_alarm: play_local_audio(active_alarm)

# 5. UI Layout
st.title("⏱️ Góc học tập cute")
cols = st.columns(3)
users = [("Phồng Tôm", "ptom.jpg"), ("Phồng Rơm", "prom.jpg"), ("Thành Đỗ", "Thanh.jpg")]

for i, (name, img) in enumerate(users):
    with cols[i]:
        # Chat Button Wrapper
        chat_active_class = "chat-active" if timers[name]["chat_requested"] else ""
        st.markdown(f'<div class="{chat_active_class}">', unsafe_allow_html=True)
        st.button("💬 want to chat!" if timers[name]["chat_requested"] else "💬", 
                  key=f"chat_{name}", 
                  on_click=lambda n=name: timers[n].update({"chat_requested": not timers[n]["chat_requested"]}))
        st.markdown('</div>', unsafe_allow_html=True)

        st.markdown(f"<h2>{'☕ Break!' if timers[name]['is_break'] else '&nbsp;'}</h2>", unsafe_allow_html=True)
        st.image(img, width=100)
        st.subheader(name)
        
        mins, secs = divmod(int(timers[name]["remaining"]), 60)
        st.markdown(f"<h1 style='text-align: center;'>{mins:02d}:{secs:02d}</h1>", unsafe_allow_html=True)
        
        # Action Buttons
        st.button("+ 50 phút", key=f"50_{name}", on_click=lambda n=name: timers[n].update({"remaining": timers[n]["remaining"]+3000, "status": "red", "start_time": datetime.now().strftime("%H:%M:%S"), "initial_minutes": 50}), use_container_width=True)
        
        c1, c2 = st.columns(2)
        c1.button("+ 1p", key=f"1_{name}", on_click=lambda n=name: timers[n].update({"remaining": timers[n]["remaining"]+60, "status": "red", "start_time": datetime.now().strftime("%H:%M:%S") if timers[n]["remaining"]==0 else timers[n]["start_time"]}), use_container_width=True)
        c2.button("+ 5p", key=f"5_{name}", on_click=lambda n=name: timers[n].update({"remaining": timers[n]["remaining"]+300, "status": "red", "start_time": datetime.now().strftime("%H:%M:%S") if timers[n]["remaining"]==0 else timers[n]["start_time"]}), use_container_width=True)
        
        st.button("Chế độ giải lao ☕", key=f"b_{name}", on_click=lambda n=name: timers[n].update({"is_break": not timers[n]["is_break"]}), use_container_width=True)
        st.button("Dừng / Tiếp tục", key=f"p_{name}", on_click=lambda n=name: timers[n].update({"status": "yellow" if timers[n]["status"]=="red" else "red"}), use_container_width=True)
        st.button("Reset", key=f"r_{name}", on_click=lambda n=name: timers[n].update({"remaining": 0.0, "status": "gray", "is_break": False, "start_time": None}), use_container_width=True)

# 6. History
st.divider()
st.header("📜 Lịch sử học tập")
if data["history"]:
    df = pd.DataFrame(data["history"])
    st.table(df.style.apply(lambda row: ['color: #1E90FF' if row['Mode'] == 'Break' else 'color: black']*len(row), axis=1))
    if st.button("🗑️ Clear All History"):
        data["history"] = []
        st.rerun()

time.sleep(1)
st.rerun()
