#!/usr/bin/env python3
"""Record a live NEXUS Streamlit console walkthrough via Playwright Chromium."""
from __future__ import annotations

import shutil
import subprocess
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
BASE = "http://127.0.0.1:8501"
SHOT = ROOT / "screenshots" / "nexus"
OUT_MP4 = ROOT / "artifacts" / "nexus-decision-intelligence-demo.mp4"
VID_DIR = Path("/tmp/nexus-demo-record/pw-video")
FFMPEG = "/usr/bin/ffmpeg"

# Walk major current tabs. shot_names may be a str or list (README keeps legacy names).
# Actions: investigate / predict / graph / None
SECTIONS = [
    ("Command Center", "Command Center — live KPIs · Wilson OTIF CI · value at stake", "01-command-center.png", None),
    ("Decision Board", "Decision Board — next action · late $ by warehouse · hold unless power clears", "02-decision-board.png", None),
    ("AI Analyst", "AI Analyst — multi-agent investigate (mock LLM)", ["03-ai-analyst.png", "02-ai-analyst.png"], "investigate"),
    ("Predictions", "Predictions — demand forecast + OTIF anomaly", "04-predictions.png", "predict"),
    ("Inference Monitor", "Inference Monitor — route mock / small / large (not causal inference)", "03-inference-monitor.png", None),
    ("GraphRAG", "GraphRAG — in-process supplier/OTIF graph snapshot", "05-graphrag.png", "graph"),
    ("Inferential", "Inferential — estimand · adjustment · CI · power · hold/act", "08-inferential.png", None),
    ("Copilot", "Copilot — Monday ops brief from extract KPIs", "06-copilot.png", None),
    ("Quality", "Quality — freshness / schema / null checks", "07-quality.png", None),
]


def wait_streamlit(page, ms: int = 2000) -> None:
    page.wait_for_timeout(ms)
    try:
        page.wait_for_selector('[data-testid="stSpinner"]', state="detached", timeout=4000)
    except Exception:
        pass


def set_caption(page, text: str) -> None:
    page.evaluate(
        """(text) => {
          let el = document.getElementById('nexus-demo-caption');
          if (!el) {
            el = document.createElement('div');
            el.id = 'nexus-demo-caption';
            el.style.cssText = [
              'position:fixed','left:24px','right:24px','bottom:18px','z-index:99999',
              'background:rgba(11,31,51,0.92)','color:#E8F1F8','padding:10px 16px',
              'border-radius:10px','font:600 15px/1.35 system-ui,sans-serif',
              'box-shadow:0 4px 18px rgba(0,0,0,0.35)','pointer-events:none',
              'letter-spacing:0.01em'
            ].join(';');
            document.body.appendChild(el);
          }
          el.textContent = text;
        }""",
        text,
    )


def show_title_card(page) -> None:
    page.evaluate(
        """() => {
          const overlay = document.createElement('div');
          overlay.id = 'nexus-title-card';
          overlay.style.cssText = [
            'position:fixed','inset:0','z-index:100000','display:flex','flex-direction:column',
            'align-items:center','justify-content:center',
            'background:linear-gradient(135deg,#0B1F33 0%,#123A56 55%,#1a4d6e 100%)',
            'color:#E8F1F8','font-family:system-ui,sans-serif','text-align:center'
          ].join(';');
          overlay.innerHTML = `
            <div style="font-size:42px;font-weight:700;letter-spacing:0.06em;margin-bottom:12px;">
              NEXUS Decision Intelligence
            </div>
            <div style="font-size:18px;opacity:0.9;max-width:720px;line-height:1.45;">
              Local-first retail + supply-chain console · DuckDB · FastAPI · Streamlit · mock LLM
            </div>
            <div style="margin-top:28px;font-size:14px;opacity:0.7;">
              Live demo · Decision Board · Inferential engineering · GraphRAG · public extracts
            </div>`;
          document.body.appendChild(overlay);
        }"""
    )
    page.wait_for_timeout(2200)
    page.evaluate(
        """() => {
          const el = document.getElementById('nexus-title-card');
          if (el) el.remove();
        }"""
    )


