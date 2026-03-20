import streamlit as st
import streamlit.components.v1 as components
import time
import base64
import pandas as pd
import io
from datetime import datetime, timedelta, timezone

st.set_page_config(layout="wide")

# --- 0. TIME LOGIC ---
def get_now_gmt7():
    return datetime.now(timezone.utc) + timedelta(hours=7)

# --- 1. SESSION STATE ---
if "last_heard_bell_time" not in st.session_state: st.session_state.last_heard_bell_time = 0.0
if "alarm_trigger" not in st.session_state: st.session_state.alarm_trigger = None
if "sound_key" not in st.session_state: st.session_state.sound_key = 0

# --- 2. AUDIO ENGINE (ISOLATED COMPONENT) ---
def play_sound(file_name, play_twice=False):
    """Uses Streamlit Components to inject JS that survives reruns and overlaps."""
    try:
        with open(file_name, "rb") as f:
            b64 = base64.b64encode(f.read()).decode()
        
        loop_logic = """
            var playCount = 1;
            snd.onended = function() {
                if(playCount < 2) {
                    playCount++;
                    this.play();
                }
            };
        """ if play_twice else ""

        js_html = f"""
            <html>
                <body>
                    <script>
                        var snd = new Audio("data:audio/mp3;base64,{b64}");
                        snd.play().catch(e => console.log("Audio blocked by browser policy"));
                        {loop_logic}
                    </script>
                </body>
            </html>
        """
        # Increment key to force component to re-render (and thus re-play sound)
        st.session_state.sound_key += 1
        components.html(js_html, height=0, width=0)
    except:
        pass

def get_base64_bin(file_path):
    try:
        with open(file_path, "rb") as f:
            return base64.b64encode(f.read()).decode()
    except: return ""

bg_base64 = get_base64_bin("background.jpg")

# --- 3. SHARED GLOBAL DATA ---
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

# Timer Logic
cur = time.time()
for name, t in data["timers"].items():
    if t["status"] == "red":
        elapsed = cur - t["last_tick"]
        t["remaining"] -= elapsed
        if t["remaining"] <= 0:
            if t["start_time"]:
                data["history"].append({"User": name, "Date": get_now_gmt7().strftime("%Y-%m-%d"), "Start": t["start_time"], "End": get_now_gmt7().strftime("%H:%M:%S"), "Duration": f"{t['initial_minutes']} min", "IsBreak": t["is_break"]})
            st.session_state.alarm_trigger = "break" if t["is_break"] else "study"
            t.update({"remaining": 0, "status": "gray", "start_time": None})
    t["last_tick"] = cur

# --- 4. STYLES (NO CHANGES) ---
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
    [data-testid="stAppViewContainer"] {{
        background-image: url("data:image/jpg;base64,{bg_base64}");
        background-size: 130% 130%; 
        background-attachment: fixed;
        animation: diagonalMove 40s ease-in-out infinite alternate;
    }}
    @keyframes diagonalMove {{ 0% {{ background-position: 0% 0%; }} 100% {{ background-position: 100% 100%; }} }}
    {" ".join([f'''
    div[data-testid="stColumn"]:has(.marker-{i+1}) {{ 
        background-color: {s[n]['bg']} !important; 
        box-shadow: {s[n]['glow']};
        padding: 20px; border-radius: 20px; min-height: 600px; 
        transition: all 0.6s cubic-bezier(0.175, 0.885, 0.32, 1.275);
        backdrop-filter: blur(8px);
        border: 1px solid rgba(255,255,255,0.3);
    }}
    div[data-testid="stColumn"]:has(.marker-{i+1}) h1, 
    div[data-testid="stColumn"]:has(.marker-{i+1}) h2, 
    div[data-testid="stColumn"]:has(.marker-{i+1}) h3 {{ color: {s[n]['text']} !important; }}
    ''' for i, n in enumerate(data["timers"])])}
    .stApp h1 {{ color: white !important; text-shadow: 3px 3px 6px rgba(0,0,0,0.7); font-size: 3rem !important; }}
    button p {{ color: white !important; font-weight: bold !important; }}
