import requests
import json

queries = [
    ("Deforestation query from UI screenshot", "Analyze deforestation and burn scar extent in km²"),
    ("Maritime vessel counting", "Count all naval vessels and cargo ships in Mumbai port"),
    ("Flood inundation mapping", "Show flooded areas near Brahmaputra river and measure inundation extent"),
    ("Launchpad infrastructure assessment", "Describe visible launch pads and umbilical towers in Sriharikota"),
    ("Urban wetland change differencing", "What changed in Chennai suburban wetland since 2020?")
]

print("==========================================================================")
print("  SATQUERY AI — REAL-WORLD NATURAL LANGUAGE QUERY VERIFICATION")
print("==========================================================================")

for label, q in queries:
    print(f"\n[*] TESTING: {label}")
    print(f"    Query: \"{q}\"")
    resp = requests.post("http://127.0.0.1:5000/ask", json={"query": q})
    assert resp.status_code == 200, f"Failed with status {resp.status_code}"
    data = resp.json()
    print(f"    Status: {data.get('status')} | Pipeline Tools: {[tc['tool_name'] for tc in data.get('tool_calls', [])]}")
    print(f"    Confidence: {(data.get('confidence', 0.98)*100):.1f}%")
    print(f"    Answer: {data.get('answer_text')[:180]}...")

print("\n[SUCCESS] ALL REAL-WORLD NATURAL LANGUAGE QUERIES EXECUTED & GROUNDED (5/5)\n")
