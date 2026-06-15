import datetime
import json
import math

import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(page_title="GreenGo", page_icon="🚦", layout="centered")

with open("signal.json", encoding="utf-8") as f:
    config = json.load(f)

LAT = config["lat"]
LON = config["lon"]
SIGNAL = config["phases"]


def parse_base_time(hhmmss: str) -> int:
    hour = int(hhmmss[0:2])
    minute = int(hhmmss[2:4])
    second = int(hhmmss[4:6])
    today = datetime.date.today()
    dt = datetime.datetime(today.year, today.month, today.day, hour, minute, second)
    return int(dt.timestamp())


def get_signal(cfg: dict, now_ts: float) -> tuple[str, int]:
    green = cfg["green_sec"]
    red = cfg["red_sec"]
    cycle = green + red
    base_ts = parse_base_time(cfg["base_time"])
    phase = (now_ts - base_ts) % cycle
    if phase < 0:
        phase += cycle
    if phase < green:
        return "green", max(1, math.ceil(green - phase))
    return "red", max(1, math.ceil(cycle - phase))


def direction_label(direction_key: str) -> str:
    return "横浜・新高島" if direction_key == "NS" else "高島町"


def select_direction(direction_key: str) -> None:
    st.session_state.direction_key = direction_key


def build_map_html(direction_key: str) -> str:
    phase = SIGNAL[direction_key]
    state, remaining = get_signal(phase, datetime.datetime.now().timestamp())
    payload = {
        "lat": LAT,
        "lon": LON,
        "phase": {
            "base_ts": parse_base_time(phase["base_time"]),
            "green_sec": phase["green_sec"],
            "red_sec": phase["red_sec"],
        },
        "initial_state": state,
        "initial_remaining": remaining,
    }
    payload_json = json.dumps(payload, ensure_ascii=False).replace("</", "<\\/")

    return f"""
<link
  rel="stylesheet"
  href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"
  integrity="sha256-p4NxAoJBhIIN+hmNHrzRCf9tD/miZyoHS5obTRR9BMY="
  crossorigin=""
/>

<style>
  html, body {{
    margin: 0;
    padding: 0;
    background: transparent;
  }}

  .map-shell {{
    position: relative;
    width: 100%;
    height: 460px;
    overflow: hidden;
    border-radius: 24px;
    border: 1px solid rgba(15, 23, 42, 0.08);
    box-shadow: 0 18px 45px rgba(15, 23, 42, 0.12);
    background:
      radial-gradient(circle at top left, rgba(255, 255, 255, 0.72), transparent 38%),
      linear-gradient(180deg, rgba(248, 250, 252, 0.98), rgba(241, 245, 249, 0.96));
  }}

  #map {{
    width: 100%;
    height: 100%;
  }}

  .signal-badge {{
    width: 56px;
    height: 56px;
    border-radius: 999px;
    display: flex;
    align-items: center;
    justify-content: center;
    font: 700 20px/1 -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
    box-shadow: 0 10px 28px rgba(15, 23, 42, 0.28);
    border: 3px solid rgba(255, 255, 255, 0.92);
    transition: background-color 160ms ease, color 160ms ease;
  }}

  .signal-badge.green {{
    background: #22c55e;
    color: #0f172a;
  }}

  .signal-badge.red {{
    background: #ef4444;
    color: #ffffff;
  }}

  .leaflet-control-attribution {{
    font-size: 10px;
  }}

  @media (max-width: 640px) {{
    .map-shell {{
      height: 62vh;
      min-height: 360px;
      max-height: 520px;
      border-radius: 20px;
    }}
  }}
</style>

<div class="map-shell">
  <div id="map"></div>
</div>

<script
  src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"
  integrity="sha256-20nQCchB9co0qIjJZRGuk2/Z9VM+kNiyxNV1lvTlZBo="
  crossorigin=""
></script>

<script>
  const payload = {payload_json};

  function computeSignal(nowSec) {{
    const green = payload.phase.green_sec;
    const red = payload.phase.red_sec;
    const cycle = green + red;
    let phase = (nowSec - payload.phase.base_ts) % cycle;

    if (phase < 0) {{
      phase += cycle;
    }}

    if (phase < green) {{
      return {{
        state: "green",
        remaining: Math.max(1, Math.ceil(green - phase)),
      }};
    }}

    return {{
      state: "red",
      remaining: Math.max(1, Math.ceil(cycle - phase)),
    }};
  }}

  function createBadgeHtml(state, remaining) {{
    return (
      '<div id="signal-badge" class="signal-badge ' +
      state +
      '"><span id="signal-count">' +
      remaining +
      "</span></div>"
    );
  }}

  function boot() {{
    if (!window.L) {{
      window.setTimeout(boot, 50);
      return;
    }}

    const map = L.map("map", {{
      zoomControl: false,
      attributionControl: true,
      dragging: false,
      scrollWheelZoom: false,
      doubleClickZoom: false,
      boxZoom: false,
      keyboard: false,
      touchZoom: false,
    }}).setView([payload.lat, payload.lon], 17);

    L.tileLayer("https://{{s}}.tile.openstreetmap.org/{{z}}/{{x}}/{{y}}.png", {{
      maxZoom: 19,
      attribution: "&copy; OpenStreetMap contributors",
    }}).addTo(map);

    const icon = L.divIcon({{
      className: "signal-marker-wrapper",
      html: createBadgeHtml(payload.initial_state, payload.initial_remaining),
      iconSize: [56, 56],
      iconAnchor: [28, 28],
    }});

    const marker = L.marker([payload.lat, payload.lon], {{
      icon,
      interactive: false,
    }}).addTo(map);

    function startRenderLoop() {{
      const markerEl = marker.getElement();
      if (!markerEl) {{
        window.setTimeout(startRenderLoop, 50);
        return;
      }}

      const badgeEl = markerEl.querySelector("#signal-badge");
      const countEl = markerEl.querySelector("#signal-count");
      let lastKey = "";

      function render() {{
        const signal = computeSignal(Date.now() / 1000);
        const nextKey = signal.state + "-" + signal.remaining;
        if (nextKey === lastKey) {{
          return;
        }}

        lastKey = nextKey;
        badgeEl.classList.remove("green", "red");
        badgeEl.classList.add(signal.state);
        countEl.textContent = String(signal.remaining);
      }}

      render();
      window.setInterval(render, 250);
    }}

    startRenderLoop();
  }}

  boot();
</script>
"""


