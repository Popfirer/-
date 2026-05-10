import tkinter as tk
from tkinter import ttk, simpledialog, messagebox
from datetime import datetime, timedelta, timezone
import calendar as _calendar
import threading
import urllib.request
import json
import time as _time

VERSION = "0.1"

WEEKDAYS = ["星期一", "星期二", "星期三", "星期四", "星期五", "星期六", "星期日"]

# ── 配色方案 ──────────────────────────────────────────
WINDOW_BG = "#f0f2f5"
CARD_BG = "#ffffff"
CARD_FG = "#1a1a2e"
ACCENT = "#2c3e50"
ACCENT_LIGHT = "#34495e"
MUTED = "#7f8c8d"
BORDER = "#d5d8dc"
HIGHLIGHT = "#e74c3c"
WUXI_GOLD = "#c0392b"

# ── wttr.in 天气代码 → 图标映射 ────────────────────────
WEATHER_ICONS = {
    "113": "☀️", "116": "🌤️", "119": "☁️", "122": "☁️",
    "143": "🌫️", "176": "🌦️", "179": "🌧️", "182": "🌨️",
    "185": "🌧️", "200": "⛈️", "227": "🌨️", "230": "🌨️",
    "248": "🌫️", "260": "🌫️", "263": "🌧️", "266": "🌧️",
    "281": "🌧️", "284": "🌧️", "293": "🌦️", "296": "🌧️",
    "299": "🌧️", "302": "🌧️", "305": "🌧️", "308": "🌧️",
    "311": "🌧️", "314": "🌧️", "317": "🌨️", "320": "🌨️",
    "323": "🌨️", "326": "🌨️", "329": "🌨️", "332": "🌨️",
    "335": "❄️", "338": "❄️", "350": "🌨️", "353": "🌦️",
    "356": "🌧️", "359": "🌧️", "362": "🌨️", "365": "🌨️",
    "368": "🌨️", "371": "🌨️", "374": "🌨️", "377": "🌨️",
    "386": "⛈️", "389": "⛈️", "392": "⛈️", "395": "⛈️",
}

