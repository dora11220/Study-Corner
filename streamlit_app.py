import streamlit as st
import time
import base64
import pandas as pd
import io
from datetime import datetime

st.set_page_config(layout="wide")

# Initialize robust session state for audio
if "bell_time" not in st.session_state: st.session_state.bell_time = 0
if "alarm_time" not in st.session_state: st.session_state.alarm_time = 0
if "alarm_type" not in st.session_state: st.session_state.alarm_type = None

# 1. Helper for Local Audio
def get_audio_html(file_name, play_twice=False):
    try:
        with open(file_name, "rb") as f:
            data = f.read()
            b64 = base64.b64encode(data).decode()
            
        if play_twice:
            return f"""
            <audio id="alarmAudio" autoplay>
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
            return f'<audio autoplay><source src="data:audio/mp3;base64,{b64}" type="audio/mp3"></audio>'
    except Exception:
        return ""

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

# 3. Timer Engine
current_time = time.time()
active_alarm = None 

for name, t_data in timers.items():
    if t_data["status"] == "red":
        elapsed = current_time - t_data["last_tick"]
        t_data["remaining"] -= elapsed
        
        if t_data["remaining"] <= 0:
            if t_data["start_time"]:
                end_str = datetime.now().strftime("%H:%M:%S")
                data["history"].append({
                    "User": name,
                    "Date": datetime.now().strftime("%Y-%m-%d"),
                    "Start": t_data["start_time"],
                    "End": end_str,
                    "Duration": f"{t_data['initial_minutes']} min",
                    "IsBreak": t_data["is_break"]
                })
            
            # Register the alarm in session state so it survives the reruns
            st.session_state.alarm_type = "break" if t_data["is_break"] else "study"
            st.session_state.alarm_time = time.time()
            
            t_data["remaining"] = 0
            t_data["status"] = "gray"
            t_data["start_time"] = None
            
    t_data["last_tick"] = current_time

# 4. UI Styles (Fixed: Using specific markers to stop CSS bleeding)
def get_styles(name):
    t = timers[name]
    if t["is_break"]: return {"bg": "#4682B4", "text": "white"}
    if t["status"] == "red": return {"bg": "#FFB3B3", "text": "#31333F"}
    if t["status"] == "yellow": return {"bg": "#FFFFE0", "text": "#31333F"}
    return {"bg": "#F0F2F6", "text": "#31333F"}

s1, s2, s3 = get_styles("Phồng Tôm"), get_styles("Phồng Rơm"), get_styles("Thành Đỗ")

st.markdown(f"""
<style>
    /* Use :has() to target ONLY the columns that contain our hidden marker spans */
    div[data-testid="stColumn"]:has(.marker-1) {{ background-color: {s1['bg']} !important; padding: 20px; border-radius: 15px; }}
    div[data-testid="stColumn"]:has(.marker-2) {{ background-color: {s2['bg']} !important; padding: 20px; border-radius: 15px; }}
    div[data-testid="stColumn"]:has(.marker-3) {{ background-color: {s3['bg']} !important; padding: 20px; border-radius: 15px; }}
    
    div[data-testid="stColumn"]:has(.marker-1) h1, div[data-testid="stColumn"]:has(.marker-1) h2, div[data-testid="stColumn"]:has(.marker-1) h3 {{ color: {s1['text']} !important; }}
    div[data-testid="stColumn"]:has(.marker-2) h1, div[data-testid="stColumn"]:has(.marker-2) h2, div[data-testid="stColumn"]:has(.marker-2) h3 {{ color: {s2['text']} !important; }}
    div[data-testid="stColumn"]:has(.marker-3) h1, div[data-testid="stColumn"]:has(.marker-3) h2, div[data-testid="stColumn"]:has(.marker-3) h3 {{ color: {s3['text']} !important; }}
    
    button p {{ color: white !important; font-weight: bold !important; }}