if "direction_key" not in st.session_state:
    st.session_state.direction_key = "NS"

active_direction = st.session_state.direction_key

st.markdown(
    """
<style>
#MainMenu, footer, header {
    visibility: hidden;
}

.block-container {
    padding-top: 1rem;
    padding-bottom: 0;
}

div[data-testid="stHorizontalBlock"] {
    gap: 0.75rem;
    flex-wrap: nowrap;
}

div[data-testid="column"] {
    min-width: 0;
}

div.stButton > button {
    height: 3.5rem;
    border-radius: 18px;
    border: 1px solid rgba(15, 23, 42, 0.12);
    background: #ffffff;
    color: #1f2937;
    font-size: 1rem;
    font-weight: 800;
    box-shadow: 0 8px 20px rgba(15, 23, 42, 0.08);
}

div.stButton > button[kind="primary"] {
    background: #111827;
    color: #f9fafb;
    border-color: #111827;
    box-shadow: 0 14px 26px rgba(15, 23, 42, 0.22);
}

div.stButton > button[kind="secondary"] {
    background: #ffffff;
    color: #1f2937;
    border-color: rgba(15, 23, 42, 0.14);
    box-shadow: 0 8px 20px rgba(15, 23, 42, 0.08);
}

div.stButton > button:hover {
    border-color: rgba(15, 23, 42, 0.3);
}

div[data-testid="column"]:first-child div.stButton > button {
    border-width: 2px;
}

@media (max-width: 640px) {
    .block-container {
        padding-left: 0.75rem;
        padding-right: 0.75rem;
    }

    div[data-testid="stHorizontalBlock"] {
        gap: 0.5rem;
        flex-wrap: nowrap;
    }

    div[data-testid="stHorizontalBlock"] > div {
        flex: 1 1 0;
        width: 0;
    }

    div.stButton > button {
        height: 3.45rem;
        border-radius: 16px;
        font-size: 0.95rem;
        padding-left: 0.25rem;
        padding-right: 0.25rem;
    }
}
</style>
""",
    unsafe_allow_html=True,
)

components.html(build_map_html(active_direction), height=540, scrolling=False)

col_ns, col_ew = st.columns(2, gap="small")

with col_ns:
    st.button(
        "横浜・新高島",
        key="direction_ns",
        type="primary" if active_direction == "NS" else "secondary",
        use_container_width=True,
        on_click=select_direction,
        args=("NS",),
    )

with col_ew:
    st.button(
        "高島町",
        key="direction_ew",
        type="primary" if active_direction == "EW" else "secondary",
        use_container_width=True,
        on_click=select_direction,
        args=("EW",),
    )