# ── 城市数据 ───────────────────────────────────────────
ALL_CITIES = {
    "北京":    {"base": 8,  "dst": None,      "query": "Beijing",      "cc": "CN"},
    "上海":    {"base": 8,  "dst": None,      "query": "Shanghai",     "cc": "CN"},
    "香港":    {"base": 8,  "dst": None,      "query": "Hong+Kong",    "cc": "CN"},
    "台北":    {"base": 8,  "dst": None,      "query": "Taipei",       "cc": "CN"},
    "无锡":    {"base": 8,  "dst": None,      "query": "Wuxi",         "cc": "CN"},
    "新加坡":  {"base": 8,  "dst": None,      "query": "Singapore",    "cc": "SG"},
    "韩国":    {"base": 9,  "dst": None,      "query": "Seoul",        "cc": "KR"},
    "首尔":    {"base": 9,  "dst": None,      "query": "Seoul",        "cc": "KR"},
    "釜山":    {"base": 9,  "dst": None,      "query": "Busan",        "cc": "KR"},
    "东京":    {"base": 9,  "dst": None,      "query": "Tokyo",        "cc": "JP"},
    "越南":    {"base": 7,  "dst": None,      "query": "Ho+Chi+Minh",  "cc": "VN"},
    "胡志明":  {"base": 7,  "dst": None,      "query": "Ho+Chi+Minh",  "cc": "VN"},
    "曼谷":    {"base": 7,  "dst": None,      "query": "Bangkok",      "cc": "TH"},
    "雅加达":  {"base": 7,  "dst": None,      "query": "Jakarta",      "cc": "ID"},
    "迪拜":    {"base": 4,  "dst": None,      "query": "Dubai",        "cc": "AE"},
    "莫斯科":  {"base": 3,  "dst": None,      "query": "Moscow",       "cc": "RU"},
    "西班牙":  {"base": 1,  "dst": "europe",  "query": "Madrid",       "cc": "ES"},
    "马德里":  {"base": 1,  "dst": "europe",  "query": "Madrid",       "cc": "ES"},
    "潘普罗纳":{"base": 1,  "dst": "europe",  "query": "Pamplona",     "cc": "ES"},
    "巴黎":    {"base": 1,  "dst": "europe",  "query": "Paris",        "cc": "FR"},
    "柏林":    {"base": 1,  "dst": "europe",  "query": "Berlin",       "cc": "DE"},
    "罗马":    {"base": 1,  "dst": "europe",  "query": "Rome",         "cc": "IT"},
    "伦敦":    {"base": 0,  "dst": "europe",  "query": "London",       "cc": "GB"},
    "纽约":    {"base": -5, "dst": "us",      "query": "New+York",     "cc": "US"},
    "洛杉矶":  {"base": -8, "dst": "us",      "query": "Los+Angeles",  "cc": "US"},
    "芝加哥":  {"base": -6, "dst": "us",      "query": "Chicago",      "cc": "US"},
    "多伦多":  {"base": -5, "dst": "us",      "query": "Toronto",      "cc": "CA"},
    "温哥华":  {"base": -8, "dst": "us",      "query": "Vancouver",    "cc": "CA"},
    "墨西哥城":{"base": -6, "dst": None,      "query": "Mexico+City",  "cc": "MX"},
    "悉尼":    {"base": 10, "dst": "sydney",  "query": "Sydney",       "cc": "AU"},
    "墨尔本":  {"base": 10, "dst": "sydney",  "query": "Melbourne",    "cc": "AU"},
    "奥克兰":  {"base": 12, "dst": "sydney",  "query": "Auckland",     "cc": "NZ"},
    "圣保罗":  {"base": -3, "dst": None,      "query": "Sao+Paulo",    "cc": "BR"},
    "布宜诺斯艾利斯": {"base": -3, "dst": None, "query": "Buenos+Aires", "cc": "AR"},
}

DEFAULT_CITIES = ["无锡", "首尔", "潘普罗纳"]


def _get_nth_weekday_sunday(year, month, nth):
    if nth == -1 or nth == "last":
        for day in range(31, 24, -1):
            try:
                return datetime(year, month, day, tzinfo=timezone.utc)
            except ValueError:
                continue
    else:
        nth_map = {"first": 1, "second": 2, "third": 3, "fourth": 4}
        n = nth_map.get(nth, nth)
        first = datetime(year, month, 1, tzinfo=timezone.utc)
        days_until_sunday = (6 - first.weekday()) % 7
        first_sunday = first + timedelta(days=days_until_sunday)
        return first_sunday + timedelta(weeks=n - 1)


def _is_summer_north(utc_dt, start_month, start_week, end_month, end_week):
    year = utc_dt.year
    spring = _get_nth_weekday_sunday(year, start_month, start_week)
    fall = _get_nth_weekday_sunday(year, end_month, end_week)
    return spring <= utc_dt < fall


def _is_summer_south(utc_dt, start_month, start_week, end_month, end_week):
    year = utc_dt.year
    start = _get_nth_weekday_sunday(year, start_month, start_week)
    end = _get_nth_weekday_sunday(year, end_month, end_week)
    if start_month > end_month:
        if utc_dt >= start or utc_dt < end:
            return True
        return False
    else:
        return start <= utc_dt < end


def get_utc_offset(city, utc_dt):
    info = ALL_CITIES.get(city)
    if info is None:
        return 0
    base = info["base"]
    rule = info["dst"]
    if rule is None:
        return base
    if rule == "europe":
        if _is_summer_north(utc_dt, start_month=3, start_week="last",
                            end_month=10, end_week="last"):
            return base + 1
        return base
    if rule == "us":
        if _is_summer_north(utc_dt, start_month=3, start_week="second",
                            end_month=11, end_week="first"):
            return base + 1
        return base
    if rule == "sydney":
        if _is_summer_south(utc_dt, start_month=10, start_week="first",
                            end_month=4, end_week="first"):
            return base + 1
        return base
    return base