def click_tab(page, name: str) -> None:
    page.get_by_role("tab", name=name).click()
    wait_streamlit(page, 1400)


def dismiss_banners(page) -> None:
    for text in ("Got it", "Close", "Dismiss"):
        try:
            btn = page.get_by_role("button", name=text)
            if btn.count() and btn.first.is_visible(timeout=400):
                btn.first.click()
        except Exception:
            pass


def _click_button(page, name: str, wait_ms: int = 2500) -> bool:
    try:
        btn = page.get_by_role("button", name=name).first
        btn.wait_for(state="visible", timeout=5000)
        btn.scroll_into_view_if_needed()
        btn.click(timeout=5000)
        page.wait_for_timeout(wait_ms)
        return True
    except Exception as e:
        print(f"button warn [{name}]:", e)
        return False


def run_action(page, action: str | None) -> None:
    if action == "investigate":
        if _click_button(page, "Investigate", 1800):
            try:
                page.get_by_text("Drivers", exact=False).first.wait_for(timeout=25000)
            except Exception:
                pass
            page.wait_for_timeout(1600)
    elif action == "predict":
        _click_button(page, "Predict demand", 2500)
        _click_button(page, "Score anomaly", 1600)
    elif action == "graph":
        _click_button(page, "Retrieve graph", 2200)


def save_shots(page, shot_names) -> None:
    names = shot_names if isinstance(shot_names, list) else [shot_names]
    for name in names:
        page.screenshot(path=str(SHOT / name), full_page=False)


def encode_mp4(webm: Path, dest: Path) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    tmp = dest.with_suffix(".tmp.mp4")
    cmd = [
        FFMPEG, "-y", "-i", str(webm),
        "-c:v", "libx264", "-pix_fmt", "yuv420p",
        "-vf", "scale=1280:720:force_original_aspect_ratio=decrease,pad=1280:720:(ow-iw)/2:(oh-ih)/2",
        "-r", "30",
        "-preset", "medium", "-crf", "23",
        "-movflags", "+faststart",
        "-an",
        str(tmp),
    ]
    subprocess.run(cmd, check=True, capture_output=True)
    shutil.move(str(tmp), str(dest))


def main() -> None:
    if VID_DIR.exists():
        shutil.rmtree(VID_DIR)
    VID_DIR.mkdir(parents=True, exist_ok=True)
    SHOT.mkdir(parents=True, exist_ok=True)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            viewport={"width": 1280, "height": 720},
            record_video_dir=str(VID_DIR),
            record_video_size={"width": 1280, "height": 720},
        )
        page = context.new_page()
        page.goto(BASE, wait_until="networkidle", timeout=90000)
        wait_streamlit(page, 4500)
        dismiss_banners(page)

        show_title_card(page)
        set_caption(page, "NEXUS Decision Intelligence — live Streamlit console")

        for tab, caption, shot_name, action in SECTIONS:
            print(f"→ {tab}")
            click_tab(page, tab)
            set_caption(page, caption)
            page.wait_for_timeout(900)
            run_action(page, action)
            save_shots(page, shot_name)
            page.wait_for_timeout(1100)

        click_tab(page, "Command Center")
        set_caption(page, "NEXUS — portfolio local demo · mock LLM · DuckDB warehouse")
        page.wait_for_timeout(1800)

        page.close()
        context.close()
        browser.close()

    videos = sorted(VID_DIR.glob("*.webm"))
    if not videos:
        raise SystemExit("No Playwright webm produced")
    webm = videos[0]
    print("WEBM", webm, "size", webm.stat().st_size)
    encode_mp4(webm, OUT_MP4)
    print("MP4", OUT_MP4, "size", OUT_MP4.stat().st_size)


if __name__ == "__main__":
    t0 = time.time()
    main()
    print(f"done in {time.time() - t0:.1f}s")