</style>
""", unsafe_allow_html=True)

# 5. Logic Functions
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

# 6. Main UI
col_title, col_bell = st.columns([10, 1])
with col_title:
    st.title("⏱️ Góc học tập cute")
with col_bell:
    st.write("<br>", unsafe_allow_html=True)
    if st.button("🔔", help="Play Bell", key="btn_bell"):
        st.session_state.bell_time = time.time()
        st.rerun()

col1, col2, col3 = st.columns(3)
users = [
    {"id": 1, "name": "Phồng Tôm", "image": "ptom.jpg", "col": col1},
    {"id": 2, "name": "Phồng Rơm", "image": "prom.jpg", "col": col2},
    {"id": 3, "name": "Thành Đỗ",  "image": "Thanh.jpg", "col": col3}
]

for user in users:
    name = user["name"]
    with user["col"]:
        # Hidden marker to perfectly target this exact column in CSS
        st.markdown(f'<span class="marker-{user["id"]}"></span>', unsafe_allow_html=True)
        
        st.markdown(f"<h2>{'☕ Break!' if timers[name]['is_break'] else '&nbsp;'}</h2>", unsafe_allow_html=True)
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

# 7. History Section
st.divider()
st.header("📜 Lịch sử học tập:")

if data["history"]:
    table_html = '<table style="width:100%; border-collapse: collapse; font-family: sans-serif;">'
    table_html += '<tr style="border-bottom: 2px solid #ccc; text-align: left;">'
    table_html += '<th>User</th><th>Date</th><th>Start</th><th>End</th><th>Duration</th></tr>'
    
    for entry in reversed(data["history"]):
        color = "#1E90FF" if entry["IsBreak"] else "inherit"
        weight = "bold" if entry["IsBreak"] else "normal"
        icon = "☕" if entry["IsBreak"] else "📚"
        
        table_html += f'<tr style="color: {color}; font-weight: {weight}; border-bottom: 1px solid #eee;">'
        table_html += f'<td>{entry["User"]} {icon}</td>'
        table_html += f'<td>{entry["Date"]}</td>'
        table_html += f'<td>{entry["Start"]}</td>'
        table_html += f'<td>{entry["End"]}</td>'
        table_html += f'<td>{entry["Duration"]}</td></tr>'
    
    table_html += '</table><br>'
    st.markdown(table_html, unsafe_allow_html=True)
    
    btn_col1, btn_col2 = st.columns([1, 1])
    
    with btn_col1:
        # Added hardcoded keys to prevent duplicate button glitches
        if st.button("🗑️ Clear All History", key="clear_hist_btn", use_container_width=True):
            data["history"] = []
            st.rerun()
            
    with btn_col2:
        df = pd.DataFrame(data["history"])
        df['Session Type'] = df['IsBreak'].apply(lambda x: 'Break' if x else 'Study')
        df = df.drop(columns=['IsBreak']) 
        
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='Study History')
        
        st.download_button(
            label="📥 Tải file Excel",
            data=output.getvalue(),
            file_name=f"Lich_su_hoc_tap_{datetime.now().strftime('%Y-%m-%d')}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            key="dl_excel_btn",
            use_container_width=True
        )
else:
    st.info("Chưa có lịch sử nào, hoàn thành 1 lần để hiện ở đây!")

# 8. Audio Engine (At the very bottom to prevent layout shifting)
# We keep audio players alive for several seconds so they aren't destroyed by st.rerun() before finishing
if time.time() - st.session_state.bell_time < 3:
    st.components.v1.html(get_audio_html("breakEnd.mp3", play_twice=False), height=0)

if time.time() - st.session_state.alarm_time < 10:  # 10 seconds alive time for double-play
    if st.session_state.alarm_type == "study":
        st.components.v1.html(get_audio_html("studyEnd.mp3", play_twice=True), height=0)
    elif st.session_state.alarm_type == "break":
        st.components.v1.html(get_audio_html("breakEnd.mp3", play_twice=True), height=0)

time.sleep(1)
st.rerun()