# ── 天气 / 节假日缓存 ──────────────────────────────────
_weather_cache = {}
_holiday_cache = {}

WEATHER_TTL = 1800
HOLIDAY_TTL = 86400


def _fetch_weather(city):
    info = ALL_CITIES.get(city)
    if info is None:
        return
    query = info.get("query", city)
    try:
        url = f"https://wttr.in/{query}?format=j1&lang=zh"
        req = urllib.request.Request(url, headers={"User-Agent": "WorldClock/0.1"})
        with urllib.request.urlopen(req, timeout=8) as resp:
            data = json.loads(resp.read())
            current = data["current_condition"][0]
            temp = current["temp_C"]
            desc = current["weatherDesc"][0]["value"]
            code = current.get("weatherCode", "")
            icon = WEATHER_ICONS.get(code, "🌡️")
            text = f"{icon}  {temp}°C  {desc}"
            _weather_cache[city] = (text, _time.time())
    except Exception:
        pass


def _get_weather(city):
    entry = _weather_cache.get(city)
    if entry is None or _time.time() - entry[1] > WEATHER_TTL:
        t = threading.Thread(target=_fetch_weather, args=(city,), daemon=True)
        t.start()
    return entry[0] if entry else None


def _fetch_holiday(cc):
    try:
        url = f"https://date.nager.at/api/v3/NextPublicHolidays/{cc}"
        req = urllib.request.Request(url, headers={"User-Agent": "WorldClock/0.1"})
        with urllib.request.urlopen(req, timeout=8) as resp:
            data = json.loads(resp.read())
            today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
            today_str = today
            for h in data:
                if h["date"] == today_str:
                    _holiday_cache[cc] = (h["localName"], h["date"], _time.time())
                    return
            _holiday_cache[cc] = ("", "", _time.time())
    except Exception:
        pass


def _get_holiday(cc):
    entry = _holiday_cache.get(cc)
    if entry is None or _time.time() - entry[2] > HOLIDAY_TTL:
        t = threading.Thread(target=_fetch_holiday, args=(cc,), daemon=True)
        t.start()
    if entry and entry[0]:
        return entry[0]
    return None


# ═══════════════════════════════════════════════════════════
#  城市时钟卡片
# ═══════════════════════════════════════════════════════════

