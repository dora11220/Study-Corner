import streamlit as st
import time

st.set_page_config(layout="wide")

# 1. Shared Global Memory
@st.cache_resource
def get_timers():
    return {
        "Phồng Tôm": {"remaining": 0.0, "status": "gray", "last_tick": time.time(), "is_break": False},
        "Phồng Rơm": {"remaining": 0.0, "status": "gray", "last_tick": time.time(), "is_break": False},
        "Thành Đỗ":  {"remaining": 0.0, "status": "gray", "last_tick": time.time(), "is_break": False}
    }

timers = get_timers()

# 2. Timer Logic
current_time = time.time()
for name, data in timers.items():
    if data["status"] == "red" and not data["is_break"]:
        elapsed = current_time - data["last_tick"]
        data["remaining"] -= elapsed
        if data["remaining"] <= 0:
            data["remaining"] = 0
            data["status"] = "gray"
    data["last_tick"] = current_time

# 3. Dynamic Color Logic
def get_color(name):
    data = timers[name]
    if data["is_break"]: return "#ADD8E6" # Blue
    if data["status"] == "red": return "#FFB3B3" # Red
    if data["status"] == "yellow": return "#FFFFE0" # Yellow
    return "#F0F2F6" # Gray

# 4. FIXED CSS (Targets only main columns & fixes button text)
css = f"""
<style>
    /* Target only the 3 main top-level columns */
    [data-testid="stHorizontalBlock"] > div[data-testid="stColumn"]:nth-of-type(1) {{ background-color: {get_color("Phồng Tôm")} !important; padding: 20px; border-radius: 15px; }}
    [data-testid="stHorizontalBlock"] > div[data-testid="stColumn"]:nth-of-type(2) {{ background-color: {get_color("Phồng Rơm")} !important; padding: 20px; border-radius: 15px; }}
    [data-testid="stHorizontalBlock"] > div[data-testid="stColumn"]:nth-of-type(3) {{ background-color: {get_color("Thành Đỗ")} !important; padding: 20px; border-radius: 15px; }}

    /* Fix: Ensure nested columns (for buttons) stay transparent */
    [data-testid="stColumn"] [data-testid="stColumn"] {{
        background-color: transparent !important;
        padding: 0px !important;
    }}

    /* FIX: Make all button text white */
    button p {{
        color: white !important;
        font-weight: bold !important;
    }}
    
    /* Make the timer and headers dark for readability */
    h1, h2, h3, p {{
        color: #31333F !important;
    }}
</style>
"""
st.markdown(css, unsafe_allow_html=True)

# 5. Helper functions
def add_time(name, minutes):
    timers[name]["remaining"] += minutes * 60
    timers[name]["status"] = "red"
    timers[name]["is_break"] = False

def toggle_pause(name):
    if timers[name]["status"] == "red": timers[name]["status"] = "yellow"
    elif timers[name]["status"] == "yellow": timers[name]["status"] = "red"

def toggle_break(name):
    timers[name]["is_break"] = not timers[name]["is_break"]

def reset_timer(name):
    timers[name]["remaining"] = 0
    timers[name]["status"] = "gray"
    timers[name]["is_break"] = False

# 6. UI Construction
st.title("⏱️ Shared Study Dashboard")
col1, col2, col3 = st.columns(3)
users = [
    {"name": "Phồng Tôm", "image": "ptom.jpg", "col": col1},
    {"name": "Phồng Rơm", "image": "prom.jpg", "col": col2},
    {"name": "Thành Đỗ",  "image": "Thanh.jpg", "col": col3}
]

for user in users:
    name = user["name"]
    with user["col"]:
        if timers[name]["is_break"]:
            st.markdown("<h2 style='text-align: center;'>☕ Break Time!</h2>", unsafe_allow_html=True)
        else:
            st.markdown("<div style='height: 46px;'></div>", unsafe_allow_html=True)

        st.image(user["image"], width=120)
        st.subheader(f"{name}'s Timer")
        
        mins, secs = divmod(int(timers[name]["remaining"]), 60)
        st.markdown(f"<h1 style='text-align: center;'>{mins:02d}:{secs:02d}</h1>", unsafe_allow_html=True)
        
        st.button("Add 50 Min", key=f"50_{name}", on_click=add_time, args=(name, 50), use_container_width=True)
        
        b_col1, b_col2 = st.columns(2) # Nested columns
        b_col1.button("+ 10m", key=f"10_{name}", on_click=add_time, args=(name, 10), use_container_width=True)
        b_col2.button("+ 5m",  key=f"5_{name}",  on_click=add_time, args=(name, 5), use_container_width=True)
        
        st.button("Toggle Break ☕", key=f"brk_{name}", on_click=toggle_break, args=(name,), use_container_width=True)
        st.button("Pause / Resume", key=f"ps_{name}", on_click=toggle_pause, args=(name,), use_container_width=True)
        st.button("Reset", key=f"rst_{name}", on_click=reset_timer, args=(name,), use_container_width=True)

time.sleep(1)
st.rerun()
