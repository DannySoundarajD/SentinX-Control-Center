# -*- coding: utf-8 -*-
"""Dashboard page – animated performance manager with circular gauges and live wave graphs.

Visual design:
  • Circular ring gauges (Cairo) for CPU, RAM, GPU, Battery with glow effects
  • Real-time scrolling wave/area graphs for CPU and RAM history
  • Detail cards for storage, GPU VRAM, battery, and dock status
  • All animations driven by GLib.timeout_add at ~30fps
"""

from __future__ import annotations
import math
import platform
import subprocess
import colorsys
from collections import deque

from gi.repository import Gtk, GLib, Gdk
import cairo
import psutil


# ── Helpers ───────────────────────────────────────────────────────────────────

def get_cpu_model() -> str:
    try:
        with open("/proc/cpuinfo", "r") as f:
            for line in f:
                if "model name" in line:
                    return line.split(":", 1)[1].strip()
    except Exception:
        pass
    try:
        res = subprocess.run(["lscpu"], capture_output=True, text=True, timeout=2)
        if res.returncode == 0:
            for line in res.stdout.split("\n"):
                if line.startswith("Model name:"):
                    return line.split(":", 1)[1].strip()
    except Exception:
        pass
    return platform.processor() or "Unknown CPU"


def _hex_to_rgb(hex_color: str) -> tuple[float, float, float]:
    """Convert #RRGGBB to (r, g, b) 0..1 floats."""
    h = hex_color.lstrip("#")
    return (int(h[0:2], 16) / 255, int(h[2:4], 16) / 255, int(h[4:6], 16) / 255)


def _lerp(a: float, b: float, t: float) -> float:
    return a + (b - a) * t


def _value_color(pct: float) -> tuple[float, float, float]:
    """Return a smooth green→yellow→red color based on percentage 0..100."""
    if pct < 50:
        t = pct / 50.0
        r, g, b = _lerp(0.35, 0.87, t), _lerp(0.75, 0.80, t), _lerp(0.31, 0.18, t)
    else:
        t = (pct - 50) / 50.0
        r, g, b = _lerp(0.87, 0.97, t), _lerp(0.80, 0.32, t), _lerp(0.18, 0.28, t)
    return r, g, b


# ── Circular Ring Gauge ───────────────────────────────────────────────────────