</style>
""", unsafe_allow_html=True)

# --- 5. MAIN UI ---
st.title("⏱️ Góc học tập cute")

def add_time(name, m):
    t = data["timers"][name]
    if t["remaining"] <= 0: t["start_time"], t["initial_minutes"] = get_now_gmt7().strftime("%H:%M:%S"), m
    else: t["initial_minutes"] += m
    t["remaining"] += m * 60
    t["status"] = "red"

def ring_bell(name):
    data["last_bell_ringer"] = name
    data["last_bell_time"] = time.time()

col1, col2, col3, col4 = st.columns(4)
users = [
    {"id": 1, "name": "Phồng Tôm", "image": "ptom.jpg", "col": col1},
    {"id": 2, "name": "Phồng Rơm", "image": "prom.jpg", "col": col2},
    {"id": 3, "name": "Thanh Độ",  "image": "Thanh.jpg", "col": col3},
    {"id": 4, "name": "黄明",      "image": "hoang.jpg", "col": col4}
]

for u in users:
    n = u["name"]
    with u["col"]:
        st.markdown(f'<span class="marker-{u["id"]}"></span>', unsafe_allow_html=True)
        st.button("🔔 Rung chuông", key=f"bell_{n}", on_click=ring_bell, args=(n,), use_container_width=True)
        st.markdown(f"<h2>{'☕ Break!' if data['timers'][n]['is_break'] else '&nbsp;'}</h2>", unsafe_allow_html=True)
        try: st.image(u["image"], width=100)
        except: st.write("👤")
        st.subheader(n)
        mm, ss = divmod(int(data["timers"][n]["remaining"]), 60)
        st.markdown(f"<h1 style='text-align: center;'>{mm:02d}:{ss:02d}</h1>", unsafe_allow_html=True)
        st.button("+ 50 phút", key=f"50_{n}", on_click=add_time, args=(n, 50), use_container_width=True)
        ca, cb = st.columns(2)
        ca.button("+ 1p", key=f"1_{n}", on_click=add_time, args=(n, 1), use_container_width=True)
        cb.button("+ 5p", key=f"5_{n}", on_click=add_time, args=(n, 5), use_container_width=True)
        st.button("Giải lao ☕", key=f"b_{n}", on_click=lambda x=n: data["timers"][x].update({"is_break": not data["timers"][x]["is_break"]}), use_container_width=True)
        st.button("Stop/Go", key=f"p_{n}", on_click=lambda x=n: data["timers"][x].update({"status": "yellow" if data["timers"][x]["status"]=="red" else "red"}), use_container_width=True)
        st.button("Reset", key=f"r_{n}", on_click=lambda x=n: data["timers"][x].update({"remaining": 0.0, "status": "gray", "is_break": False, "start_time": None}), use_container_width=True)

# --- 6. HISTORY SECTION (KEEPING BLACK-GRAY) ---
st.divider()
st.markdown("<h2 style='color: white; text-shadow: 2px 2px 4px black;'>📜 Lịch sử học tập:</h2>", unsafe_allow_html=True)
if data["history"]:
    table = '<table style="width:100%; border-collapse: collapse; background-color: rgba(30, 30, 30, 0.9); border-radius: 12px; overflow: hidden; color: white;">'
    table += '<tr style="border-bottom: 2px solid #555; background-color: rgba(0, 0, 0, 0.5); text-align: left;">'
    table += '<th style="padding: 12px;">User</th><th style="padding: 12px;">Date</th><th style="padding: 12px;">Start</th><th style="padding: 12px;">End</th><th style="padding: 12px;">Duration</th></tr>'
    for e in reversed(data["history"]):
        c = "#00BFFF" if e["IsBreak"] else "white"
        table += f'<tr style="color: {c}; border-bottom: 1px solid #444;"><td style="padding: 12px;">{e["User"]} {"☕" if e["IsBreak"] else "📚"}</td><td style="padding: 12px;">{e["Date"]}</td><td style="padding: 12px;">{e["Start"]}</td><td style="padding: 12px;">{e["End"]}</td><td style="padding: 12px;">{e["Duration"]}</td></tr>'
    st.markdown(table + '</table><br>', unsafe_allow_html=True)
    h1, h2 = st.columns(2)
    with h1: 
        if st.button("🗑️ Clear All History", use_container_width=True): data["history"] = []; st.rerun()
    with h2:
        df = pd.DataFrame(data["history"])
        out = io.BytesIO()
        with pd.ExcelWriter(out) as wr: df.to_excel(wr, index=False)
        st.download_button("📥 Tải file Excel", data=out.getvalue(), file_name="History.xlsx", use_container_width=True)

# --- 7. AUDIO EXECUTION ---
if data["last_bell_time"] > st.session_state.last_heard_bell_time:
    play_sound("bellButton.mp3")
    st.session_state.last_heard_bell_time = data["last_bell_time"]

if st.session_state.alarm_trigger:
    f = "breakEnd.mp3" if st.session_state.alarm_trigger == "break" else "studyEnd.mp3"
    play_sound(f, play_twice=True)
    st.session_state.alarm_trigger = None 

# Regular refresh
time.sleep(1)
st.rerun()
