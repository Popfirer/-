import tkinter as tk
from tkinter import ttk, simpledialog, messagebox
from datetime import datetime, timedelta, timezone
import calendar as _calendar
import threading
import urllib.request
import json
import time as _time

WEEKDAYS = ["星期一", "星期二", "星期三", "星期四", "星期五", "星期六", "星期日"]

CARD_BG = "#ffffff"
CARD_FG = "#1a1a1a"
WINDOW_BG = "#f5f5f5"
BORDER_COLOR = "#222222"

# All supported cities with DST rules
# base: UTC offset, dst: DST rule, query: wttr.in query name, cc: country code for holidays
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


# --- weather / holiday cache ---
_weather_cache = {}     # city -> (text, timestamp)
_holiday_cache = {}     # cc -> (holiday_name_or_empty, date_str, timestamp)

WEATHER_TTL = 1800       # 30 minutes
HOLIDAY_TTL = 86400      # 24 hours


def _fetch_weather(city):
    info = ALL_CITIES.get(city)
    if info is None:
        return
    query = info.get("query", city)
    try:
        url = f"https://wttr.in/{query}?format=j1&lang=zh"
        req = urllib.request.Request(url, headers={"User-Agent": "WorldClock/1.0"})
        with urllib.request.urlopen(req, timeout=8) as resp:
            data = json.loads(resp.read())
            current = data["current_condition"][0]
            temp = current["temp_C"]
            desc = current["weatherDesc"][0]["value"]
            text = f"{temp}°C {desc}"
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
        req = urllib.request.Request(url, headers={"User-Agent": "WorldClock/1.0"})
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


class CityClock(tk.Frame):
    def __init__(self, parent, city, on_right_click):
        super().__init__(parent, bg=CARD_BG, highlightbackground=BORDER_COLOR,
                         highlightthickness=1, padx=18, pady=14)
        self.city = city

        self.name_label = tk.Label(self, text=city, font=("Microsoft YaHei UI", 13, "bold"),
                                   bg=CARD_BG, fg=CARD_FG)
        self.name_label.pack(anchor="w")
        self.time_label = tk.Label(self, text="", font=("Consolas", 26),
                                   bg=CARD_BG, fg=CARD_FG)
        self.time_label.pack(anchor="w", pady=(2, 2))
        self.weather_label = tk.Label(self, text="", font=("Microsoft YaHei UI", 9),
                                      bg=CARD_BG, fg="#444444")
        self.weather_label.pack(anchor="w")
        self.info_label = tk.Label(self, text="", font=("Microsoft YaHei UI", 10),
                                   bg=CARD_BG, fg="#666666")
        self.info_label.pack(anchor="w")
        self.holiday_label = tk.Label(self, text="", font=("Microsoft YaHei UI", 9, "bold"),
                                      bg=CARD_BG, fg="#d43030")
        self.holiday_label.pack(anchor="w")

        for w in (self, self.name_label, self.time_label, self.weather_label,
                  self.info_label, self.holiday_label):
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
        utc_now = datetime.now(timezone.utc)
        offset = get_utc_offset(self.city, utc_now)
        local_now = utc_now + timedelta(hours=offset)
        time_str = local_now.strftime("%H:%M:%S")
        date_str = f"{local_now.month}月{local_now.day}日"
        weekday_str = WEEKDAYS[local_now.weekday()]
        self.time_label.config(text=time_str)
        week_num = local_now.isocalendar()[1]
        self.info_label.config(text=f"{date_str}  {weekday_str}  第{week_num}周")

        # weather
        w = _get_weather(self.city)
        self.weather_label.config(text=w if w else "加载中...")

        # holiday
        info = ALL_CITIES.get(self.city)
        if info:
            h = _get_holiday(info.get("cc", ""))
            self.holiday_label.config(text=f"🎉 {h}" if h else "")

        # refresh weather/holiday in background periodically
        self._tick_count += 1
        if self._tick_count % 900 == 0:  # ~ every 3 min (200ms * 900)
            self._refresh_weather()

        self.after(200, self.update)


# --- 2026 年日历 ---
WEEKDAY_HEADERS = ["一", "二", "三", "四", "五", "六", "日"]
MONTH_NAMES = ["1月", "2月", "3月", "4月", "5月", "6月",
               "7月", "8月", "9月", "10月", "11月", "12月"]
