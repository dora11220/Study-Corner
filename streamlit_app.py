import streamlit as st
import time
from datetime import datetime

st.set_page_config(layout="wide")

# 1. Shared Global Memory (Now includes History)
@st.cache_resource
def get_global_data():
    return {
        "timers": {
            "Phồng Tôm": {"remaining": 0.0, "status": "gray", "last_tick": time.time(), "is_break": False, "start_time": None, "initial_minutes": 0},
            "Phồng Rơm": {"remaining": 0.0, "status": "gray", "last_tick": time.time(), "is_break": False, "start_time": None, "initial_minutes": 0},
            "Thành Đỗ":  {"remaining": 0.0, "status": "gray", "last_tick": time.time(), "is_break": False, "start_time": None, "initial_minutes": 0}
        },
        "history": [] # This stores the study sessions
    }

data = get_global_data()
timers = data["timers"]

# 2. Sound Logic
def play_ding():
    sound_url = "https://www.soundjay.com/buttons/sounds/beep-07a.mp3"
    st.components.v1.html(f'<audio autoplay><source src="{sound_url}"></audio>', height=0)

# 3. Timer Engine & History Recording
current_time = time.time()
trigger_alarm = False

for name, t_data in timers.items():
    if t_data["status"] == "red":
        elapsed = current_time - t_data["last_tick"]
        t_data["remaining"] -= elapsed
        
        # When timer hits zero:
        if t_data["remaining"] <= 0:
            # Record to history before resetting
            if t_data["start_time"]:
                end_str = datetime.now().strftime("%H:%M:%S")
                data["history"].append({
                    "User": name,
                    "Date": datetime.now().strftime("%Y-%m-%d"),
                    "Start": t_data["start_time"],
                    "End": end_str,
                    "Duration": f"{t_data['initial_minutes']} min"
                })
            
            t_data["remaining"] = 0
            t_data["status"] = "gray"
            t_data["start_time"] = None
            trigger_alarm = True
            
    t_data["last_tick"] = current_time

# 4. UI Styles (CSS)
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
    
    [data-testid="stHorizontalBlock"] > div[data-testid="stColumn"]:nth-of-type(1) h1, h2, h3 {{ color: {s1['text']} !important; }}
    [data-testid="stHorizontalBlock"] > div[data-testid="stColumn"]:nth-of-type(2) h1, h2, h3 {{ color: {s2['text']} !important; }}
    [data-testid="stHorizontalBlock"] > div[data-testid="stColumn"]:nth-of-type(3) h1, h2, h3 {{ color: {s3['text']} !important; }}

    button p {{ color: white !important; font-weight: bold !important; }}
    [data-testid="stColumn"] [data-testid="stColumn"] {{ background-color: transparent !important; padding: 0px !important; }}
</style>
""", unsafe_allow_html=True)

if trigger_alarm: play_ding()

# 5. Helper Functions
def add_time(name, minutes):
    if timers[name]["remaining"] == 0:
        timers[name]["start_time"] = datetime.now().strftime("%H:%M:%S")
        timers[name]["initial_minutes"] = minutes
    else:
        timers[name]["initial_minutes"] += minutes
        
    timers[name]["remaining"] += minutes * 60
    timers[name]["status"] = "red"

def reset_timer(name):
    timers[name].update({"remaining": 0.0, "status": "gray", "is_break": False, "start_time": None})

def clear_history():
    data["history"] = []

# 6. Main UI
st.title("⏱️ Study Dashboard & History")
col1, col2, col3 = st.columns(3)
users = [
    {"name": "Phồng Tôm", "image": "ptom.jpg", "col": col1},
    {"name": "Phồng Rơm", "image": "prom.jpg", "col": col2},
    {"name": "Thành Đỗ",  "image": "Thanh.jpg", "col": col3}
]

for user in users:
    name = user["name"]
    with user["col"]:
        st.markdown(f"<h2>{'☕ Break!' if timers[name]['is_break'] else '&nbsp;'}</h2>", unsafe_allow_html=True)
        st.image(user["image"], width=100)
        st.subheader(name)
        mins, secs = divmod(int(timers[name]["remaining"]), 60)
        st.markdown(f"<h1 style='text-align: center;'>{mins:02d}:{secs:02d}</h1>", unsafe_allow_html=True)
        
        st.button("Add 50 Min", key=f"50_{name}", on_click=add_time, args=(name, 50), use_container_width=True)
        c_a, c_b = st.columns(2)
        c_a.button("+10m", key=f"10_{name}", on_click=add_time, args=(name, 10), use_container_width=True)
        c_b.button("+5m", key=f"5_{name}", on_click=add_time, args=(name, 5), use_container_width=True)
        st.button("Break Mode ☕", key=f"b_{name}", on_click=lambda n=name: timers[n].update({"is_break": not timers[n]["is_break"]}), use_container_width=True)
        st.button("Pause/Resume", key=f"p_{name}", on_click=lambda n=name: timers[n].update({"status": "yellow" if timers[n]["status"]=="red" else "red"}), use_container_width=True)
        st.button("Reset", key=f"r_{name}", on_click=reset_timer, args=(name,), use_container_width=True)

# 7. History Section
st.divider()
st.header("📜 Session History")

if data["history"]:
    # Display history in a nice table
    st.table(data["history"])
    if st.button("🗑️ Clear All History"):
        clear_history()
        st.rerun()
else:
    st.info("No sessions recorded yet. Finish a timer to see it here!")

time.sleep(1)
st.rerun()
