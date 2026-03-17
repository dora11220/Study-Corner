import streamlit as st
import time
import base64
import pandas as pd
import io
from datetime import datetime, timedelta, timezone

st.set_page_config(layout="wide")

# --- 0. BULLETPROOF GMT+7 TIME FUNCTION ---
def get_gmt7_time(format_str):
    """Forces the time to be UTC + 7 hours exactly."""
    # Get standard UTC time, then mathematically add 7 hours
    gmt7_time = datetime.now(timezone.utc) + timedelta(hours=7)
    return gmt7_time.strftime(format_str)

# --- 1. SESSION STATE INITIALIZATION ---
if "local_played_bell_time" not in st.session_state: st.session_state.local_played_bell_time = 0.0
if "alarm_trigger" not in st.session_state: st.session_state.alarm_trigger = None

# --- 2. AUDIO ENGINE ---
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
            return f"""
            <audio autoplay style="display:none;">
                <source src="data:audio/mp3;base64,{b64}" type="audio/mp3">
            </audio>
            """
    except Exception as e:
        return f""

# --- 3. SHARED GLOBAL MEMORY ---
@st.cache_resource
def get_global_data():
    return {
        "timers": {
            "Phồng Tôm": {"remaining": 0.0, "status": "gray", "last_tick": time.time(), "is_break": False, "start_time": None, "initial_minutes": 0},
            "Phồng Rơm": {"remaining": 0.0, "status": "gray", "last_tick": time.time(), "is_break": False, "start_time": None, "initial_minutes": 0},
            "Thành Đỗ":  {"remaining": 0.0, "status": "gray", "last_tick": time.time(), "is_break": False, "start_time": None, "initial_minutes": 0}
        },
        "history": [],
        "last_global_bell_time": 0.0 
    }

data = get_global_data()
timers = data["timers"]

# Engine tick
current_time = time.time()
for name, t_data in timers.items():
    if t_data["status"] == "red":
        elapsed = current_time - t_data["last_tick"]
        t_data["remaining"] -= elapsed
        
        if t_data["remaining"] <= 0:
            if t_data["start_time"]:
                data["history"].append({
                    "User": name,
                    "Date": get_gmt7_time("%Y-%m-%d"), 
                    "Start": t_data["start_time"],
                    "End": get_gmt7_time("%H:%M:%S"), 
                    "Duration": f"{t_data['initial_minutes']} min",
                    "IsBreak": t_data["is_break"]
                })
            
            st.session_state.alarm_trigger = "break" if t_data["is_break"] else "study"
            t_data["remaining"] = 0
            t_data["status"] = "gray"
            t_data["start_time"] = None
    t_data["last_tick"] = current_time

# --- 4. CSS STYLES ---
def get_styles(name):
    t = timers[name]
    if t["is_break"]: return {"bg": "#4682B4", "text": "white"}
    if t["status"] == "red": return {"bg": "#FFB3B3", "text": "#31333F"}
    if t["status"] == "yellow": return {"bg": "#FFFFE0", "text": "#31333F"}
    return {"bg": "#F0F2F6", "text": "#31333F"}

s1, s2, s3 = get_styles("Phồng Tôm"), get_styles("Phồng Rơm"), get_styles("Thành Đỗ")

st.markdown(f"""
<style>
    div[data-testid="stColumn"]:has(.marker-1) {{ background-color: {s1['bg']} !important; padding: 20px; border-radius: 15px; min-height: 550px; }}
    div[data-testid="stColumn"]:has(.marker-2) {{ background-color: {s2['bg']} !important; padding: 20px; border-radius: 15px; min-height: 550px; }}
    div[data-testid="stColumn"]:has(.marker-3) {{ background-color: {s3['bg']} !important; padding: 20px; border-radius: 15px; min-height: 550px; }}
    
    div[data-testid="stColumn"]:has(.marker-1) h1, div[data-testid="stColumn"]:has(.marker-1) h2, div[data-testid="stColumn"]:has(.marker-1) h3 {{ color: {s1['text']} !important; }}
    div[data-testid="stColumn"]:has(.marker-2) h1, div[data-testid="stColumn"]:has(.marker-2) h2, div[data-testid="stColumn"]:has(.marker-2) h3 {{ color: {s2['text']} !important; }}
    div[data-testid="stColumn"]:has(.marker-3) h1, div[data-testid="stColumn"]:has(.marker-3) h2, div[data-testid="stColumn"]:has(.marker-3) h3 {{ color: {s3['text']} !important; }}
    
    button p {{ color: white !important; font-weight: bold !important; }}
</style>
""", unsafe_allow_html=True)