class CircularGauge(Gtk.DrawingArea):
    """Animated circular ring gauge drawn with Cairo.

    Features
    --------
    * Dark track ring + coloured fill arc
    * Subtle outer glow using semi-transparent layered arcs
    * Smooth value animation (eased lerp toward target)
    * Central text: current percentage + label
    """

    SIZE = 160  # pixels

    def __init__(self, label: str, color: tuple[float, float, float] = (0.345, 0.651, 1.0)) -> None:
        super().__init__()
        self._label = label
        self._color = color          # base RGB 0..1
        self._target_pct = 0.0       # where we want to go
        self._current_pct = 0.0      # smoothly animated value
        self._sub_text = ""          # secondary text (e.g. "8.2 GB")

        self.set_size_request(self.SIZE, self.SIZE)
        self.set_draw_func(self._draw)

        # Animate at ~45fps
        GLib.timeout_add(22, self._tick)

    def set_value(self, pct: float, sub_text: str = "") -> None:
        """Set the target percentage (0..100)."""
        self._target_pct = max(0.0, min(100.0, pct))
        self._sub_text = sub_text

    def _tick(self) -> bool:
        # Ease toward target (exponential smoothing)
        self._current_pct = _lerp(self._current_pct, self._target_pct, 0.12)
        self.queue_draw()
        return True

    def _draw(self, area: Gtk.DrawingArea, cr: cairo.Context, w: int, h: int) -> None:
        cx, cy = w / 2, h / 2
        radius = min(w, h) / 2 - 14
        track_w = 14.0
        pct = self._current_pct / 100.0

        cr.set_source_rgba(0, 0, 0, 0)
        cr.paint()

        start_angle = math.pi * 0.75        # 135° (bottom-left)
        total_sweep = math.pi * 1.5         # 270° sweep

        # ── Track (background ring)
        cr.set_source_rgba(1, 1, 1, 0.05)
        cr.set_line_width(track_w)
        cr.set_line_cap(cairo.LINE_CAP_ROUND)
        cr.arc(cx, cy, radius, start_angle, start_angle + total_sweep)
        cr.stroke()

        if pct > 0.001:
            sweep = total_sweep * pct
            r, g, b = _value_color(self._current_pct)

            # ── Outer glow (3 layers, growing width, decreasing alpha)
            for glow_w, alpha in [(track_w + 14, 0.04), (track_w + 8, 0.09), (track_w + 3, 0.15)]:
                cr.set_source_rgba(r, g, b, alpha)
                cr.set_line_width(glow_w)
                cr.set_line_cap(cairo.LINE_CAP_ROUND)
                cr.arc(cx, cy, radius, start_angle, start_angle + sweep)
                cr.stroke()

            # ── Main coloured arc
            cr.set_line_width(track_w)
            cr.set_line_cap(cairo.LINE_CAP_ROUND)

            # Gradient along arc using a radial approximation (solid bright colour)
            cr.set_source_rgba(r, g, b, 0.95)
            cr.arc(cx, cy, radius, start_angle, start_angle + sweep)
            cr.stroke()

            # ── Tip dot (bright circle at arc end)
            tip_angle = start_angle + sweep
            tx = cx + math.cos(tip_angle) * radius
            ty = cy + math.sin(tip_angle) * radius
            cr.arc(tx, ty, track_w / 2 - 1, 0, 2 * math.pi)
            cr.set_source_rgba(r, g, b, 1.0)
            cr.fill()
            # Inner white highlight on tip
            cr.arc(tx, ty, track_w / 4, 0, 2 * math.pi)
            cr.set_source_rgba(1, 1, 1, 0.5)
            cr.fill()

        # ── Centre text: large percentage
        cr.select_font_face("Inter", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
        value_str = f"{int(self._current_pct)}%"
        cr.set_font_size(28)
        xb, yb, tw, th, _, _ = cr.text_extents(value_str)
        cr.set_source_rgba(0.9, 0.94, 0.98, 1.0)
        cr.move_to(cx - tw / 2 - xb, cy - yb / 2 - 8)
        cr.show_text(value_str)

        # ── Label below percentage
        cr.set_font_size(11)
        cr.select_font_face("Inter", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_NORMAL)
        lxb, lyb, ltw, lth, _, _ = cr.text_extents(self._label)
        cr.set_source_rgba(0.545, 0.580, 0.627, 1.0)
        cr.move_to(cx - ltw / 2 - lxb, cy + 14)
        cr.show_text(self._label)

        # ── Sub text (e.g. "8.2 GB")
        if self._sub_text:
            cr.set_font_size(10)
            sxb, syb, stw, sth, _, _ = cr.text_extents(self._sub_text)
            cr.set_source_rgba(0.435, 0.470, 0.517, 1.0)
            cr.move_to(cx - stw / 2 - sxb, cy + 30)
            cr.show_text(self._sub_text)


# ── Scrolling Wave Graph ──────────────────────────────────────────────────────

HISTORY_LEN = 120   # number of data points to keep


class WaveGraph(Gtk.DrawingArea):
    """Animated scrolling area / wave graph for multiple metrics.

    Each series is drawn as a smooth Bezier-interpolated filled area.
    """

    COLORS = [
        (0.345, 0.651, 1.0),   # CPU – blue
        (0.247, 0.729, 0.502),  # RAM – green
        (0.976, 0.502, 0.506),  # GPU – red/coral
    ]
    LABELS = ["CPU", "RAM", "GPU"]

    def __init__(self) -> None:
        super().__init__()
        self.set_vexpand(True)
        self.set_hexpand(True)
        self.set_size_request(-1, 160)

        # Each series: deque of 0..100 floats
        self._series: list[deque[float]] = [
            deque([0.0] * HISTORY_LEN, maxlen=HISTORY_LEN),
            deque([0.0] * HISTORY_LEN, maxlen=HISTORY_LEN),
            deque([0.0] * HISTORY_LEN, maxlen=HISTORY_LEN),
        ]
        self._current: list[float] = [0.0, 0.0, 0.0]  # smoothed render values

        self.set_draw_func(self._draw)
        GLib.timeout_add(33, self._tick)   # ~30fps

    def push(self, index: int, value: float) -> None:
        """Push a new data point (0..100) into series *index*."""
        if 0 <= index < len(self._series):
            self._series[index].append(max(0.0, min(100.0, value)))

    def _tick(self) -> bool:
        self.queue_draw()
        return True

    def _smooth_path(self, cr: cairo.Context, pts: list[tuple[float, float]]) -> None:
        """Draw a smooth catmull-rom style curve through pts."""
        if len(pts) < 2:
            return
        cr.move_to(*pts[0])
        for i in range(1, len(pts) - 1):
            x0, y0 = pts[i - 1]
            x1, y1 = pts[i]
            x2, y2 = pts[i + 1]
            cp1x = x1 - (x2 - x0) / 6
            cp1y = y1 - (y2 - y0) / 6
            cp2x = x1 + (x2 - x0) / 6
            cp2y = y1 + (y2 - y0) / 6
            cr.curve_to(cp1x, cp1y, cp2x, cp2y, x2, y2)
        cr.line_to(*pts[-1])

    def _draw(self, area: Gtk.DrawingArea, cr: cairo.Context, w: int, h: int) -> None:
        # Background
        cr.set_source_rgba(0.082, 0.102, 0.133, 1.0)
        cr.rectangle(0, 0, w, h)
        cr.fill()

        # Grid lines (subtle horizontal)
        cr.set_line_width(0.5)
        for pct in [25, 50, 75, 100]:
            y = h - (h * pct / 100) - 1
            cr.set_source_rgba(1, 1, 1, 0.04)
            cr.move_to(0, y)
            cr.line_to(w, y)
            cr.stroke()
            # Grid label
            cr.set_source_rgba(1, 1, 1, 0.15)
            cr.set_font_size(9)
            cr.select_font_face("Inter", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_NORMAL)
            cr.move_to(4, y - 3)
            cr.show_text(f"{pct}%")

        n = HISTORY_LEN
        step = w / (n - 1) if n > 1 else w

        for s_idx, series in enumerate(self._series):
            data = list(series)
            if not data:
                continue
            r, g, b = self.COLORS[s_idx]

            pts = [(i * step, h - (h * data[i] / 100) - 1) for i in range(len(data))]

            # Filled area with gradient
            pattern = cairo.LinearGradient(0, 0, 0, h)
            pattern.add_color_stop_rgba(0, r, g, b, 0.35)
            pattern.add_color_stop_rgba(1, r, g, b, 0.01)

            cr.set_source(pattern)
            cr.move_to(pts[0][0], h)
            self._smooth_path(cr, pts)
            cr.line_to(pts[-1][0], h)
            cr.close_path()
            cr.fill()

            # Stroke line on top
            cr.set_source_rgba(r, g, b, 0.85)
            cr.set_line_width(1.8)
            cr.move_to(*pts[0])
            self._smooth_path(cr, pts)
            cr.stroke()

            # Live value dot at right edge
            last_y = h - (h * data[-1] / 100) - 1
            cr.arc(w - 3, last_y, 4, 0, 2 * math.pi)
            cr.set_source_rgba(r, g, b, 1.0)
            cr.fill()
            cr.arc(w - 3, last_y, 2, 0, 2 * math.pi)
            cr.set_source_rgba(1, 1, 1, 0.9)
            cr.fill()

        # Legend bottom-right
        legend_x = w - 120
        legend_y = h - 12
        for idx, lbl in enumerate(self.LABELS):
            r, g, b = self.COLORS[idx]
            # Color dot
            cr.arc(legend_x + idx * 42, legend_y, 4, 0, 2 * math.pi)
            cr.set_source_rgba(r, g, b, 1.0)
            cr.fill()
            # Label
            cr.set_source_rgba(0.8, 0.85, 0.9, 0.8)
            cr.set_font_size(10)
            cr.move_to(legend_x + idx * 42 + 8, legend_y + 4)
            cr.show_text(lbl)


# ── Full Dashboard Page ───────────────────────────────────────────────────────

class DashboardPage(Gtk.Box):
    """Animated performance dashboard with circular gauges and live wave graphs."""

    def __init__(self) -> None:
        super().__init__(
            orientation=Gtk.Orientation.VERTICAL, spacing=0,
            margin_start=0, margin_end=0, margin_top=0, margin_bottom=0
        )
        self._cpu_model = get_cpu_model()

        # ── Outer scroll
        scroll = Gtk.ScrolledWindow()
        scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        scroll.set_hexpand(True)
        scroll.set_vexpand(True)
        self.append(scroll)

        inner = Gtk.Box(
            orientation=Gtk.Orientation.VERTICAL, spacing=0,
            margin_start=24, margin_end=24, margin_top=24, margin_bottom=24
        )
        scroll.set_child(inner)

        # ── Page header
        hdr = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        hdr.set_margin_bottom(20)
        t = Gtk.Label(label="Performance Monitor")
        t.set_xalign(0)
        t.get_style_context().add_class("page-title")
        hdr.append(t)
        st = Gtk.Label(label="Live system metrics — updated every second")
        st.set_xalign(0)
        st.get_style_context().add_class("page-subtitle")
        hdr.append(st)
        inner.append(hdr)

        # ── Gauge row ──────────────────────────────────────────────────────────
        gauge_card = self._make_gauge_card()
        inner.append(gauge_card)

        # ── Wave graph card ────────────────────────────────────────────────────
        wave_frame = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        wave_frame.get_style_context().add_class("settings-card")
        wave_frame.set_margin_top(12)

        wave_title_row = Gtk.Box(spacing=8)
        wave_title_row.get_style_context().add_class("card-title-row")
        wave_title_lbl = Gtk.Label(label="RESOURCE HISTORY")
        wave_title_lbl.get_style_context().add_class("card-title")
        wave_title_row.append(wave_title_lbl)
        wave_frame.append(wave_title_row)

        self._wave = WaveGraph()
        self._wave.set_margin_start(4)
        self._wave.set_margin_end(4)
        self._wave.set_margin_top(4)
        self._wave.set_margin_bottom(4)
        wave_frame.append(self._wave)
        inner.append(wave_frame)

        # ── Detail cards ───────────────────────────────────────────────────────
        detail_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        detail_row.set_margin_top(12)
        inner.append(detail_row)

        # Left column: CPU + Memory details
        left_col = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        left_col.set_hexpand(True)
        detail_row.append(left_col)

        from widgets.card import SettingsCard
        from widgets.setting_row import SettingsRow

        cpu_detail = SettingsCard(title="PROCESSOR", icon_name="cpu-symbolic")
        self._cpu_model_row = SettingsRow("Model", subtitle="—")
        cpu_detail.add(self._cpu_model_row)
        self._cpu_cores_row = SettingsRow("Cores / Threads", subtitle="—")
        cpu_detail.add(self._cpu_cores_row)
        self._cpu_freq_row = SettingsRow("Frequency", subtitle="—")
        cpu_detail.add(self._cpu_freq_row)
        self._cpu_usage_row = SettingsRow("Utilization", subtitle="—")
        cpu_detail.add(self._cpu_usage_row)
        left_col.append(cpu_detail)

        mem_detail = SettingsCard(title="MEMORY", icon_name="media-memory-symbolic")
        self._ram_total_row = SettingsRow("Total", subtitle="—")
        mem_detail.add(self._ram_total_row)
        self._ram_used_row = SettingsRow("In Use", subtitle="—")
        mem_detail.add(self._ram_used_row)
        self._ram_avail_row = SettingsRow("Available", subtitle="—")
        mem_detail.add(self._ram_avail_row)
        self._ram_swap_row = SettingsRow("Swap Used", subtitle="—")
        mem_detail.add(self._ram_swap_row)
        left_col.append(mem_detail)

        # Right column: GPU + Storage + Battery
        right_col = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        right_col.set_hexpand(True)
        detail_row.append(right_col)

        gpu_detail = SettingsCard(title="GPU", icon_name="video-display-symbolic")
        self._gpu_model_row = SettingsRow("Model", subtitle="—")
        gpu_detail.add(self._gpu_model_row)
        self._gpu_usage_row = SettingsRow("GPU Utilization", subtitle="—")
        gpu_detail.add(self._gpu_usage_row)
        self._gpu_vram_row = SettingsRow("VRAM", subtitle="—")
        gpu_detail.add(self._gpu_vram_row)
        right_col.append(gpu_detail)

        stor_detail = SettingsCard(title="STORAGE", icon_name="drive-harddisk-symbolic")
        self._stor_root_row = SettingsRow("Root  ( / )", subtitle="—")
        stor_detail.add(self._stor_root_row)
        self._stor_home_row = SettingsRow("Home  ( /home )", subtitle="—")
        stor_detail.add(self._stor_home_row)
        right_col.append(stor_detail)

        bat_detail = SettingsCard(title="BATTERY", icon_name="battery-symbolic")
        self._bat_charge_row = SettingsRow("Charge", subtitle="—")
        bat_detail.add(self._bat_charge_row)
        self._bat_state_row = SettingsRow("Status", subtitle="—")
        bat_detail.add(self._bat_state_row)
        right_col.append(bat_detail)

        # ── Initial data + schedule updates
        self._gpu_pct = 0.0
        self._update_slow()          # Storage / Battery (slow, once)
        GLib.timeout_add(1000, self._update_fast)   # CPU/RAM/GPU every 1 s
        GLib.timeout_add(8000, self._update_slow)   # Storage/Battery every 8 s

    # ─────────────────────────────────────────────────────────────────────────
    def _make_gauge_card(self) -> Gtk.Widget:
        """Build the four circular gauge widgets inside a card."""
        card = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        card.get_style_context().add_class("settings-card")

        title_row = Gtk.Box(spacing=8)
        title_row.get_style_context().add_class("card-title-row")
        title_lbl = Gtk.Label(label="LIVE METRICS")
        title_lbl.get_style_context().add_class("card-title")
        title_row.append(title_lbl)
        card.append(title_row)

        gauge_row = Gtk.Box(
            orientation=Gtk.Orientation.HORIZONTAL,
            spacing=0, homogeneous=True
        )
        gauge_row.set_margin_top(16)
        gauge_row.set_margin_bottom(16)

        self._cpu_gauge = CircularGauge("CPU", _hex_to_rgb("#58a6ff"))
        self._ram_gauge = CircularGauge("RAM", _hex_to_rgb("#3fb950"))
        self._gpu_gauge = CircularGauge("GPU", _hex_to_rgb("#f85149"))
        self._bat_gauge = CircularGauge("Battery", _hex_to_rgb("#d2a519"))

        for g in [self._cpu_gauge, self._ram_gauge, self._gpu_gauge, self._bat_gauge]:
            wrapper = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
            wrapper.set_halign(Gtk.Align.CENTER)
            wrapper.set_hexpand(True)
            wrapper.append(g)
            gauge_row.append(wrapper)

        card.append(gauge_row)
        return card

    # ── Fast update (every 1s): CPU, RAM, GPU ─────────────────────────────────
    def _update_fast(self) -> bool:
        from widgets.setting_row import SettingsRow

        # CPU
        try:
            cpu_pct = psutil.cpu_percent(interval=None)
            cores = psutil.cpu_count(logical=False) or "?"
            threads = psutil.cpu_count(logical=True) or "?"
            freq = psutil.cpu_freq()
            freq_str = f"{freq.current / 1000:.2f} GHz" if freq else "N/A"

            self._cpu_gauge.set_value(cpu_pct, f"{cpu_pct:.1f}%")
            self._cpu_model_row.set_subtitle(self._cpu_model)
            self._cpu_cores_row.set_subtitle(f"{cores} cores / {threads} threads")
            self._cpu_freq_row.set_subtitle(freq_str)
            self._cpu_usage_row.set_subtitle(f"{cpu_pct:.1f} %")
            self._wave.push(0, cpu_pct)
        except Exception:
            pass

        # RAM
        try:
            mem = psutil.virtual_memory()
            swap = psutil.swap_memory()
            used_gb = mem.used / (1024 ** 3)
            total_gb = mem.total / (1024 ** 3)
            avail_gb = mem.available / (1024 ** 3)
            swap_gb = swap.used / (1024 ** 3)

            self._ram_gauge.set_value(mem.percent, f"{used_gb:.1f} GB")
            self._ram_total_row.set_subtitle(f"{total_gb:.1f} GB")
            self._ram_used_row.set_subtitle(f"{used_gb:.1f} GB  ({mem.percent:.0f}%)")
            self._ram_avail_row.set_subtitle(f"{avail_gb:.1f} GB")
            self._ram_swap_row.set_subtitle(f"{swap_gb:.1f} GB  ({swap.percent:.0f}%)")
            self._wave.push(1, mem.percent)
        except Exception:
            pass

        # GPU via nvidia-smi
        try:
            res = subprocess.run(
                ["nvidia-smi",
                 "--query-gpu=name,utilization.gpu,memory.total,memory.used",
                 "--format=csv,noheader,nounits"],
                capture_output=True, text=True, timeout=2
            )
            if res.returncode == 0 and res.stdout.strip():
                parts = [p.strip() for p in res.stdout.strip().split(",")]
                name = parts[0]
                gpu_pct = float(parts[1]) if len(parts) > 1 else 0.0
                vram_total = float(parts[2]) if len(parts) > 2 else 0.0
                vram_used  = float(parts[3]) if len(parts) > 3 else 0.0

                vram_pct = (vram_used / vram_total * 100) if vram_total > 0 else 0.0
                vram_str = (
                    f"{vram_used/1024:.2f} GB / {vram_total/1024:.1f} GB  ({vram_pct:.0f}%)"
                )

                self._gpu_gauge.set_value(gpu_pct, f"{gpu_pct:.0f}%")
                self._gpu_model_row.set_subtitle(name)
                self._gpu_usage_row.set_subtitle(f"{gpu_pct:.0f} %")
                self._gpu_vram_row.set_subtitle(vram_str)
                self._wave.push(2, gpu_pct)
        except Exception:
            pass

        return True

    # ── Slow update (every 8s): Storage, Battery ──────────────────────────────
    def _update_slow(self) -> bool:
        # Storage
        for path, row in [("/", self._stor_root_row), ("/home", self._stor_home_row)]:
            try:
                d = psutil.disk_usage(path)
                row.set_subtitle(
                    f"{d.used/(1024**3):.1f} GB / {d.total/(1024**3):.0f} GB  ({d.percent:.0f}% used)"
                )
            except Exception:
                row.set_subtitle("N/A")

        # Battery
        try:
            bat = psutil.sensors_battery()
            if bat:
                pct = bat.percent
                state = "⚡ Charging" if bat.power_plugged else "🔋 Discharging"
                self._bat_gauge.set_value(pct, f"{pct:.0f}%")
                self._bat_charge_row.set_subtitle(f"{pct:.0f} %")
                self._bat_state_row.set_subtitle(state)
            else:
                self._bat_gauge.set_value(0, "N/A")
                self._bat_charge_row.set_subtitle("No battery")
                self._bat_state_row.set_subtitle("N/A")
        except Exception:
            pass

        return True