class CityClock(tk.Frame):
    """单个城市的时钟卡片，带天气和节假日信息"""

    def __init__(self, parent, city, on_right_click):
        super().__init__(parent, bg=CARD_BG, padx=18, pady=14,
                         highlightbackground="#c8ccd0", highlightthickness=1,
                         highlightcolor="#c8ccd0")
        self.city = city

        # 城市名
        header = tk.Frame(self, bg=CARD_BG)
        header.pack(fill="x")

        is_wuxi = (city == "无锡")
        name_fg = WUXI_GOLD if is_wuxi else ACCENT
        name_font = ("Microsoft YaHei UI", 13, "bold")
        self.name_label = tk.Label(header, text=city, font=name_font,
                                   bg=CARD_BG, fg=name_fg)
        self.name_label.pack(side="left")
        if is_wuxi:
            tag = tk.Label(header, text="📍 本地", font=("Microsoft YaHei UI", 8),
                           bg=CARD_BG, fg=WUXI_GOLD)
            tag.pack(side="left", padx=(6, 0))

        # 时间
        self.time_label = tk.Label(self, text="", font=("Consolas", 28, "bold"),
                                   bg=CARD_BG, fg=CARD_FG)
        self.time_label.pack(anchor="w", pady=(6, 2))

        # 天气（含图标）
        self.weather_label = tk.Label(self, text="", font=("Microsoft YaHei UI", 10),
                                      bg=CARD_BG, fg="#555555")
        self.weather_label.pack(anchor="w")

        # 日期 + 星期 + 周数
        self.info_label = tk.Label(self, text="", font=("Microsoft YaHei UI", 10),
                                   bg=CARD_BG, fg=MUTED)
        self.info_label.pack(anchor="w")

        # 节假日
        self.holiday_label = tk.Label(self, text="", font=("Microsoft YaHei UI", 9, "bold"),
                                      bg=CARD_BG, fg=HIGHLIGHT)
        self.holiday_label.pack(anchor="w")

        # 右键菜单绑定
        for w in (self, self.name_label, self.time_label,
                  self.weather_label, self.info_label, self.holiday_label):
            w.bind("<Button-3>", lambda e, c=city: on_right_click(e, c))
        self.name_label.bind("<Button-1>", lambda e, c=city: on_right_click(e, c))

        self._refresh_weather()
        self._tick_count = 0
        self.update()

    def _refresh_weather(self):
        t = threading.Thread(target=self._bg_fetch, daemon=True)
        t.start()

    def _bg_fetch(self):
        _fetch_weather(self.city)
        info = ALL_CITIES.get(self.city)
        if info:
            _fetch_holiday(info.get("cc", ""))

    def update(self):
        if not self.winfo_exists():
            return
        utc_now = datetime.now(timezone.utc)
        offset = get_utc_offset(self.city, utc_now)
        local_now = utc_now + timedelta(hours=offset)
        time_str = local_now.strftime("%H:%M")
        date_str = f"{local_now.month}月{local_now.day}日"
        weekday_str = WEEKDAYS[local_now.weekday()]
        self.time_label.config(text=time_str)
        week_num = local_now.isocalendar()[1]
        self.info_label.config(text=f"{date_str}  {weekday_str}  第{week_num}周")

        w = _get_weather(self.city)
        self.weather_label.config(text=w if w else "⏳ 加载中...")

        info = ALL_CITIES.get(self.city)
        if info:
            h = _get_holiday(info.get("cc", ""))
            self.holiday_label.config(text=f"🎉 {h}" if h else "")

        self._tick_count += 1
        if self._tick_count % 900 == 0:
            self._refresh_weather()

        self.after(200, self.update)


# ═══════════════════════════════════════════════════════════
#  2026 年日历（带无锡日期高亮）
# ═══════════════════════════════════════════════════════════

WEEKDAY_HEADERS = ["一", "二", "三", "四", "五", "六", "日"]
MONTH_NAMES = ["1月", "2月", "3月", "4月", "5月", "6月",
               "7月", "8月", "9月", "10月", "11月", "12月"]
HEADER_BG = "#e8e8e8"
TODAY_BG = ACCENT
TODAY_FG = "#ffffff"
WEEKEND_FG = "#c0392b"


