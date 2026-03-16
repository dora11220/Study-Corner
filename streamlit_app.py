import streamlit as st
import time
import base64
from datetime import datetime

st.set_page_config(layout="wide")

# 1. Helper for Local Audio
def get_audio_html(file_name):
    """Encodes local mp3 to base64 so it can be played in the HTML component."""
    with open(file_name, "rb") as f:
        data = f.read()
        b64 = base64.b64encode(data).decode()
    return f'<audio autoplay><source src="data:audio/mp3;base64,{b64}" type="audio/mp3"></audio>'

# 2. Shared Global Memory
@st.cache_resource
def get_global_data():
    return {
        "timers": {
            "Phồng Tôm": {"remaining": 0.0, "status": "gray", "last_tick": time.time(), "is_break": False, "start_time": None, "initial_minutes": 0},
            "Phồng Rơm": {"remaining": 0.0, "status": "gray", "last_tick": time.time(), "is_break": False, "start_time": None, "initial_minutes": 0},
            "Thành Đỗ":  {"remaining": 0.0, "status": "gray", "last_tick": time.time(), "is_break": False, "start_time": None, "initial_minutes": 0}
        },
        "history": []
    }

data = get_global_data()
timers = data["timers"]

# 3. Timer Engine & History Recording
current_time = time.time()
active_alarm = None # Will store 'study' or 'break'

for name, t_data in timers.items():
    if t_data["status"] == "red":
        elapsed = current_time - t_data["last_tick"]
        t_data["remaining"] -= elapsed
        
        # When timer hits zero:
        if t_data["remaining"] <= 0:
            if t_data["start_time"]:
                end_str = datetime.now().strftime("%H:%M:%S")
                # Save session type
                data["history"].append({
                    "User": name,
                    "Date": datetime.now().strftime("%Y-%m-%d"),
                    "Start": t_data["start_time"],
                    "End": end_str,
                    "Duration": f"{t_data['initial_minutes']} min",
                    "IsBreak": t_data["is_break"] # New flag for history styling
                })
            
            # Determine which sound to play
            active_alarm = "break" if t_data["is_break"] else "study"
            
            t_data["remaining"] = 0
            t_data["status"] = "gray"
            t_data["start_time"] = None
            
    t_data["last_tick"] = current_time

# 4. Sound Triggering
if active_alarm == "study":
    st.components.v1.html(get_audio_html("studyEnd.mp3"), height=0)
elif active_alarm == "break":
    st.components.v1.html(get_audio_html("breakEnd.mp3"), height=0)

# 5. UI Styles (CSS)
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
</style>
""", unsafe_allow_html=True)

# 6. Helper Functions
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

# 7. Main UI
st.title("⏱️ Góc học tập cute")
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
        # Check if user has an image, otherwise show placeholder
        try:
            st.image(user["image"], width=100)
        except:
            st.write("👤")
            
        st.subheader(name)
        mins, secs = divmod(int(timers[name]["remaining"]), 60)
        st.markdown(f"<h1 style='text-align: center;'>{mins:02d}:{secs:02d}</h1>", unsafe_allow_html=True)
        
        st.button("+ 50 phút", key=f"50_{name}", on_click=add_time, args=(name, 50), use_container_width=True)
        c_a, c_b = st.columns(2)
        c_a.button("+ 1p", key=f"1_{name}", on_click=add_time, args=(name, 1), use_container_width=True)
        c_b.button("+ 5p", key=f"5_{name}", on_click=add_time, args=(name, 5), use_container_width=True)

        st.button("Chế độ giải lao ☕", key=f"b_{name}", on_click=lambda n=name: timers[n].update({"is_break": not timers[n]["is_break"]}), use_container_width=True)
        st.button("Dừng / Tiếp tục", key=f"p_{name}", on_click=lambda n=name: timers[n].update({"status": "yellow" if timers[n]["status"]=="red" else "red"}), use_container_width=True)
        st.button("Reset", key=f"r_{name}", on_click=reset_timer, args=(name,), use_container_width=True)

# 8. History Section (Custom Styled Table)
st.divider()
st.header("📜 Lịch sử học tập:")

if data["history"]:
    # Building a custom HTML table for coloring
    html_table = """
    <table style="width:100%; border-collapse: collapse;">
        <tr style="border-bottom: 2px solid #ccc; text-align: left;">
            <th>User</th><th>Date</th><th>Start</th><th>End</th><th>Duration</th>
        </tr>
    """
    for entry in reversed(data["history"]):
        color = "#1E90FF" if entry["IsBreak"] else "inherit"
        weight = "bold" if entry["IsBreak"] else "normal"
        html_table += f"""
        <tr style="color: {color}; font-weight: {weight}; border-bottom: 1px solid #eee;">
            <td>{entry['User']} {'☕' if entry['IsBreak'] else '📚'}</td>
            <td>{entry['Date']}</td>
            <td>{entry['Start']}</td>
            <td>{entry['End']}</td>
            <td>{entry['Duration']}</td>
        </tr>
        """
    html_table += "</table>"
    st.markdown(html_table, unsafe_allow_html=True)
    
    if st.button("🗑️ Clear All History"):
        data["history"] = []
        st.rerun()
else:
    st.info("Chưa có lịch sử nào, hoàn thành 1 lần để hiện ở đây!")

time.sleep(1)
st.rerun()