# --- 5. UI ACTIONS ---
def add_time(name, minutes):
    if timers[name]["remaining"] == 0:
        timers[name]["start_time"] = get_gmt7_time("%H:%M:%S") 
        timers[name]["initial_minutes"] = minutes
    else:
        timers[name]["initial_minutes"] += minutes
    timers[name]["remaining"] += minutes * 60
    timers[name]["status"] = "red"

# --- 6. MAIN DISPLAY ---
col_title, col_bell = st.columns([10, 1])
with col_title:
    st.title("⏱️ Góc học tập cute")
with col_bell:
    st.write("<br>", unsafe_allow_html=True)
    if st.button("🔔", help="Play Bell (Broadcasts to everyone)", key="global_bell_btn"):
        data["last_global_bell_time"] = time.time()
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
        st.button("Reset", key=f"r_{name}", on_click=lambda n=name: timers[n].update({"remaining": 0.0, "status": "gray", "is_break": False, "start_time": None}), use_container_width=True)

# --- 7. HISTORY SECTION ---
st.divider()
st.header("📜 Lịch sử học tập:")

if data["history"]:
    table_html = '<table style="width:100%; border-collapse: collapse; font-family: sans-serif;">'
    table_html += '<tr style="border-bottom: 2px solid #ccc; text-align: left;"><th>User</th><th>Date</th><th>Start</th><th>End</th><th>Duration</th></tr>'
    for entry in reversed(data["history"]):
        color = "#1E90FF" if entry["IsBreak"] else "inherit"
        icon = "☕" if entry["IsBreak"] else "📚"
        table_html += f'<tr style="color: {color}; border-bottom: 1px solid #eee;"><td>{entry["User"]} {icon}</td><td>{entry["Date"]}</td><td>{entry["Start"]}</td><td>{entry["End"]}</td><td>{entry["Duration"]}</td></tr>'
    table_html += '</table><br>'
    st.markdown(table_html, unsafe_allow_html=True)
    
    h_col1, h_col2 = st.columns(2)
    with h_col1:
        if st.button("🗑️ Clear All History", key="clear_final_btn", use_container_width=True):
            data["history"] = []
            st.rerun()
    with h_col2:
        df = pd.DataFrame(data["history"])
        df['Type'] = df['IsBreak'].apply(lambda x: 'Break' if x else 'Study')
        df_out = df[['User', 'Date', 'Start', 'End', 'Duration', 'Type']]
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df_out.to_excel(writer, index=False)
        st.download_button("📥 Tải file Excel", data=output.getvalue(), file_name=f"History_{get_gmt7_time('%Y-%m-%d')}.xlsx", mime="application/vnd.ms-excel", key="dl_final_btn", use_container_width=True)
else:
    st.info("Chưa có lịch sử học tập.")

# --- 8. AUDIO TRIGGER & RERUN LOOP ---
bell_placeholder = st.empty()
alarm_placeholder = st.empty()

if data["last_global_bell_time"] > st.session_state.local_played_bell_time:
    bell_placeholder.html(get_audio_html("endBreak.mp3", play_twice=False))
    st.session_state.local_played_bell_time = data["last_global_bell_time"]

if st.session_state.alarm_trigger:
    file = "breakEnd.mp3" if st.session_state.alarm_trigger == "break" else "studyEnd.mp3"
    alarm_placeholder.html(get_audio_html(file, play_twice=True))
    st.session_state.alarm_trigger = None 

time.sleep(1)
st.rerun()