class CalendarTab(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent, bg=WINDOW_BG)
        self._today = datetime.now()
        self._build()

    def _build(self):
        # ── 顶部：无锡当天日期大标题 ──
        top_bar = tk.Frame(self, bg=CARD_BG, highlightbackground=BORDER,
                          highlightthickness=1)
        top_bar.pack(fill="x", padx=16, pady=(12, 6))

        wuxi_dt = self._today
        wuxi_date_str = f"{wuxi_dt.year}年{wuxi_dt.month}月{wuxi_dt.day}日"
        wuxi_weekday = WEEKDAYS[wuxi_dt.weekday()]
        wuxi_weeknum = wuxi_dt.isocalendar()[1]

        tk.Label(top_bar, text="🏠 无锡 · 今天",
                 font=("Microsoft YaHei UI", 11, "bold"),
                 bg=CARD_BG, fg=WUXI_GOLD).pack(side="left", padx=(16, 12), pady=10)
        tk.Label(top_bar,
                 text=f"{wuxi_date_str}  {wuxi_weekday}  第{wuxi_weeknum}周",
                 font=("Microsoft YaHei UI", 15, "bold"),
                 bg=CARD_BG, fg=CARD_FG).pack(side="left", padx=(0, 10), pady=10)
        tk.Label(top_bar, text="UTC+8  ·  中国标准时间",
                 font=("Microsoft YaHei UI", 9),
                 bg=CARD_BG, fg=MUTED).pack(side="right", padx=(0, 20), pady=10)

        # ── 可滚动的月历区域 ──
        canvas = tk.Canvas(self, bg=WINDOW_BG, highlightthickness=0)
        scrollbar = ttk.Scrollbar(self, orient="vertical", command=canvas.yview)
        self._scroll_frame = tk.Frame(canvas, bg=WINDOW_BG)
        self._scroll_frame.bind("<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=self._scroll_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        self._bind_mousewheel(canvas)

        self._month_frames = {}
        for month in range(1, 13):
            row, col = divmod(month - 1, 3)
            mf = self._build_month(self._scroll_frame, 2026, month)
            mf.grid(row=row, column=col, padx=12, pady=10, sticky="n")
            self._month_frames[month] = mf
        for c in range(3):
            self._scroll_frame.grid_columnconfigure(c, weight=1)

    def _bind_mousewheel(self, canvas):
        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
        canvas.bind_all("<MouseWheel>", _on_mousewheel)
        canvas.bind("<Enter>", lambda e: canvas.bind_all("<MouseWheel>", _on_mousewheel))
        canvas.bind("<Leave>", lambda e: canvas.unbind_all("<MouseWheel>"))

    def _build_month(self, parent, year, month):
        frame = tk.Frame(parent, bg=CARD_BG, highlightbackground=BORDER,
                         highlightthickness=1, padx=10, pady=8)

        # 月份标题
        is_today_month = (year == self._today.year and month == self._today.month)
        month_fg = WUXI_GOLD if is_today_month else ACCENT
        tk.Label(frame, text=MONTH_NAMES[month - 1],
                 font=("Microsoft YaHei UI", 12, "bold"),
                 bg=CARD_BG, fg=month_fg).grid(row=0, column=0, columnspan=8, pady=(0, 4))

        # 周 列 + 星期标题
        tk.Label(frame, text="周", font=("Microsoft YaHei UI", 8, "bold"),
                 bg=HEADER_BG, fg="#999999", width=3).grid(row=1, column=0, padx=1, pady=1)
        for i, h in enumerate(WEEKDAY_HEADERS):
            fg = WEEKEND_FG if i >= 5 else "#666666"
            tk.Label(frame, text=h, font=("Microsoft YaHei UI", 8, "bold"),
                     bg=HEADER_BG, fg=fg, width=3).grid(row=1, column=i + 1, padx=1, pady=1)

        cal = _calendar.Calendar(firstweekday=0)
        days = cal.monthdayscalendar(year, month)
        today_tuple = (self._today.year, self._today.month, self._today.day)

        for r, week in enumerate(days):
            wk = next((d for d in week if d != 0), None)
            wk_num = datetime(year, month, wk).isocalendar()[1] if wk else ""
            tk.Label(frame, text=str(wk_num), font=("Microsoft YaHei UI", 7),
                     bg=CARD_BG, fg="#aaaaaa", width=3).grid(row=r + 2, column=0, padx=1, pady=1)
            for c, day in enumerate(week):
                if day == 0:
                    txt, fg_val, bg_val = "", "#cccccc", CARD_BG
                elif (year, month, day) == today_tuple:
                    txt, fg_val, bg_val = str(day), TODAY_FG, TODAY_BG
                elif c >= 5:
                    txt, fg_val, bg_val = str(day), WEEKEND_FG, CARD_BG
                else:
                    txt, fg_val, bg_val = str(day), CARD_FG, CARD_BG
                lbl = tk.Label(frame, text=txt, font=("Consolas", 9),
                               bg=bg_val, fg=fg_val, width=3)
                lbl.grid(row=r + 2, column=c + 1, padx=1, pady=1)

        return frame


# ═══════════════════════════════════════════════════════════
#  城市选择对话框
# ═══════════════════════════════════════════════════════════

class CitySelectDialog:
    def __init__(self, parent, current, existing):
        self.result = None
        self.top = tk.Toplevel(parent)
        self.top.title("选择城市")
        self.top.configure(bg=WINDOW_BG)
        self.top.resizable(False, False)
        self.top.attributes("-topmost", True)

        tk.Label(self.top, text="选择替换的城市：",
                 font=("Microsoft YaHei UI", 11), bg=WINDOW_BG, fg=CARD_FG).pack(padx=24, pady=(16, 8))

        lb = tk.Listbox(self.top, font=("Microsoft YaHei UI", 11), width=16, height=12,
                        selectbackground=ACCENT, selectforeground="#ffffff",
                        bg=CARD_BG, fg=CARD_FG, relief="solid", bd=1)
        lb.pack(padx=24, pady=(0, 12))

        cities = sorted([c for c in ALL_CITIES if c not in existing])
        for c in cities:
            lb.insert("end", c)

        def on_select(event=None):
            sel = lb.curselection()
            if sel:
                self.result = lb.get(sel[0])
                self.top.destroy()

        lb.bind("<Double-Button-1>", on_select)

        btn_frame = tk.Frame(self.top, bg=WINDOW_BG)
        btn_frame.pack(pady=(0, 16))
        tk.Button(btn_frame, text="确定", command=on_select, width=8,
                  bg=ACCENT, fg="#ffffff", relief="flat", bd=0,
                  font=("Microsoft YaHei UI", 10),
                  activebackground=ACCENT_LIGHT, activeforeground="#ffffff").pack(side="left", padx=6)
        tk.Button(btn_frame, text="取消", command=self.top.destroy, width=8,
                  bg=CARD_BG, fg=CARD_FG, relief="solid", bd=1,
                  font=("Microsoft YaHei UI", 10)).pack(side="left", padx=6)

        x = parent.winfo_rootx() + 40
        y = parent.winfo_rooty() + 40
        self.top.geometry(f"+{x}+{y}")
        self.top.grab_set()


# ═══════════════════════════════════════════════════════════
#  主应用
# ═══════════════════════════════════════════════════════════

class WorldClockApp:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title(f"世界时钟 v{VERSION} · 2026")
        self.root.configure(bg=WINDOW_BG)
        self.root.geometry("1000x780")
        self.root.minsize(720, 540)
        self.root.attributes("-topmost", True)

        # ── 顶部栏 ──
        header = tk.Frame(self.root, bg=ACCENT, padx=24, pady=14)
        header.pack(fill="x")

        tk.Label(header, text=f"🌍 世界时钟 v{VERSION} · 2026",
                 font=("Microsoft YaHei UI", 16, "bold"),
                 bg=ACCENT, fg="#ffffff").pack(side="left")
        tk.Label(header, text="右键卡片管理城市 | 点击城市名修改",
                 font=("Microsoft YaHei UI", 9),
                 bg=ACCENT, fg="#bdc3c7").pack(side="right")

        # ── 无锡当天日期信息条 ──
        wuxi_bar = tk.Frame(self.root, bg="#ffffff", padx=20, pady=8,
                           highlightbackground=BORDER, highlightthickness=1)
        wuxi_bar.pack(fill="x", padx=0)
        today = datetime.now()
        tk.Label(wuxi_bar, text="🏠 无锡",
                 font=("Microsoft YaHei UI", 11, "bold"),
                 bg="#ffffff", fg=WUXI_GOLD).pack(side="left")
        tk.Label(wuxi_bar,
                 text=f"{today.year}年{today.month}月{today.day}日  {WEEKDAYS[today.weekday()]}  第{today.isocalendar()[1]}周  |  UTC+8 中国标准时间",
                 font=("Microsoft YaHei UI", 11),
                 bg="#ffffff", fg=CARD_FG).pack(side="left", padx=(10, 0))
        tk.Label(wuxi_bar, text="CST · Beijing Time",
                 font=("Consolas", 9),
                 bg="#ffffff", fg=MUTED).pack(side="right")

        # ── 标签页 ──
        style = ttk.Style()
        style.theme_use('clam')
        style.configure("TNotebook", background=WINDOW_BG, borderwidth=0)
        style.configure("TNotebook.Tab",
                        font=("Microsoft YaHei UI", 11, "bold"),
                        padding=[24, 10],
                        background="#e0e0e0",
                        foreground="#333333",
                        borderwidth=1,
                        relief="flat")
        style.map("TNotebook.Tab",
                  background=[("selected", ACCENT), ("active", "#d0d0d0")],
                  foreground=[("selected", "#ffffff"), ("active", "#222222")],
                  padding=[("selected", [24, 12])])
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill="both", expand=True, padx=12, pady=(8, 0))

        # 标签页 1：世界时钟
        self.clock_tab = tk.Frame(self.notebook, bg=WINDOW_BG)
        self.notebook.add(self.clock_tab, text="世界时钟")
        self.grid = tk.Frame(self.clock_tab, bg=WINDOW_BG)
        self.grid.pack(padx=4, pady=(8, 0), fill="both", expand=True)

        # 标签页 2：日历
        self.calendar_tab = CalendarTab(self.notebook)
        self.notebook.add(self.calendar_tab, text="2026年日历")

        # ── 底部栏 ──
        footer = tk.Frame(self.root, bg=WINDOW_BG)
        footer.pack(fill="x", padx=20, pady=(8, 12))
        tk.Label(footer, text="作者: wangqiang@wuxipake.com  |  Tel: 18018390039",
                 font=("Microsoft YaHei UI", 8), bg=WINDOW_BG, fg="#999999").pack(side="left")
        tk.Label(footer, text=f"v{VERSION}  |  By Trae CN + Claude Code + Deepseek V4",
                 font=("Microsoft YaHei UI", 8), bg=WINDOW_BG, fg="#999999").pack(side="right")

        self.cities = list(DEFAULT_CITIES)
        self.clocks = {}
        self._build_grid()

        self.root.mainloop()

    def _build_grid(self):
        for w in self.grid.winfo_children():
            w.destroy()
        self.clocks.clear()

        cols = 3 if len(self.cities) > 3 else len(self.cities)
        for c in range(cols):
            self.grid.grid_columnconfigure(c, weight=1)
        for i, city in enumerate(self.cities):
            row, col = divmod(i, cols)
            clock = CityClock(self.grid, city, self._on_card_right_click)
            clock.grid(row=row, column=col, padx=8, pady=8, sticky="nsew")
            self.clocks[city] = clock

    def _on_card_right_click(self, event, city):
        menu = tk.Menu(self.root, tearoff=0)
        menu.add_command(label=f"修改位置", command=lambda c=city: self._replace_city(c))
        menu.add_command(label=f"删除 {city}", command=lambda c=city: self._remove_city(c))
        menu.add_separator()
        add_menu = tk.Menu(menu, tearoff=0)
        for name in sorted(ALL_CITIES):
            if name not in self.cities:
                add_menu.add_command(label=name, command=lambda n=name: self._add_city(n))
        menu.add_cascade(label="添加城市", menu=add_menu)
        menu.add_command(label="恢复默认", command=self._reset_default)
        menu.post(event.x_root, event.y_root)

    def _replace_city(self, old_city):
        dialog = CitySelectDialog(self.root, old_city, self.cities)
        self.root.wait_window(dialog.top)
        if dialog.result and dialog.result != old_city:
            idx = self.cities.index(old_city)
            self.cities[idx] = dialog.result
            self._build_grid()

    def _remove_city(self, city):
        if len(self.cities) <= 1:
            messagebox.showwarning("提示", "至少保留一个城市。")
            return
        self.cities.remove(city)
        self._build_grid()

    def _add_city(self, city):
        self.cities.append(city)
        self._build_grid()

    def _reset_default(self):
        self.cities = list(DEFAULT_CITIES)
        self._build_grid()


if __name__ == "__main__":
    WorldClockApp()
