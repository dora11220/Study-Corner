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
        st.error(f"Missing audio file: {file_path}")

# 3. Timer Engine & History
current_time = time.time()
active_alarm = None # Tracks if studyEnd or breakEnd should play

for name, t_data in timers.items():
    if t_data["status"] == "red":
        elapsed = current_time - t_data["last_tick"]
        t_data["remaining"] -= elapsed
        
        if t_data["remaining"] <= 0:
            # Determine alarm and mode
            mode_label = "Break" if t_data["is_break"] else "Study"
            active_alarm = "breakEnd.mp3" if t_data["is_break"] else "studyEnd.mp3"
            
            # Record history
            if t_data["start_time"]:
                data["history"].append({
                    "User": name,
                    "Date": datetime.now().strftime("%Y-%m-%d"),
                    "Start": t_data["start_time"],
                    "End": datetime.now().strftime("%H:%M:%S"),
                    "Duration": f"{t_data['initial_minutes']} min",
                    "Mode": mode_label
                })
            
            t_data["remaining"] = 0
            t_data["status"] = "gray"
            t_data["start_time"] = None
            
    t_data["last_tick"] = current_time

# 4. CSS Styling
def get_styles(name):
    t = timers[name]
    if t["is_break"]: return {"bg": "#4682B4", "text": "white"}
    if t["status"] == "red": return {"bg": "#FFB3B3", "text": "#31333F"}
    if t["status"] == "yellow": return {"bg": "#FFFFE0", "text": "#31333F"}
    return {"bg": "#F0F2F6", "text": "#31333F"}

s1, s2, s3 = get_styles("Phồng Tôm"), get_styles("Phồng Rơm"), get_styles("Thành Đỗ")

st.markdown(f"""
<style>
    [data-testid="stHorizontalBlock"] > div[data-testid="stColumn"]:nth-of-type(1) {{ background-color: {s1['bg']} !important; padding: 20px; border-radius: 15px; }}
    [data-testid="stHorizontalBlock"] > div[data-testid="stColumn"]:nth-of-type(2) {{ background-color: {s2['bg']} !important; padding: 20px; border-radius: 15px; }}
    [data-testid="stHorizontalBlock"] > div[data-testid="stColumn"]:nth-of-type(3) {{ background-color: {s3['bg']} !important; padding: 20px; border-radius: 15px; }}
    
    [data-testid="stColumn"] h1, [data-testid="stColumn"] h2, [data-testid="stColumn"] h3 {{ transition: color 0.3s; }}
    [data-testid="stHorizontalBlock"] > div[data-testid="stColumn"]:nth-of-type(1) :is(h1,h2,h3) {{ color: {s1['text']} !important; }}
    [data-testid="stHorizontalBlock"] > div[data-testid="stColumn"]:nth-of-type(2) :is(h1,h2,h3) {{ color: {s2['text']} !important; }}
    [data-testid="stHorizontalBlock"] > div[data-testid="stColumn"]:nth-of-type(3) :is(h1,h2,h3) {{ color: {s3['text']} !important; }}

    button p {{ color: white !important; font-weight: bold !important; }}
</style>
""", unsafe_allow_html=True)

if active_alarm:
    play_local_audio(active_alarm)

# 5. Helper Functions
def add_time(name, minutes):
    if timers[name]["remaining"] == 0:
        timers[name]["start_time"] = datetime.now().strftime("%H:%M:%S")
        timers[name]["initial_minutes"] = minutes
    else:
        timers[name]["initial_minutes"] += minutes
    timers[name]["remaining"] += minutes * 60
    timers[name]["status"] = "red"

def toggle_chat(name):
    timers[name]["chat_requested"] = not timers[name]["chat_requested"]

# 6. UI
st.title("⏱️ Góc học tập cute")
cols = st.columns(3)
users = [("Phồng Tôm", "ptom.jpg"), ("Phồng Rơm", "prom.jpg"), ("Thành Đỗ", "Thanh.jpg")]

for i, (name, img) in enumerate(users):
    with cols[i]:
        # Chat Toggle Button (Top Right feel)
        chat_label = "💬 want to chat!" if timers[name]["chat_requested"] else "💬"
        chat_bg = "#00BFFF" if timers[name]["chat_requested"] else "#808080"
        
        st.markdown(f"""<style>div[data-testid="stColumn"] button[key*="chat_{name}"] {{ background-color: {chat_bg} !important; }}</style>""", unsafe_allow_html=True)
        st.button(chat_label, key=f"chat_{name}", on_click=toggle_chat, args=(name,))

        st.markdown(f"<h2>{'☕ Break!' if timers[name]['is_break'] else '&nbsp;'}</h2>", unsafe_allow_html=True)
        st.image(img, width=100)
        st.subheader(name)
        
        mins, secs = divmod(int(timers[name]["remaining"]), 60)
        st.markdown(f"<h1 style='text-align: center;'>{mins:02d}:{secs:02d}</h1>", unsafe_allow_html=True)
        
        st.button("+ 50 phút", key=f"50_{name}", on_click=add_time, args=(name, 50), use_container_width=True)
        c1, c2 = st.columns(2)
        c1.button("+ 1p", key=f"1_{name}", on_click=add_time, args=(name, 1), use_container_width=True)
        c2.button("+ 5p", key=f"5_{name}", on_click=add_time, args=(name, 5), use_container_width=True)
        
        st.button("Chế độ giải lao ☕", key=f"b_{name}", on_click=lambda n=name: timers[n].update({"is_break": not timers[n]["is_break"]}), use_container_width=True)
        st.button("Dừng / Tiếp tục", key=f"p_{name}", on_click=lambda n=name: timers[n].update({"status": "yellow" if timers[n]["status"]=="red" else "red"}), use_container_width=True)
        st.button("Reset", key=f"r_{name}", on_click=lambda n=name: timers[n].update({"remaining": 0.0, "status": "gray", "is_break": False, "start_time": None}), use_container_width=True)

# 7. Styled History
st.divider()
st.header("📜 Lịch sử học tập")

if data["history"]:
    df = pd.DataFrame(data["history"])
    
    # Function to apply blue color if the mode was "Break"
    def style_break(row):
        color = 'color: #1E90FF;' if row['Mode'] == 'Break' else 'color: black;'
        return [color] * len(row)

    st.table(df.style.apply(style_break, axis=1))
    
    if st.button("🗑️ Clear All History"):
        data["history"] = []
        st.rerun()
else:
    st.info("Chưa có lịch sử nào!")

time.sleep(1)
st.rerun()