HEADER_BG = "#e8e8e8"
TODAY_BG = "#222222"
TODAY_FG = "#ffffff"
WEEKEND_FG = "#c0392b"


class CalendarTab(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent, bg=WINDOW_BG)
        self._build()

    def _build(self):
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
        frame = tk.Frame(parent, bg=CARD_BG, highlightbackground="#dddddd",
                         highlightthickness=1, padx=10, pady=8)

        tk.Label(frame, text=MONTH_NAMES[month - 1],
                 font=("Microsoft YaHei UI", 12, "bold"),
                 bg=CARD_BG, fg=CARD_FG).grid(row=0, column=0, columnspan=8, pady=(0, 4))

        tk.Label(frame, text="周", font=("Microsoft YaHei UI", 8, "bold"),
                 bg=HEADER_BG, fg="#999999", width=3).grid(row=1, column=0, padx=1, pady=1)
        for i, h in enumerate(WEEKDAY_HEADERS):
            fg = WEEKEND_FG if i >= 5 else "#666666"
            tk.Label(frame, text=h, font=("Microsoft YaHei UI", 8, "bold"),
                     bg=HEADER_BG, fg=fg, width=3).grid(row=1, column=i + 1, padx=1, pady=1)

        cal = _calendar.Calendar(firstweekday=0)
        days = cal.monthdayscalendar(year, month)
        today = datetime.now()
        today_tuple = (today.year, today.month, today.day)

        for r, week in enumerate(days):
            # week number
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


class WorldClockApp:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("世界时钟 · 2026")
        self.root.configure(bg=WINDOW_BG)
        self.root.geometry("960x720")
        self.root.minsize(640, 480)
        self.root.attributes("-topmost", True)

        # --- header ---
        header = tk.Frame(self.root, bg=WINDOW_BG)
        header.pack(fill="x", padx=20, pady=(16, 4))

        tk.Label(header, text="世界时钟 · 2026",
                 font=("Microsoft YaHei UI", 14, "bold"),
                 bg=WINDOW_BG, fg=BORDER_COLOR).pack(side="left")
        tk.Label(header, text="右键卡片 | 点击城市名修改",
                 font=("Microsoft YaHei UI", 9),
                 bg=WINDOW_BG, fg="#aaaaaa").pack(side="right")

        # --- notebook ---
        style = ttk.Style()
        style.configure("TNotebook", background=WINDOW_BG, borderwidth=0)
        style.configure("TNotebook.Tab", font=("Microsoft YaHei UI", 10),
                        padding=[18, 6])
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill="both", expand=True, padx=20, pady=(6, 0))

        # tab 1: world clock
        self.clock_tab = tk.Frame(self.notebook, bg=WINDOW_BG)
        self.notebook.add(self.clock_tab, text="世界时钟")
        self.grid = tk.Frame(self.clock_tab, bg=WINDOW_BG)
        self.grid.pack(padx=0, pady=(6, 0))

        # tab 2: calendar
        self.calendar_tab = CalendarTab(self.notebook)
        self.notebook.add(self.calendar_tab, text="2026年日历")

        # --- footer ---
        footer = tk.Frame(self.root, bg=WINDOW_BG)
        footer.pack(fill="x", padx=20, pady=(8, 12))
        tk.Label(footer, text="作者: wangqiang@wuxipake.com  |  Tel: 18018390039",
                 font=("Microsoft YaHei UI", 8), bg=WINDOW_BG, fg="#999999").pack(side="left")
        tk.Label(footer, text="By Trae CN + Claude Code + Deepseek V4",
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
                        selectbackground="#222222", selectforeground="#ffffff",
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
                  bg=CARD_BG, fg=CARD_FG, relief="solid", bd=1).pack(side="left", padx=6)
        tk.Button(btn_frame, text="取消", command=self.top.destroy, width=8,
                  bg=CARD_BG, fg=CARD_FG, relief="solid", bd=1).pack(side="left", padx=6)

        x = parent.winfo_rootx() + 40
        y = parent.winfo_rooty() + 40
        self.top.geometry(f"+{x}+{y}")
        self.top.grab_set()


if __name__ == "__main__":
    WorldClockApp()
