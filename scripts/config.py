"""Everything the cards say, and the brand. Edit here, then run render_readme_cards.py."""

LOGIN = "theommishra-dev"

# Brand: amber on near-black (no personal website to copy from, chosen 2026-11-19).
COLORS = {
    "bg": "#0F1114",
    "panel": "#15181C",
    "line": "#262A30",
    "ink": "#EEEAE3",
    "muted": "#8E8B85",
    "faint": "#4A4D52",
    "accent": "#FFB224",
    "accent_ink": "#FFC65C",  # amber for small text, a touch lighter for contrast
    "bar": "#5A4520",         # every month that is not the best one
}
# Sequential ramp for the contribution graph: empty cell, then 4 steps dark -> bright amber.
RAMP = ["#1C1F24", "#4A3714", "#87600F", "#C98A12", "#FFB224"]

PORTRAIT = True  # ASCII portrait from data/portrait.txt (make it with scripts/make_portrait.py)

HERO = {
    "name": ["Om", "Mishra"],
    "kicker": "Bologna, Italy  ·  open to detection engineering roles",
    "about": ["Cybersecurity engineer. I make detection rules, machine",
              "learning and LLMs work together in the SOC."],
    "tags": ["Elastic SIEM", "Detection engineering", "LLM triage", "MCP"],
}

TILES = [
    {"file": "security", "label": "SECURITY", "value": 40000, "fmt": "{:,}", "suffix": "+",
     "caption": ["EV chargers watched by", "my detections"], "cta": "LinkedIn",
     "href": "https://www.linkedin.com/in/theommishra"},
    {"file": "youtube", "label": "YOUTUBE", "value": 5.5, "fmt": "{:.1f}", "suffix": "k",
     "caption": ["subscribers to The Om", "Vlogs | In Italy"], "cta": "Watch",
     "href": "https://www.youtube.com/@TheOmVlogsOfficial"},
    {"file": "skills", "label": "BUILDING WITH CLAUDE", "value": 5, "fmt": "{:d}", "suffix": "",
     "caption": ["Anthropic certifications;", "my open Claude skills"], "cta": "claude-skills",
     "href": "https://github.com/theommishra-dev/claude-skills"},
]

# Featured repos: text is written here (fits the card), stars and language come from the API.
REPOS = [
    {"name": "VoiceFlow", "lines": ["Free, private push-to-talk dictation for", "Apple Silicon Macs. Local Whisper on MLX,", "nothing leaves the machine."]},
    {"name": "claude-skills", "lines": ["Claude Code skills I build and use. First:", "resume-optimizer, which tailors a resume", "to any job description."]},
    {"name": "smart-water-bowl-iot", "lines": ["ESP32 sensor node over MQTT, HTTP and CoAP", "into InfluxDB and Grafana, with 24 hour", "water level forecasting."]},
    {"name": "satellite-segmentation-unet", "lines": ["Multi-class land cover segmentation of", "aerial images with a U-Net built from", "scratch in TensorFlow/Keras."]},
]
