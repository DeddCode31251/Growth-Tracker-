#!/usr/bin/env python3
"""
Growth Tracker — Daily / Weekly / Monthly / Study Techniques / Settings
-------------------------------------------------------------------------
One tkinter app that:
  - Generates your daily schedule automatically from the weekday
  - Tracks Weekly progress (per-day % complete, per-category totals)
  - Tracks Monthly progress (calendar heatmap + streaks)
  - Teaches & times study techniques (Pomodoro + technique library)
  - Lets you customize the rotation subjects, off-day, and sleep goal

Standard library only. Run with:  python growth_tracker.py
Data saved next to this script in todo_data.json / settings.json
"""

import json
import os
import calendar
import datetime
import subprocess
import threading
import shutil
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog, filedialog

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_FILE = os.path.join(BASE_DIR, "todo_data.json")
SETTINGS_FILE = os.path.join(BASE_DIR, "settings.json")
PROJECTS_FILE = os.path.join(BASE_DIR, "projects.json")


# CONSTANTS

CATEGORY_COLORS = {
    "School": "#3b82f6", "Study": "#2563eb", "Football": "#22c55e",
    "Web Dev": "#a855f7", "Bug Bounty": "#ef4444", "Python": "#14b8a6",
    "C": "#0d9488", "Electronics": "#f59e0b", "Math": "#eab308",
    "Chess": "#6b7280", "Brain Games": "#ec4899", "Reading": "#92400e",
    "Business": "#f43f5e", "Rest": "#9ca3af", "Custom": "#0ea5e9",
    "Youtube": "#d65780","Body Training": "#0ea5e9","Praying":"#c6e0ff" ,
    "Reading Bible":"#d6a2ad"
}

# Categories that count as trackable "habits" for streaks / weekly totals
HABIT_CATEGORIES = ["Reading Bible","Praying","Body Training","Study", "Football", "Web Dev", "Bug Bounty", "Python",
                     "C", "Electronics", "Math", "Business", "Chess", "Brain Games", "Reading"]

# datetime.weekday(): Monday=0 ... Sunday=6. Saturday=5, Sunday=6.
WEEK_ORDER = [5, 6, 0, 1, 2, 3, 4]  # displayed Sat -> Fri
WEEKDAY_LABELS = {5: "Sat", 6: "Sun", 0: "Mon", 1: "Tue", 2: "Wed", 3: "Thu", 4: "Fri"}

DEFAULT_SETTINGS = {
    "rotation": ["Python", "C", "Electronics", "Math", "Business","Youtube"],
    "off_day_index": 4,       # Friday
    "sleep_goal_hours": 7,
    "pomodoro_work_min": 25,
    "pomodoro_break_min": 5,
    "download_dir": "downloads",
}

MOTIVATION = [
    # --- Aristotle ---
    ("We are what we repeatedly do. Excellence, then, is not an act, but a habit.", "Aristotle"),
    ("The energy of the mind is the essence of life.", "Aristotle"),
    ("It is the mark of an educated mind to entertain a thought without accepting it.", "Aristotle"),
    ("Knowing yourself is the beginning of all wisdom.", "Aristotle"),
    ("Educating the mind without educating the heart is no education at all.", "Aristotle"),
    ("Pleasure in the job puts perfection in the work.", "Aristotle"),
    ("Patience is bitter, but its fruit is sweet.", "Aristotle"),
    # --- Alexander the Great ---
    ("There is nothing impossible to him who will try.", "Alexander the Great"),
    ("I am not afraid of an army of lions led by a sheep; I am afraid of an army of sheep led by a lion.", "Alexander the Great"),
    ("Through every generation of the human race there has been a constant war, a war with fear.", "Alexander the Great"),
    ("Upon my death, place my hands outside my coffin, so the world can see they are empty.", "Alexander the Great"),
    ("My father will leave me nothing to conquer.", "Alexander the Great"),
    ("Remember that upon the conduct of each depends the fate of all.", "Alexander the Great"),
    # --- Marcus Aurelius ---
    ("You have power over your mind, not outside events. Realize this, and you will find strength.", "Marcus Aurelius"),
    ("Waste no more time arguing about what a good man should be. Be one.", "Marcus Aurelius"),
    ("The impediment to action advances action. What stands in the way becomes the way.", "Marcus Aurelius"),
    ("If it is not right, do not do it; if it is not true, do not say it.", "Marcus Aurelius"),
    ("The best revenge is to be unlike him who performed the injury.", "Marcus Aurelius"),
    ("Confine yourself to the present.", "Marcus Aurelius"),
    ("Very little is needed to make a happy life; it is all within yourself, in your way of thinking.", "Marcus Aurelius"),
    # --- Seneca ---
    ("Luck is what happens when preparation meets opportunity.", "Seneca"),
    ("It is not that we have a short time to live, but that we waste a lot of it.", "Seneca"),
    ("Difficulties strengthen the mind, as labor does the body.", "Seneca"),
    ("He who is brave is free.", "Seneca"),
    ("Every new beginning comes from some other beginning's end.", "Seneca"),
    ("We suffer more often in imagination than in reality.", "Seneca"),
    # --- Sun Tzu ---
    ("Victorious warriors win first and then go to war, while defeated warriors go to war first and then seek to win.", "Sun Tzu"),
    ("In the midst of chaos, there is also opportunity.", "Sun Tzu"),
    ("Opportunities multiply as they are seized.", "Sun Tzu"),
    ("The supreme art of war is to subdue the enemy without fighting.", "Sun Tzu"),
    ("Know yourself and you will win all battles.", "Sun Tzu"),
    ("Let your plans be dark and impenetrable as night.", "Sun Tzu"),
    # --- Napoleon Bonaparte ---
    ("Impossible is a word to be found only in the dictionary of fools.", "Napoleon Bonaparte"),
    ("A leader is a dealer in hope.", "Napoleon Bonaparte"),
    ("Victory belongs to the most persevering.", "Napoleon Bonaparte"),
    ("Ability is nothing without opportunity.", "Napoleon Bonaparte"),
    ("The battlefield is a scene of constant chaos. The winner will be the one who controls that chaos.", "Napoleon Bonaparte"),
    ("Take time to deliberate, but when the time for action arrives, stop thinking and go in.", "Napoleon Bonaparte"),
    # --- Julius Caesar ---
    ("Experience is the teacher of all things.", "Julius Caesar"),
    ("It is easier to find men who will volunteer to die than to find those who are willing to endure pain with patience.", "Julius Caesar"),
    ("As a rule, men worry more about what they can't see than about what they can.", "Julius Caesar"),
    ("I came, I saw, I conquered.", "Julius Caesar"),
    # --- Friedrich Nietzsche ---
    ("He who has a why to live can bear almost any how.", "Friedrich Nietzsche"),
    ("That which does not kill us makes us stronger.", "Friedrich Nietzsche"),
    ("You have your way. I have my way. As for the right way, it does not exist.", "Friedrich Nietzsche"),
    ("Without music, life would be a mistake.", "Friedrich Nietzsche"),
    ("The higher we soar, the smaller we appear to those who cannot fly.", "Friedrich Nietzsche"),
    # --- Winston Churchill ---
    ("Success is not final, failure is not fatal: it is the courage to continue that counts.", "Winston Churchill"),
    ("If you're going through hell, keep going.", "Winston Churchill"),
    ("We make a living by what we get, but we make a life by what we give.", "Winston Churchill"),
    ("Attitude is a little thing that makes a big difference.", "Winston Churchill"),
    ("Never let a good crisis go to waste.", "Winston Churchill"),
    ("Continuous effort, not strength or intelligence, is the key to unlocking our potential.", "Winston Churchill"),
    # --- Theodore Roosevelt ---
    ("Believe you can and you're halfway there.", "Theodore Roosevelt"),
    ("It is hard to fail, but it is worse never to have tried to succeed.", "Theodore Roosevelt"),
    ("Do what you can, with what you have, where you are.", "Theodore Roosevelt"),
    ("Nothing in the world is worth having or worth doing unless it means effort, pain, difficulty.", "Theodore Roosevelt"),
    ("Far and away the best prize that life offers is the chance to work hard at work worth doing.", "Theodore Roosevelt"),
    # --- Confucius ---
    ("It does not matter how slowly you go as long as you do not stop.", "Confucius"),
    ("Our greatest glory is not in never falling, but in rising every time we fall.", "Confucius"),
    ("The man who moves a mountain begins by carrying away small stones.", "Confucius"),
    ("Real knowledge is to know the extent of one's ignorance.", "Confucius"),
    ("Success depends upon previous preparation, and without such preparation there is sure to be failure.", "Confucius"),
    ("He who conquers himself is the mightiest warrior.", "Confucius"),
    # --- Miyamoto Musashi ---
    ("Today is victory over yourself of yesterday.", "Miyamoto Musashi"),
    ("You must understand that there is more than one path to the top of the mountain.", "Miyamoto Musashi"),
    ("Perceive that which cannot be seen with the eye.", "Miyamoto Musashi"),
    ("Do nothing which is of no use.", "Miyamoto Musashi"),
    ("From one thing, know ten thousand things.", "Miyamoto Musashi"),
    # --- Bruce Lee ---
    ("I fear not the man who has practiced 10,000 kicks once, but the man who has practiced one kick 10,000 times.", "Bruce Lee"),
    ("A goal is not always meant to be reached, it often serves simply as something to aim at.", "Bruce Lee"),
    ("As you think, so shall you become.", "Bruce Lee"),
    ("Do not pray for an easy life, pray for the strength to endure a difficult one.", "Bruce Lee"),
    ("Absorb what is useful, discard what is not, add what is uniquely your own.", "Bruce Lee"),
    ("Defeat is a state of mind; no one is ever defeated until defeat has been accepted as a reality.", "Bruce Lee"),
    ("The successful warrior is the average man, with laser-like focus.", "Bruce Lee"),
    # --- Muhammad Ali ---
    ("I hated every minute of training, but I said, don't quit, suffer now and live the rest of your life as a champion.", "Muhammad Ali"),
    ("Champions aren't made in gyms. Champions are made from something deep inside them, a desire, a dream, a vision.", "Muhammad Ali"),
    ("It's the repetition of affirmations that leads to belief.", "Muhammad Ali"),
    ("He who is not courageous enough to take risks will accomplish nothing in life.", "Muhammad Ali"),
    ("Don't count the days, make the days count.", "Muhammad Ali"),
    ("Impossible is not a fact. It's an opinion.", "Muhammad Ali"),
    # --- Leonardo da Vinci ---
    ("It had long since come to my attention that people of accomplishment rarely sat back and let things happen to them.", "Leonardo da Vinci"),
    ("Iron rusts from disuse; water loses its purity from stagnation; even so does inaction sap the vigor of the mind.", "Leonardo da Vinci"),
    ("Learning never exhausts the mind.", "Leonardo da Vinci"),
    ("Simplicity is the ultimate sophistication.", "Leonardo da Vinci"),
    ("Obstacles cannot crush me; every obstacle yields to stern resolve.", "Leonardo da Vinci"),
    # --- Socrates ---
    ("The secret of change is to focus all of your energy not on fighting the old, but on building the new.", "Socrates"),
    ("The unexamined life is not worth living.", "Socrates"),
    ("I cannot teach anybody anything. I can only make them think.", "Socrates"),
    ("Wisdom begins in wonder.", "Socrates"),
    # --- Plato ---
    ("The first and best victory is to conquer self.", "Plato"),
    ("At the touch of love everyone becomes a poet.", "Plato"),
    ("Courage is knowing what not to fear.", "Plato"),
    # --- Genghis Khan ---
    ("Conquering the world on horseback is easy; it is dismounting and governing that is hard.", "Genghis Khan"),
    ("An action committed in anger is an action doomed to failure.", "Genghis Khan"),
    ("If you are afraid, don't do it. If you're doing it, don't be afraid.", "Genghis Khan"),
    ("A leader can never be brave enough to think of nothing but the good of his people.", "Genghis Khan"),
    # --- Epictetus ---
    ("It's not what happens to you, but how you react to it that matters.", "Epictetus"),
    ("No man is free who is not master of himself.", "Epictetus"),
    ("First say to yourself what you would be; and then do what you have to do.", "Epictetus"),
    ("Wealth consists not in having great possessions, but in having few wants.", "Epictetus"),
    ("Circumstances don't make the man, they only reveal him to himself.", "Epictetus"),
    # --- Lao Tzu ---
    ("A journey of a thousand miles begins with a single step.", "Lao Tzu"),
    ("Mastering others is strength. Mastering yourself is true power.", "Lao Tzu"),
    ("Nature does not hurry, yet everything is accomplished.", "Lao Tzu"),
    ("The wise man does not lay up his own treasures.", "Lao Tzu"),
    ("New beginnings are often disguised as painful endings.", "Lao Tzu"),
    # --- Cicero ---
    ("A room without books is like a body without a soul.", "Cicero"),
    ("While there's life, there's hope.", "Cicero"),
    ("The pursuit of truth and beauty is a sphere of activity in which we are permitted to remain children all our lives.", "Cicero"),
    # --- Michael Jordan ---
    ("I've failed over and over again in my life. And that is why I succeed.", "Michael Jordan"),
    ("Some people want it to happen, some wish it would happen, others make it happen.", "Michael Jordan"),
    ("Limits, like fears, are often just an illusion.", "Michael Jordan"),
    ("Talent wins games, but teamwork and intelligence win championships.", "Michael Jordan"),
    ("You must expect great things of yourself before you can do them.", "Michael Jordan"),
    # --- Kobe Bryant ---
    ("The most important thing is to try and inspire people so that they can be great in whatever they want to do.", "Kobe Bryant"),
    ("Great things come from hard work and perseverance. No excuses.", "Kobe Bryant"),
    ("I can't relate to lazy people. We don't speak the same language.", "Kobe Bryant"),
    ("Rest at the end, not in the middle.", "Kobe Bryant"),
    # --- Nikola Tesla ---
    ("The present is theirs; the future, for which I really worked, is mine.", "Nikola Tesla"),
    ("My brain is only a receiver; in the Universe there is a core from which we obtain knowledge.", "Nikola Tesla"),
    ("Let the future tell the truth and evaluate each one according to his work.", "Nikola Tesla"),
    # --- Steve Jobs ---
    ("Your time is limited, so don't waste it living someone else's life.", "Steve Jobs"),
    ("Stay hungry, stay foolish.", "Steve Jobs"),
    ("The only way to do great work is to love what you do.", "Steve Jobs"),
    ("Innovation distinguishes between a leader and a follower.", "Steve Jobs"),
]

STUDY_TECHNIQUES = [
    {
        "name": "Active Recall",
        "best_for": "Web Dev, Bug Bounty, Math, School",
        "what": "Instead of re-reading notes, close them and force yourself to "
                "retrieve the answer from memory — write it, say it, or code it "
                "without looking.",
        "how": "After learning something, cover the material and try to explain "
               "or rebuild it from scratch. Check your gaps, then repeat.",
    },
    {
        "name": "Build-Measure-Learn",
        "best_for": "Business, side projects",
        "what": "The lean-startup loop: turn an idea into the smallest testable "
                "version, put it in front of real people, and let their reaction "
                "tell you what to change — instead of planning in your head for months.",
        "how": "Write your idea in one sentence, build the smallest version in "
               "days (not months), show 5 real people, note what they actually "
               "do (not just what they say), adjust, repeat.",
    },
    {
        "name": "The 20% Rule (Learn-to-Build Ratio)",
        "best_for": "Web Dev, Bug Bounty, Python, C, Electronics",
        "what": "Once you can follow a tutorial without getting lost, you've "
                "hit diminishing returns on watching more. Flip the ratio: "
                "~20% learning new material, ~80% building with it.",
        "how": "See the Projects tab for the concrete signals that tell you "
               "it's time to stop consuming courses and start shipping.",
    },
    {
        "name": "Spaced Repetition",
        "best_for": "Python, C, Math, School, vocab/definitions",
        "what": "Review material at increasing intervals (1 day, 3 days, 7 days, "
                "14 days...) right before you'd naturally forget it.",
        "how": "Keep a simple list of concepts you learned. Revisit each one on "
               "day 1, day 3, day 7. Tools like flashcards work well for this.",
    },
    {
        "name": "Pomodoro Technique",
        "best_for": "Any deep-focus block (coding, bug bounty, studying)",
        "what": "Work in focused sprints (usually 25 min) followed by a short "
                "break, to keep attention sharp and avoid burnout.",
        "how": "Use the Pomodoro timer in this tab. One sprint = one 'session'. "
               "Take a real break away from the screen when it rings.",
    },
    {
        "name": "Feynman Technique",
        "best_for": "Math, School, Electronics/PCB concepts",
        "what": "Explain a concept in the simplest possible words, as if "
                "teaching a beginner. Gaps in your explanation reveal gaps "
                "in your understanding.",
        "how": "Pick a topic, write a plain-language explanation, find where "
               "you got stuck or vague, go back to the source, simplify again.",
    },
    {
        "name": "Interleaving",
        "best_for": "Math, School, Chess",
        "what": "Mix different topics or problem types in one session instead "
                "of drilling one type repeatedly — it builds real pattern "
                "recognition instead of rote memory.",
        "how": "In a school-study block, rotate between 2-3 subjects or "
               "problem types every 15-20 minutes instead of doing one only.",
    },
    {
        "name": "SQ3R (for reading)",
        "best_for": "Reading books, textbooks",
        "what": "Survey, Question, Read, Recite, Review — a structured way to "
                "read that boosts retention far above passive reading.",
        "how": "Skim first (Survey), turn headings into questions, read for "
               "answers, recite key points aloud from memory, then review.",
    },
    {
        "name": "Deliberate Practice",
        "best_for": "Chess, Bug Bounty, Electronics/PCB",
        "what": "Practice at the edge of your ability on a specific weakness, "
               "with immediate feedback — not just repeating what's already easy.",
        "how": "Pick one weak skill (e.g. a chess opening you keep losing, or "
               "one vuln class). Drill only that, check results, adjust.",
    },
    {
        "name": "Mind Mapping",
        "best_for": "Electronics, School, Web Dev architecture",
        "what": "Visually branch out ideas from a central concept to see how "
               "pieces connect — great for systems and architecture thinking.",
        "how": "Write the core topic in the center of a page, branch out "
               "sub-topics and how they relate. Use it to plan projects too.",
    },
]


# JSON HELPERS

def load_json(path, default):
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError):
            return default
    return default


def save_json(path, obj):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, indent=2, ensure_ascii=False)



# TEMPLATE BUILDER (depends on live settings so it's editable)

def rotating_subject_for(weekday_index, settings):
    rot = settings.get("rotation") or DEFAULT_SETTINGS["rotation"]
    return rot[weekday_index % len(rot)]


def build_template(weekday_index, settings):
    subject = rotating_subject_for(weekday_index, settings)
    off_day = settings.get("off_day_index", DEFAULT_SETTINGS["off_day_index"])

    if weekday_index == off_day:
        return [
            ("09:00-11:00", "Deep Work: Bug Bounty (extended)", "Bug Bounty", 120),
            ("11:00-12:00", "Web Dev project time", "Web Dev", 60),
            ("12:00-13:00", "Free time / family", "Rest", 60),
            ("13:00-15:00", "School study catch-up", "Study", 120),
            ("15:00-16:00", f"Deep focus: {subject} (extended)", subject, 60),
            ("16:00-17:00", "Electronics / PCB hands-on project", "Electronics", 60),
            ("17:00-17:30", "Chess practice", "Chess", 30),
            ("17:30-18:00", "Brain games", "Brain Games", 30),
            ("18:00-18:30", "Reading", "Reading", 30),
        ]

    return [
        ("05:00-05:10", "Praying", "Praying", 0),
        ("05:10-05:20", "Reading Bible", "Reading Bible", 0),
        ("05:20-05:40", "Body Training", "Body Training", 0),
        ("06:00-15:00", "School", "School", 0),
        ("15:00-15:30", "Lunch / rest", "Rest", 30),
        ("15:30-17:30", "School study (2h)", "Study", 120),
        ("17:30-17:45", "Break", "Rest", 15),
        ("17:45-18:45", "Football", "Football", 60),
        ("18:45-19:15", "Dinner / shower", "Rest", 30),
        ("19:15-20:15", "Web Dev", "Web Dev", 60),
        ("20:15-21:15", "Bug Bounty", "Bug Bounty", 60),
        ("21:15-22:00", f"Deep focus: {subject}", subject, 45),
        ("22:00-22:15", "Chess", "Chess", 15),
        ("22:15-22:30", "Brain games", "Brain Games", 15),
        ("22:30-22:50", "Reading", "Reading", 20),
        ("22:50-23:00", "Plan tomorrow / wind down", "Rest", 10),
    ]



# STORE — central data access

class Store:
    def __init__(self):
        self.data = load_json(DATA_FILE, {})
        self.settings = load_json(SETTINGS_FILE, json.loads(json.dumps(DEFAULT_SETTINGS)))
        self.settings.setdefault("download_dir", "downloads")
        self.projects = load_json(PROJECTS_FILE, [])

    def save_data(self):
        save_json(DATA_FILE, self.data)

    def save_settings(self):
        save_json(SETTINGS_FILE, self.settings)

    def save_projects(self):
        save_json(PROJECTS_FILE, self.projects)

    def add_project(self, name, category, status, notes):
        self.projects.append({
            "id": int(datetime.datetime.now().timestamp() * 1000),
            "name": name, "category": category, "status": status,
            "notes": notes, "created": datetime.date.today().isoformat(),
        })
        self.save_projects()

    def update_project(self, project_id, **fields):
        for p in self.projects:
            if p["id"] == project_id:
                p.update(fields)
                break
        self.save_projects()

    def delete_project(self, project_id):
        self.projects = [p for p in self.projects if p["id"] != project_id]
        self.save_projects()

    def get_or_create_day(self, date_str, weekday_index):
        if date_str not in self.data:
            template = build_template(weekday_index, self.settings)
            self.data[date_str] = {
                "tasks": [
                    {"time": t, "name": n, "category": c, "minutes": m,
                     "done": False, "custom": False}
                    for (t, n, c, m) in template
                ],
                "focus_sessions": 0,
                "notes": "",
            }
            self.save_data()
        self.data[date_str].setdefault("focus_sessions", 0)
        self.data[date_str].setdefault("notes", "")
        return self.data[date_str]

    def day_stats(self, date_str):
        """Return (done, total, pct) without creating the day."""
        day = self.data.get(date_str)
        if not day:
            return 0, 0, 0
        tasks = day["tasks"]
        total = len(tasks)
        done = sum(1 for t in tasks if t["done"])
        pct = int(done / total * 100) if total else 0
        return done, total, pct

    def category_minutes(self, date_str, category):
        day = self.data.get(date_str)
        if not day:
            return 0, 0
        done_min = sum(t["minutes"] for t in day["tasks"] if t["category"] == category and t["done"])
        total_min = sum(t["minutes"] for t in day["tasks"] if t["category"] == category)
        return done_min, total_min

    def category_scheduled(self, date_str, weekday_index, category):
        """Is this category scheduled on this date? Uses real data if present,
        otherwise falls back to what the template would generate."""
        day = self.data.get(date_str)
        if day:
            return any(t["category"] == category for t in day["tasks"])
        template = build_template(weekday_index, self.settings)
        return any(c == category for (_, _, c, _) in template)

    def category_completed(self, date_str, weekday_index, category):
        """True/False/None(not scheduled that day)."""
        if not self.category_scheduled(date_str, weekday_index, category):
            return None
        day = self.data.get(date_str)
        if not day:
            return False
        matching = [t for t in day["tasks"] if t["category"] == category]
        return any(t["done"] for t in matching)

    def current_streak(self, category):
        streak = 0
        d = datetime.date.today()
        for _ in range(730):  # cap search at 2 years back
            status = self.category_completed(d.isoformat(), d.weekday(), category)
            if status is None:
                d -= datetime.timedelta(days=1)
                continue
            if status:
                streak += 1
                d -= datetime.timedelta(days=1)
            else:
                break
        return streak

    def best_streak(self, category, lookback_days=365):
        today = datetime.date.today()
        dates = [today - datetime.timedelta(days=i) for i in range(lookback_days)]
        dates.reverse()
        best = cur = 0
        for d in dates:
            status = self.category_completed(d.isoformat(), d.weekday(), category)
            if status is None:
                continue
            if status:
                cur += 1
                best = max(best, cur)
            else:
                cur = 0
        return best



# DAILY TAB

class DailyTab(tk.Frame):
    def __init__(self, master, store: Store):
        super().__init__(master, bg="#0f172a")
        self.store = store
        self.today = datetime.date.today()
        self.date_str = self.today.isoformat()
        self.weekday_index = self.today.weekday()
        self.day = self.store.get_or_create_day(self.date_str, self.weekday_index)
        self.tasks = self.day["tasks"]
        self.label_widgets = {}

        self._build_header()
        self._build_progress()
        self._build_task_area()
        self._build_notes()
        self._build_footer()
        self.refresh()

    def _build_header(self):
        header = tk.Frame(self, bg="#0f172a")
        header.pack(fill="x", padx=20, pady=(16, 4))
        tk.Label(header, text=f"{self.today.strftime('%A')}, {self.today.strftime('%d %B %Y')}",
                  font=("Segoe UI", 16, "bold"), bg="#0f172a", fg="white").pack(anchor="w")
        self._build_quote_card(header)

    def _build_quote_card(self, parent):
        import random
        card = tk.Frame(parent, bg="#1e293b")
        card.pack(fill="x", pady=(10, 0))

        accent = tk.Frame(card, bg="#eab308", width=5)
        accent.pack(side="left", fill="y")

        inner = tk.Frame(card, bg="#1e293b")
        inner.pack(side="left", fill="both", expand=True, padx=(4, 0))

        top_row = tk.Frame(inner, bg="#1e293b")
        top_row.pack(fill="x", padx=14, pady=(10, 0))
        tk.Label(top_row, text="\u201C", font=("Georgia", 26, "bold"),
                  bg="#1e293b", fg="#eab308").pack(side="left", anchor="n")

        text_col = tk.Frame(top_row, bg="#1e293b")
        text_col.pack(side="left", fill="both", expand=True, padx=(6, 0))

        self.quote_label = tk.Label(text_col, text="", font=("Segoe UI", 11, "italic"),
                                      bg="#1e293b", fg="#e2e8f0", wraplength=470,
                                      justify="left", anchor="w")
        self.quote_label.pack(fill="x", anchor="w")

        self.author_label = tk.Label(inner, text="", font=("Segoe UI", 10, "bold"),
                                       bg="#1e293b", fg="#eab308", anchor="e")
        self.author_label.pack(fill="x", padx=14, pady=(4, 4), anchor="e")

        refresh_btn = tk.Button(inner, text="\u21bb New quote", command=self.new_quote,
                                  bg="#334155", fg="white", activebackground="#475569",
                                  relief="flat", font=("Segoe UI", 8, "bold"),
                                  padx=8, pady=3, bd=0, cursor="hand2")
        refresh_btn.pack(anchor="e", padx=14, pady=(0, 10))

        self._random = random
        self.new_quote()

    def new_quote(self):
        quote, author = self._random.choice(MOTIVATION)
        self.quote_label.config(text=f"\u201C{quote}\u201D")
        self.author_label.config(text=f"\u2014 {author}")

    def _build_progress(self):
        frame = tk.Frame(self, bg="#0f172a")
        frame.pack(fill="x", padx=20, pady=(6, 4))
        self.progress_label = tk.Label(frame, text="", font=("Segoe UI", 10, "bold"),
                                        bg="#0f172a", fg="#22c55e")
        self.progress_label.pack(anchor="w")
        style = ttk.Style(self)
        style.theme_use("clam")
        style.configure("green.Horizontal.TProgressbar", troughcolor="#1e293b",
                          background="#22c55e", thickness=12)
        self.progress_bar = ttk.Progressbar(frame, style="green.Horizontal.TProgressbar",
                                             orient="horizontal", mode="determinate", maximum=100)
        self.progress_bar.pack(fill="x", pady=(4, 0))

    def _build_task_area(self):
        container = tk.Frame(self, bg="#0f172a")
        container.pack(fill="both", expand=True, padx=20, pady=6)
        canvas = tk.Canvas(container, bg="#0f172a", highlightthickness=0, height=340)
        scrollbar = ttk.Scrollbar(container, orient="vertical", command=canvas.yview)
        self.task_list_frame = tk.Frame(canvas, bg="#0f172a")
        self.task_list_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=self.task_list_frame, anchor="nw", width=560)
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        def _wheel(e):
            canvas.yview_scroll(int(-1 * (e.delta / 120)), "units")
        canvas.bind_all("<MouseWheel>", _wheel)

    def _build_notes(self):
        frame = tk.Frame(self, bg="#0f172a")
        frame.pack(fill="x", padx=20, pady=(4, 4))
        tk.Label(frame, text="Notes / reflection for today:", font=("Segoe UI", 9),
                  bg="#0f172a", fg="#94a3b8").pack(anchor="w")
        self.notes_text = tk.Text(frame, height=2, bg="#1e293b", fg="white",
                                    insertbackground="white", relief="flat", font=("Segoe UI", 10))
        self.notes_text.insert("1.0", self.day.get("notes", ""))
        self.notes_text.pack(fill="x", pady=(2, 0))
        self.notes_text.bind("<FocusOut>", self.save_notes)

    def save_notes(self, event=None):
        self.day["notes"] = self.notes_text.get("1.0", "end").strip()
        self.store.save_data()

    def _build_footer(self):
        footer = tk.Frame(self, bg="#0f172a")
        footer.pack(fill="x", padx=20, pady=(4, 14))
        tk.Button(footer, text="+ Add custom task", command=self.add_task, bg="#1e293b", fg="white",
                   relief="flat", font=("Segoe UI", 10, "bold"), padx=10, pady=6).pack(side="left")
        tk.Button(footer, text="Reset today's checks", command=self.reset_today, bg="#1e293b",
                   fg="#f87171", relief="flat", font=("Segoe UI", 10), padx=10, pady=6).pack(side="left", padx=(10, 0))

    def refresh(self):
        for w in self.task_list_frame.winfo_children():
            w.destroy()
        for idx, task in enumerate(self.tasks):
            self._render_row(idx, task)
        done, total, pct = self.store.day_stats(self.date_str)
        self.progress_bar["value"] = pct
        self.progress_label.config(text=f"Today's progress: {done}/{total} tasks  ({pct}%)")

    def _render_row(self, idx, task):
        color = CATEGORY_COLORS.get(task["category"], "#0ea5e9")
        row = tk.Frame(self.task_list_frame, bg="#1e293b")
        row.pack(fill="x", pady=4, padx=2)
        tk.Frame(row, bg=color, width=6).pack(side="left", fill="y")
        var = tk.BooleanVar(value=task["done"])

        def toggle(i=idx, v=var):
            self.tasks[i]["done"] = v.get()
            self.store.save_data()
            self.refresh()

        tk.Checkbutton(row, variable=var, command=toggle, bg="#1e293b", activebackground="#1e293b",
                        selectcolor="#0f172a", relief="flat").pack(side="left", padx=(8, 4), pady=8)
        text_frame = tk.Frame(row, bg="#1e293b")
        text_frame.pack(side="left", fill="both", expand=True, pady=6)
        tk.Label(text_frame, text=task["name"], font=("Segoe UI", 11, "bold"), bg="#1e293b",
                  fg="#64748b" if task["done"] else "white", anchor="w").pack(anchor="w")
        tk.Label(text_frame, text=f"{task['time']}  ·  {task['category']}", font=("Segoe UI", 9),
                  bg="#1e293b", fg="#94a3b8", anchor="w").pack(anchor="w")
        if task.get("custom"):
            tk.Button(row, text="✕", command=lambda i=idx: self.delete_task(i), bg="#1e293b",
                       fg="#f87171", relief="flat", font=("Segoe UI", 10, "bold"), bd=0).pack(side="right", padx=8)

    def add_task(self):
        name = simpledialog.askstring("New task", "Task name:", parent=self)
        if not name:
            return
        time_str = simpledialog.askstring("New task", "Time (e.g. 22:50-23:10) — optional:", parent=self) or "Anytime"
        self.tasks.append({"time": time_str, "name": name, "category": "Custom",
                            "minutes": 0, "done": False, "custom": True})
        self.store.save_data()
        self.refresh()

    def delete_task(self, idx):
        if messagebox.askyesno("Delete task", f"Delete '{self.tasks[idx]['name']}'?"):
            self.tasks.pop(idx)
            self.store.save_data()
            self.refresh()

    def reset_today(self):
        if messagebox.askyesno("Reset", "Uncheck all of today's tasks?"):
            for t in self.tasks:
                t["done"] = False
            self.store.save_data()
            self.refresh()

    def notify_focus_session(self):
        self.day["focus_sessions"] = self.day.get("focus_sessions", 0) + 1
        self.store.save_data()



# WEEKLY TAB

class WeeklyTab(tk.Frame):
    def __init__(self, master, store: Store):
        super().__init__(master, bg="#0f172a")
        self.store = store
        self.week_offset = 0  # 0 = current week
        self._build_ui()
        self.refresh()

    def _current_week_dates(self):
        today = datetime.date.today()
        # find this week's Saturday (start of displayed week)
        days_since_sat = (today.weekday() - 5) % 7
        this_sat = today - datetime.timedelta(days=days_since_sat)
        start = this_sat + datetime.timedelta(weeks=self.week_offset)
        return [start + datetime.timedelta(days=i) for i in range(7)]

    def _build_ui(self):
        header = tk.Frame(self, bg="#0f172a")
        header.pack(fill="x", padx=20, pady=(16, 6))
        tk.Button(header, text="◀ Prev week", command=self.prev_week, bg="#1e293b", fg="white",
                   relief="flat", font=("Segoe UI", 9)).pack(side="left")
        self.week_label = tk.Label(header, text="", font=("Segoe UI", 14, "bold"), bg="#0f172a", fg="white")
        self.week_label.pack(side="left", padx=14)
        tk.Button(header, text="Next week ▶", command=self.next_week, bg="#1e293b", fg="white",
                   relief="flat", font=("Segoe UI", 9)).pack(side="left")

        self.days_frame = tk.Frame(self, bg="#0f172a")
        self.days_frame.pack(fill="x", padx=20, pady=6)

        self.summary_frame = tk.Frame(self, bg="#0f172a")
        self.summary_frame.pack(fill="both", expand=True, padx=20, pady=(10, 16))

    def prev_week(self):
        self.week_offset -= 1
        self.refresh()

    def next_week(self):
        self.week_offset += 1
        self.refresh()

    def refresh(self):
        for w in self.days_frame.winfo_children():
            w.destroy()
        for w in self.summary_frame.winfo_children():
            w.destroy()

        dates = self._current_week_dates()
        self.week_label.config(text=f"{dates[0].strftime('%d %b')} – {dates[6].strftime('%d %b %Y')}")

        for d in dates:
            done, total, pct = self.store.day_stats(d.isoformat())
            color = "#22c55e" if pct == 100 else ("#eab308" if pct >= 50 else ("#ef4444" if total else "#334155"))
            card = tk.Frame(self.days_frame, bg="#1e293b", width=76, height=90)
            card.pack(side="left", padx=4, fill="y", expand=True)
            card.pack_propagate(False)
            tk.Label(card, text=WEEKDAY_LABELS[d.weekday()], font=("Segoe UI", 9, "bold"),
                      bg="#1e293b", fg="#94a3b8").pack(pady=(8, 0))
            tk.Label(card, text=str(d.day), font=("Segoe UI", 12, "bold"), bg="#1e293b", fg="white").pack()
            tk.Frame(card, bg=color, height=6, width=50).pack(pady=(6, 2))
            tk.Label(card, text=f"{pct}%", font=("Segoe UI", 9), bg="#1e293b", fg=color).pack()

        # Category totals for the week
        tk.Label(self.summary_frame, text="This week's category minutes (done / scheduled):",
                  font=("Segoe UI", 11, "bold"), bg="#0f172a", fg="white").pack(anchor="w", pady=(0, 6))

        totals_container = tk.Frame(self.summary_frame, bg="#0f172a")
        totals_container.pack(fill="both", expand=True)

        for cat in HABIT_CATEGORIES:
            done_min = total_min = 0
            for d in dates:
                dm, tm = self.store.category_minutes(d.isoformat(), cat)
                done_min += dm
                total_min += tm
            if total_min == 0:
                continue
            row = tk.Frame(totals_container, bg="#1e293b")
            row.pack(fill="x", pady=2)
            tk.Frame(row, bg=CATEGORY_COLORS.get(cat, "#0ea5e9"), width=6).pack(side="left", fill="y")
            tk.Label(row, text=cat, font=("Segoe UI", 10, "bold"), bg="#1e293b", fg="white",
                      width=14, anchor="w").pack(side="left", padx=8, pady=6)
            pct = int(done_min / total_min * 100) if total_min else 0
            tk.Label(row, text=f"{done_min} / {total_min} min  ({pct}%)", font=("Segoe UI", 10),
                      bg="#1e293b", fg="#94a3b8").pack(side="left")



# MONTHLY TAB

class MonthlyTab(tk.Frame):
    def __init__(self, master, store: Store):
        super().__init__(master, bg="#0f172a")
        self.store = store
        today = datetime.date.today()
        self.year, self.month = today.year, today.month
        self._build_ui()
        self.refresh()

    def _build_ui(self):
        header = tk.Frame(self, bg="#0f172a")
        header.pack(fill="x", padx=20, pady=(16, 6))
        tk.Button(header, text="◀", command=self.prev_month, bg="#1e293b", fg="white",
                   relief="flat", font=("Segoe UI", 10, "bold"), width=3).pack(side="left")
        self.month_label = tk.Label(header, text="", font=("Segoe UI", 14, "bold"), bg="#0f172a", fg="white")
        self.month_label.pack(side="left", padx=14)
        tk.Button(header, text="▶", command=self.next_month, bg="#1e293b", fg="white",
                   relief="flat", font=("Segoe UI", 10, "bold"), width=3).pack(side="left")

        self.calendar_frame = tk.Frame(self, bg="#0f172a")
        self.calendar_frame.pack(padx=20, pady=8)

        self.stats_frame = tk.Frame(self, bg="#0f172a")
        self.stats_frame.pack(fill="both", expand=True, padx=20, pady=(10, 16))

    def prev_month(self):
        self.month -= 1
        if self.month == 0:
            self.month = 12
            self.year -= 1
        self.refresh()

    def next_month(self):
        self.month += 1
        if self.month == 13:
            self.month = 1
            self.year += 1
        self.refresh()

    def refresh(self):
        for w in self.calendar_frame.winfo_children():
            w.destroy()
        for w in self.stats_frame.winfo_children():
            w.destroy()

        self.month_label.config(text=datetime.date(self.year, self.month, 1).strftime("%B %Y"))

        for col, wd in enumerate(WEEK_ORDER):
            tk.Label(self.calendar_frame, text=WEEKDAY_LABELS[wd], font=("Segoe UI", 9, "bold"),
                      bg="#0f172a", fg="#94a3b8", width=8).grid(row=0, column=col, pady=(0, 4))

        cal = calendar.Calendar(firstweekday=5)  # weeks start Saturday
        weeks = cal.monthdayscalendar(self.year, self.month)

        for r, week in enumerate(weeks, start=1):
            for c, day_num in enumerate(week):
                if day_num == 0:
                    tk.Frame(self.calendar_frame, bg="#0f172a", width=68, height=54).grid(row=r, column=c, padx=2, pady=2)
                    continue
                d = datetime.date(self.year, self.month, day_num)
                _, total, pct = self.store.day_stats(d.isoformat())
                if d > datetime.date.today():
                    bg = "#1e293b"
                elif total == 0:
                    bg = "#1e293b"
                elif pct == 100:
                    bg = "#16a34a"
                elif pct >= 66:
                    bg = "#22c55e"
                elif pct >= 33:
                    bg = "#eab308"
                elif pct > 0:
                    bg = "#f97316"
                else:
                    bg = "#7f1d1d"
                cell = tk.Frame(self.calendar_frame, bg=bg, width=68, height=54)
                cell.grid(row=r, column=c, padx=2, pady=2)
                cell.grid_propagate(False)
                lbl = tk.Label(cell, text=str(day_num), font=("Segoe UI", 10, "bold"), bg=bg, fg="white")
                lbl.pack(pady=(6, 0))
                pct_lbl = tk.Label(cell, text=f"{pct}%" if total else "-", font=("Segoe UI", 8), bg=bg, fg="white")
                pct_lbl.pack()
                for w in (cell, lbl, pct_lbl):
                    w.bind("<Button-1>", lambda e, ds=d.isoformat(): self.show_day_detail(ds))

        # Monthly stats
        tk.Label(self.stats_frame, text="Monthly streaks (current / best):", font=("Segoe UI", 11, "bold"),
                  bg="#0f172a", fg="white").pack(anchor="w", pady=(0, 6))
        grid = tk.Frame(self.stats_frame, bg="#0f172a")
        grid.pack(fill="x")
        for i, cat in enumerate(HABIT_CATEGORIES):
            cur = self.store.current_streak(cat)
            best = self.store.best_streak(cat)
            if cur == 0 and best == 0:
                continue
            row = tk.Frame(grid, bg="#1e293b")
            row.pack(fill="x", pady=2)
            tk.Frame(row, bg=CATEGORY_COLORS.get(cat, "#0ea5e9"), width=6).pack(side="left", fill="y")
            tk.Label(row, text=cat, font=("Segoe UI", 10, "bold"), bg="#1e293b", fg="white",
                      width=14, anchor="w").pack(side="left", padx=8, pady=6)
            tk.Label(row, text=f"🔥 {cur} day streak   ·   best: {best}", font=("Segoe UI", 10),
                      bg="#1e293b", fg="#94a3b8").pack(side="left")

    def show_day_detail(self, date_str):
        day = self.store.data.get(date_str)
        win = tk.Toplevel(self)
        win.title(date_str)
        win.configure(bg="#0f172a")
        win.geometry("360x400")
        if not day:
            tk.Label(win, text="No data for this day.", bg="#0f172a", fg="white",
                      font=("Segoe UI", 11)).pack(pady=20)
            return
        for t in day["tasks"]:
            mark = "✅" if t["done"] else "⬜"
            tk.Label(win, text=f"{mark} {t['name']}  ({t['category']})", bg="#0f172a",
                      fg="white" if t["done"] else "#94a3b8", font=("Segoe UI", 10),
                      anchor="w", justify="left", wraplength=330).pack(anchor="w", padx=14, pady=2)
        if day.get("notes"):
            tk.Label(win, text=f"Notes: {day['notes']}", bg="#0f172a", fg="#94a3b8",
                      font=("Segoe UI", 9, "italic"), wraplength=330, justify="left").pack(anchor="w", padx=14, pady=(10, 0))



# STUDY TECHNIQUES TAB (with Pomodoro timer)

class StudyTab(tk.Frame):
    def __init__(self, master, store: Store, daily_tab: DailyTab):
        super().__init__(master, bg="#0f172a")
        self.store = store
        self.daily_tab = daily_tab
        self.remaining_seconds = store.settings["pomodoro_work_min"] * 60
        self.is_break = False
        self.running = False
        self.timer_job = None
        self._build_pomodoro()
        self._build_technique_list()

    def _build_pomodoro(self):
        frame = tk.Frame(self, bg="#1e293b")
        frame.pack(fill="x", padx=20, pady=(16, 10))

        tk.Label(frame, text="Pomodoro Timer", font=("Segoe UI", 13, "bold"),
                  bg="#1e293b", fg="white").pack(pady=(12, 2))
        self.mode_label = tk.Label(frame, text="Focus session", font=("Segoe UI", 10),
                                     bg="#1e293b", fg="#22c55e")
        self.mode_label.pack()
        self.timer_label = tk.Label(frame, text=self._fmt_time(), font=("Segoe UI", 34, "bold"),
                                      bg="#1e293b", fg="white")
        self.timer_label.pack(pady=6)

        btns = tk.Frame(frame, bg="#1e293b")
        btns.pack(pady=(0, 14))
        self.start_btn = tk.Button(btns, text="Start", command=self.toggle_timer, bg="#22c55e", fg="white",
                                     relief="flat", font=("Segoe UI", 10, "bold"), padx=14, pady=6)
        self.start_btn.pack(side="left", padx=4)
        tk.Button(btns, text="Reset", command=self.reset_timer, bg="#334155", fg="white",
                   relief="flat", font=("Segoe UI", 10), padx=14, pady=6).pack(side="left", padx=4)

        self.sessions_label = tk.Label(frame, text="", font=("Segoe UI", 9), bg="#1e293b", fg="#94a3b8")
        self.sessions_label.pack(pady=(0, 12))
        self._update_sessions_label()

    def _fmt_time(self):
        m, s = divmod(self.remaining_seconds, 60)
        return f"{m:02d}:{s:02d}"

    def toggle_timer(self):
        self.running = not self.running
        self.start_btn.config(text="Pause" if self.running else "Start")
        if self.running:
            self._tick()

    def _tick(self):
        if not self.running:
            return
        if self.remaining_seconds <= 0:
            self._on_session_end()
            return
        self.remaining_seconds -= 1
        self.timer_label.config(text=self._fmt_time())
        self.timer_job = self.after(1000, self._tick)

    def _on_session_end(self):
        self.running = False
        self.bell()
        if not self.is_break:
            self.daily_tab.notify_focus_session()
            self._update_sessions_label()
            messagebox.showinfo("Pomodoro", "Focus session done. Take a break!")
            self.is_break = True
            self.remaining_seconds = self.store.settings["pomodoro_break_min"] * 60
            self.mode_label.config(text="Break", fg="#eab308")
        else:
            messagebox.showinfo("Pomodoro", "Break's over. Ready for another session?")
            self.is_break = False
            self.remaining_seconds = self.store.settings["pomodoro_work_min"] * 60
            self.mode_label.config(text="Focus session", fg="#22c55e")
        self.start_btn.config(text="Start")
        self.timer_label.config(text=self._fmt_time())

    def reset_timer(self):
        self.running = False
        if self.timer_job:
            self.after_cancel(self.timer_job)
        self.is_break = False
        self.remaining_seconds = self.store.settings["pomodoro_work_min"] * 60
        self.mode_label.config(text="Focus session", fg="#22c55e")
        self.timer_label.config(text=self._fmt_time())
        self.start_btn.config(text="Start")

    def _update_sessions_label(self):
        n = self.daily_tab.day.get("focus_sessions", 0)
        self.sessions_label.config(text=f"Focus sessions completed today: {n}")

    def _build_technique_list(self):
        tk.Label(self, text="Study Technique Library", font=("Segoe UI", 12, "bold"),
                  bg="#0f172a", fg="white").pack(anchor="w", padx=20, pady=(6, 6))

        container = tk.Frame(self, bg="#0f172a")
        container.pack(fill="both", expand=True, padx=20, pady=(0, 16))
        canvas = tk.Canvas(container, bg="#0f172a", highlightthickness=0)
        scrollbar = ttk.Scrollbar(container, orient="vertical", command=canvas.yview)
        inner = tk.Frame(canvas, bg="#0f172a")
        inner.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=inner, anchor="nw", width=560)
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        def _wheel(e):
            canvas.yview_scroll(int(-1 * (e.delta / 120)), "units")
        canvas.bind_all("<MouseWheel>", _wheel)

        for tech in STUDY_TECHNIQUES:
            card = tk.Frame(inner, bg="#1e293b")
            card.pack(fill="x", pady=5, padx=2)
            tk.Label(card, text=tech["name"], font=("Segoe UI", 11, "bold"), bg="#1e293b",
                      fg="white", anchor="w").pack(anchor="w", padx=12, pady=(8, 0))
            tk.Label(card, text=f"Best for: {tech['best_for']}", font=("Segoe UI", 9, "italic"),
                      bg="#1e293b", fg="#22c55e", anchor="w").pack(anchor="w", padx=12)
            tk.Label(card, text=tech["what"], font=("Segoe UI", 9), bg="#1e293b", fg="#cbd5e1",
                      anchor="w", justify="left", wraplength=520).pack(anchor="w", padx=12, pady=(4, 0))
            tk.Label(card, text=f"How: {tech['how']}", font=("Segoe UI", 9), bg="#1e293b", fg="#94a3b8",
                      anchor="w", justify="left", wraplength=520).pack(anchor="w", padx=12, pady=(2, 10))



# SETTINGS TAB

class SettingsTab(tk.Frame):
    def __init__(self, master, store: Store):
        super().__init__(master, bg="#0f172a")
        self.store = store
        self._build_ui()

    def _build_ui(self):
        tk.Label(self, text="Settings", font=("Segoe UI", 14, "bold"), bg="#0f172a",
                  fg="white").pack(anchor="w", padx=20, pady=(16, 10))

        # Off day
        row = tk.Frame(self, bg="#0f172a")
        row.pack(fill="x", padx=20, pady=6)
        tk.Label(row, text="Off day (no school/football):", bg="#0f172a", fg="white",
                  font=("Segoe UI", 10)).pack(side="left")
        self.off_day_var = tk.StringVar(value=WEEKDAY_LABELS[self.store.settings["off_day_index"]])
        off_day_menu = ttk.Combobox(row, textvariable=self.off_day_var, state="readonly",
                                      values=[WEEKDAY_LABELS[i] for i in WEEK_ORDER], width=8)
        off_day_menu.pack(side="left", padx=10)
        off_day_menu.bind("<<ComboboxSelected>>", self.save_off_day)

        # Sleep goal
        row2 = tk.Frame(self, bg="#0f172a")
        row2.pack(fill="x", padx=20, pady=6)
        tk.Label(row2, text="Sleep goal (hours):", bg="#0f172a", fg="white",
                  font=("Segoe UI", 10)).pack(side="left")
        self.sleep_var = tk.IntVar(value=self.store.settings["sleep_goal_hours"])
        sleep_spin = tk.Spinbox(row2, from_=4, to=10, textvariable=self.sleep_var, width=5,
                                  command=self.save_sleep_goal)
        sleep_spin.pack(side="left", padx=10)

        # Pomodoro lengths
        row3 = tk.Frame(self, bg="#0f172a")
        row3.pack(fill="x", padx=20, pady=6)
        tk.Label(row3, text="Pomodoro work / break (min):", bg="#0f172a", fg="white",
                  font=("Segoe UI", 10)).pack(side="left")
        self.work_var = tk.IntVar(value=self.store.settings["pomodoro_work_min"])
        self.break_var = tk.IntVar(value=self.store.settings["pomodoro_break_min"])
        tk.Spinbox(row3, from_=5, to=60, textvariable=self.work_var, width=4,
                    command=self.save_pomodoro).pack(side="left", padx=(10, 4))
        tk.Label(row3, text="/", bg="#0f172a", fg="white").pack(side="left")
        tk.Spinbox(row3, from_=1, to=30, textvariable=self.break_var, width=4,
                    command=self.save_pomodoro).pack(side="left", padx=(4, 0))

        # Rotation subjects
        tk.Label(self, text="Rotating deep-focus subjects (cycles daily):", bg="#0f172a", fg="white",
                  font=("Segoe UI", 10, "bold")).pack(anchor="w", padx=20, pady=(16, 4))
        rot_frame = tk.Frame(self, bg="#0f172a")
        rot_frame.pack(fill="x", padx=20)
        self.rotation_listbox = tk.Listbox(rot_frame, bg="#1e293b", fg="white", height=5,
                                             selectbackground="#334155", relief="flat")
        for subj in self.store.settings["rotation"]:
            self.rotation_listbox.insert("end", subj)
        self.rotation_listbox.pack(side="left", fill="x", expand=True)

        rot_btns = tk.Frame(rot_frame, bg="#0f172a")
        rot_btns.pack(side="left", padx=8)
        tk.Button(rot_btns, text="+ Add", command=self.add_rotation_subject, bg="#1e293b", fg="white",
                   relief="flat", font=("Segoe UI", 9)).pack(fill="x", pady=2)
        tk.Button(rot_btns, text="Remove", command=self.remove_rotation_subject, bg="#1e293b", fg="#f87171",
                   relief="flat", font=("Segoe UI", 9)).pack(fill="x", pady=2)

        # Export / Reset
        tk.Label(self, text="Data", font=("Segoe UI", 10, "bold"), bg="#0f172a", fg="white").pack(
            anchor="w", padx=20, pady=(20, 4))
        data_row = tk.Frame(self, bg="#0f172a")
        data_row.pack(fill="x", padx=20, pady=4)
        tk.Button(data_row, text="Export CSV", command=self.export_csv, bg="#1e293b", fg="white",
                   relief="flat", font=("Segoe UI", 9), padx=10, pady=6).pack(side="left")
        tk.Button(data_row, text="Reset ALL data", command=self.reset_all, bg="#1e293b", fg="#f87171",
                   relief="flat", font=("Segoe UI", 9), padx=10, pady=6).pack(side="left", padx=(10, 0))

        tk.Label(self, text="Note: rotation/off-day changes apply to future days generated from now on;\n"
                              "past days already saved won't be rewritten.",
                  font=("Segoe UI", 8, "italic"), bg="#0f172a", fg="#64748b",
                  justify="left").pack(anchor="w", padx=20, pady=(16, 10))

    def save_off_day(self, event=None):
        label_to_index = {v: k for k, v in WEEKDAY_LABELS.items()}
        self.store.settings["off_day_index"] = label_to_index[self.off_day_var.get()]
        self.store.save_settings()

    def save_sleep_goal(self):
        self.store.settings["sleep_goal_hours"] = self.sleep_var.get()
        self.store.save_settings()

    def save_pomodoro(self):
        self.store.settings["pomodoro_work_min"] = self.work_var.get()
        self.store.settings["pomodoro_break_min"] = self.break_var.get()
        self.store.save_settings()

    def add_rotation_subject(self):
        name = simpledialog.askstring("Add subject", "New rotating subject name:", parent=self)
        if name:
            self.rotation_listbox.insert("end", name)
            self._save_rotation()

    def remove_rotation_subject(self):
        sel = self.rotation_listbox.curselection()
        if sel:
            self.rotation_listbox.delete(sel[0])
            self._save_rotation()

    def _save_rotation(self):
        self.store.settings["rotation"] = list(self.rotation_listbox.get(0, "end"))
        self.store.save_settings()

    def export_csv(self):
        import csv
        path = os.path.join(BASE_DIR, "export.csv")
        with open(path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["date", "time", "task", "category", "minutes", "done"])
            for date_str, day in sorted(self.store.data.items()):
                for t in day["tasks"]:
                    writer.writerow([date_str, t["time"], t["name"], t["category"], t["minutes"], t["done"]])
        messagebox.showinfo("Exported", f"Data exported to:\n{path}")

    def reset_all(self):
        if messagebox.askyesno("Reset ALL data", "This deletes every saved day permanently. Continue?"):
            self.store.data = {}
            self.store.save_data()
            messagebox.showinfo("Done", "All data cleared. Restart the app to regenerate today.")



# PROJECTS TAB — when to stop learning and start building

STATUS_COLORS = {
    "Idea": "#6b7280", "Planning": "#3b82f6", "Building": "#f59e0b",
    "Shipped": "#22c55e", "Paused": "#ef4444",
}
STATUS_ORDER = ["Idea", "Planning", "Building", "Shipped", "Paused"]

PROJECT_GUIDANCE = (
    "Courses and tutorials have diminishing returns fast. Signals it's time to "
    "stop watching and start building:\n\n"
    "• You can predict the next line/step in a tutorial before it shows you.\n"
    "• You've learned the core syntax/tools of a topic (not mastered — just enough "
    "to be dangerous).\n"
    "• You're consuming content but can't remember what you learned last week.\n\n"
    "Rule of thumb: ~20% learning, ~80% building. Pick a project slightly above "
    "your comfort level, get stuck constantly, and Google/ask specific questions "
    "as they come up — that's when real learning happens. Ship something small "
    "every 2-4 weeks rather than one 'perfect' project for months."
)


class ProjectsTab(tk.Frame):
    def __init__(self, master, store: Store):
        super().__init__(master, bg="#0f172a")
        self.store = store
        self._build_ui()
        self.refresh()

    def _build_ui(self):
        tk.Label(self, text="Projects — Learn, then Build", font=("Segoe UI", 14, "bold"),
                  bg="#0f172a", fg="white").pack(anchor="w", padx=20, pady=(16, 8))

        guidance_card = tk.Frame(self, bg="#1e293b")
        guidance_card.pack(fill="x", padx=20, pady=(0, 10))
        tk.Frame(guidance_card, bg="#f43f5e", width=5).pack(side="left", fill="y")
        tk.Label(guidance_card, text=PROJECT_GUIDANCE, font=("Segoe UI", 9), bg="#1e293b",
                  fg="#cbd5e1", justify="left", anchor="w", wraplength=540).pack(
                      side="left", padx=12, pady=10, fill="both", expand=True)

        add_row = tk.Frame(self, bg="#0f172a")
        add_row.pack(fill="x", padx=20, pady=(0, 8))
        tk.Button(add_row, text="+ Add project", command=self.add_project, bg="#1e293b", fg="white",
                   relief="flat", font=("Segoe UI", 10, "bold"), padx=10, pady=6).pack(side="left")

        container = tk.Frame(self, bg="#0f172a")
        container.pack(fill="both", expand=True, padx=20, pady=(0, 16))
        canvas = tk.Canvas(container, bg="#0f172a", highlightthickness=0)
        scrollbar = ttk.Scrollbar(container, orient="vertical", command=canvas.yview)
        self.list_frame = tk.Frame(canvas, bg="#0f172a")
        self.list_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=self.list_frame, anchor="nw", width=560)
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        def _wheel(e):
            canvas.yview_scroll(int(-1 * (e.delta / 120)), "units")
        canvas.bind_all("<MouseWheel>", _wheel)

    def refresh(self):
        for w in self.list_frame.winfo_children():
            w.destroy()
        if not self.store.projects:
            tk.Label(self.list_frame, text="No projects yet. Add one once you're ready to build.",
                      font=("Segoe UI", 9, "italic"), bg="#0f172a", fg="#64748b").pack(anchor="w", pady=10)
            return
        for p in self.store.projects:
            self._render_project(p)

    def _render_project(self, p):
        cat_color = CATEGORY_COLORS.get(p["category"], "#0ea5e9")
        status_color = STATUS_COLORS.get(p["status"], "#6b7280")

        card = tk.Frame(self.list_frame, bg="#1e293b")
        card.pack(fill="x", pady=4, padx=2)
        tk.Frame(card, bg=cat_color, width=6).pack(side="left", fill="y")

        body = tk.Frame(card, bg="#1e293b")
        body.pack(side="left", fill="both", expand=True, padx=10, pady=8)

        top = tk.Frame(body, bg="#1e293b")
        top.pack(fill="x")
        tk.Label(top, text=p["name"], font=("Segoe UI", 11, "bold"), bg="#1e293b",
                  fg="white", anchor="w").pack(side="left")
        badge = tk.Label(top, text=p["status"], font=("Segoe UI", 8, "bold"), bg=status_color,
                           fg="white", padx=6, pady=1)
        badge.pack(side="left", padx=8)

        tk.Label(body, text=f"{p['category']}  ·  started {p['created']}", font=("Segoe UI", 9),
                  bg="#1e293b", fg="#94a3b8", anchor="w").pack(anchor="w", pady=(2, 0))
        if p.get("notes"):
            tk.Label(body, text=p["notes"], font=("Segoe UI", 9), bg="#1e293b", fg="#cbd5e1",
                      anchor="w", justify="left", wraplength=380).pack(anchor="w", pady=(4, 0))

        controls = tk.Frame(card, bg="#1e293b")
        controls.pack(side="right", padx=8)
        status_var = tk.StringVar(value=p["status"])
        status_menu = ttk.Combobox(controls, textvariable=status_var, values=STATUS_ORDER,
                                     state="readonly", width=9)
        status_menu.pack(pady=(8, 2))
        status_menu.bind("<<ComboboxSelected>>",
                          lambda e, pid=p["id"], v=status_var: self._set_status(pid, v.get()))
        tk.Button(controls, text="✕", command=lambda pid=p["id"]: self.delete_project(pid),
                   bg="#1e293b", fg="#f87171", relief="flat", font=("Segoe UI", 9, "bold"), bd=0).pack()

    def _set_status(self, project_id, status):
        self.store.update_project(project_id, status=status)
        self.refresh()

    def add_project(self):
        name = simpledialog.askstring("New project", "Project name:", parent=self)
        if not name:
            return
        categories = [c for c in CATEGORY_COLORS if c not in ("Rest", "Custom", "School")]
        cat_win = tk.Toplevel(self)
        cat_win.title("Category")
        cat_win.configure(bg="#0f172a")
        tk.Label(cat_win, text="Which subject area is this project for?", bg="#0f172a", fg="white",
                  font=("Segoe UI", 10)).pack(padx=16, pady=(14, 6))
        cat_var = tk.StringVar(value=categories[0])
        ttk.Combobox(cat_win, textvariable=cat_var, values=categories, state="readonly").pack(padx=16, pady=4)

        def confirm():
            notes = simpledialog.askstring("New project", "Short notes / goal (optional):", parent=self) or ""
            self.store.add_project(name, cat_var.get(), "Idea", notes)
            cat_win.destroy()
            self.refresh()

        tk.Button(cat_win, text="Add", command=confirm, bg="#22c55e", fg="white",
                   relief="flat", font=("Segoe UI", 10, "bold"), padx=12, pady=6).pack(pady=12)

    def delete_project(self, project_id):
        if messagebox.askyesno("Delete project", "Delete this project?"):
            self.store.delete_project(project_id)
            self.refresh()



# DOWNLOADS TAB — save tutorial videos for offline learning (via yt-dlp)

DOWNLOAD_DISCLAIMER = (
    "Only download videos you have the right to save — your own uploads, "
    "content with a permissive/Creative-Commons license, or material whose "
    "creator has given permission for offline use. Respect copyright and "
    "YouTube's Terms of Service; this is meant for saving your own tutorial "
    "playlists for offline studying, not for redistributing others' content."
)


class DownloadsTab(tk.Frame):
    def __init__(self, master, store: Store):
        super().__init__(master, bg="#0f172a")
        self.store = store
        self._build_ui()
        self.check_tool()

    def _build_ui(self):
        tk.Label(self, text="Downloads (offline learning videos)", font=("Segoe UI", 14, "bold"),
                  bg="#0f172a", fg="white").pack(anchor="w", padx=20, pady=(16, 6))

        disclaimer_card = tk.Frame(self, bg="#1e293b")
        disclaimer_card.pack(fill="x", padx=20, pady=(0, 10))
        tk.Frame(disclaimer_card, bg="#eab308", width=5).pack(side="left", fill="y")
        tk.Label(disclaimer_card, text=DOWNLOAD_DISCLAIMER, font=("Segoe UI", 8, "italic"),
                  bg="#1e293b", fg="#94a3b8", justify="left", anchor="w", wraplength=540).pack(
                      side="left", padx=12, pady=8, fill="both", expand=True)

        self.tool_status_label = tk.Label(self, text="", font=("Segoe UI", 9), bg="#0f172a", fg="#94a3b8")
        self.tool_status_label.pack(anchor="w", padx=20)
        self.install_btn = tk.Button(self, text="Install / update yt-dlp", command=self.install_tool,
                                       bg="#1e293b", fg="white", relief="flat", font=("Segoe UI", 9), padx=8, pady=4)

        form = tk.Frame(self, bg="#0f172a")
        form.pack(fill="x", padx=20, pady=(10, 6))

        tk.Label(form, text="Video URL:", bg="#0f172a", fg="white", font=("Segoe UI", 9)).grid(
            row=0, column=0, sticky="w")
        self.url_entry = tk.Entry(form, bg="#1e293b", fg="white", insertbackground="white",
                                    relief="flat", font=("Segoe UI", 10))
        self.url_entry.grid(row=0, column=1, columnspan=2, sticky="ew", padx=(8, 0), pady=4)

        tk.Label(form, text="Quality:", bg="#0f172a", fg="white", font=("Segoe UI", 9)).grid(
            row=1, column=0, sticky="w")
        self.quality_var = tk.StringVar(value="Best")
        ttk.Combobox(form, textvariable=self.quality_var, state="readonly",
                      values=["Best", "1080p", "720p", "Audio only (mp3)"], width=18).grid(
                          row=1, column=1, sticky="w", padx=(8, 0), pady=4)

        tk.Label(form, text="Save to:", bg="#0f172a", fg="white", font=("Segoe UI", 9)).grid(
            row=2, column=0, sticky="w")
        self.dir_var = tk.StringVar(value=self._download_dir())
        tk.Entry(form, textvariable=self.dir_var, bg="#1e293b", fg="white", insertbackground="white",
                  relief="flat", font=("Segoe UI", 9)).grid(row=2, column=1, sticky="ew", padx=(8, 4), pady=4)
        tk.Button(form, text="Browse", command=self.browse_dir, bg="#334155", fg="white",
                   relief="flat", font=("Segoe UI", 8)).grid(row=2, column=2, pady=4)

        form.columnconfigure(1, weight=1)

        self.download_btn = tk.Button(self, text="Download", command=self.start_download, bg="#22c55e",
                                        fg="white", relief="flat", font=("Segoe UI", 10, "bold"), padx=14, pady=6)
        self.download_btn.pack(anchor="w", padx=20, pady=(4, 8))

        self.log_text = tk.Text(self, bg="#1e293b", fg="#cbd5e1", relief="flat", height=14,
                                  font=("Consolas", 9), insertbackground="white")
        self.log_text.pack(fill="both", expand=True, padx=20, pady=(0, 16))
        self.log_text.configure(state="disabled")

    def _download_dir(self):
        d = self.store.settings.get("download_dir", "downloads")
        return d if os.path.isabs(d) else os.path.join(BASE_DIR, d)

    def browse_dir(self):
        chosen = filedialog.askdirectory(initialdir=self.dir_var.get())
        if chosen:
            self.dir_var.set(chosen)

    def check_tool(self):
        if shutil.which("yt-dlp"):
            self.tool_status_label.config(text="✅ yt-dlp found and ready.", fg="#22c55e")
            self.install_btn.pack_forget()
        else:
            self.tool_status_label.config(text="⚠ yt-dlp not found on this system.", fg="#f87171")
            self.install_btn.pack(anchor="w", padx=20, pady=(2, 0))

    def install_tool(self):
        self.log("Installing yt-dlp via pip...")

        def run():
            try:
                proc = subprocess.run(
                    ["pip", "install", "--user", "-U", "yt-dlp"],
                    capture_output=True, text=True,
                )
                self.after(0, lambda: self.log(proc.stdout + proc.stderr))
                self.after(0, self.check_tool)
            except Exception as e:
                self.after(0, lambda: self.log(f"Install failed: {e}"))

        threading.Thread(target=run, daemon=True).start()

    def log(self, msg):
        self.log_text.configure(state="normal")
        self.log_text.insert("end", msg.rstrip() + "\n")
        self.log_text.see("end")
        self.log_text.configure(state="disabled")

    def start_download(self):
        url = self.url_entry.get().strip()
        if not url:
            messagebox.showwarning("Missing URL", "Paste a video URL first.")
            return
        if not shutil.which("yt-dlp"):
            messagebox.showwarning("yt-dlp missing", "Install yt-dlp first using the button above.")
            return

        out_dir = self.dir_var.get().strip() or self._download_dir()
        os.makedirs(out_dir, exist_ok=True)
        self.store.settings["download_dir"] = out_dir
        self.store.save_settings()

        quality = self.quality_var.get()
        out_template = os.path.join(out_dir, "%(title)s.%(ext)s")

        if quality == "Audio only (mp3)":
            cmd = ["yt-dlp", "-x", "--audio-format", "mp3", "-o", out_template, url]
        elif quality == "1080p":
            cmd = ["yt-dlp", "-f", "bv*[height<=1080]+ba/b[height<=1080]", "-o", out_template, url]
        elif quality == "720p":
            cmd = ["yt-dlp", "-f", "bv*[height<=720]+ba/b[height<=720]", "-o", out_template, url]
        else:
            cmd = ["yt-dlp", "-o", out_template, url]

        self.download_btn.config(state="disabled", text="Downloading...")
        self.log(f"Running: {' '.join(cmd)}")

        def run():
            try:
                proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                          text=True, bufsize=1)
                for line in proc.stdout:
                    self.after(0, lambda l=line: self.log(l))
                proc.wait()
                self.after(0, lambda: self.log("Done." if proc.returncode == 0 else
                                                 f"Exited with code {proc.returncode}"))
            except Exception as e:
                self.after(0, lambda: self.log(f"Error: {e}"))
            finally:
                self.after(0, lambda: self.download_btn.config(state="normal", text="Download"))

        threading.Thread(target=run, daemon=True).start()



# MAIN APP

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Growth Tracker")
        self.geometry("700x820")
        self.configure(bg="#0f172a")
        self.minsize(600, 660)

        self.store = Store()

        style = ttk.Style(self)
        style.theme_use("clam")
        style.configure("TNotebook", background="#0f172a", borderwidth=0)
        style.configure("TNotebook.Tab", background="#1e293b", foreground="white",
                          padding=(12, 8), font=("Segoe UI", 9, "bold"))
        style.map("TNotebook.Tab", background=[("selected", "#334155")])

        notebook = ttk.Notebook(self)
        notebook.pack(fill="both", expand=True)

        daily_tab = DailyTab(notebook, self.store)
        weekly_tab = WeeklyTab(notebook, self.store)
        monthly_tab = MonthlyTab(notebook, self.store)
        study_tab = StudyTab(notebook, self.store, daily_tab)
        projects_tab = ProjectsTab(notebook, self.store)
        downloads_tab = DownloadsTab(notebook, self.store)
        settings_tab = SettingsTab(notebook, self.store)

        notebook.add(daily_tab, text="Daily")
        notebook.add(weekly_tab, text="Weekly")
        notebook.add(monthly_tab, text="Monthly")
        notebook.add(study_tab, text="Study")
        notebook.add(projects_tab, text="Projects")
        notebook.add(downloads_tab, text="Downloads")
        notebook.add(settings_tab, text="Settings")

        def on_tab_changed(event):
            tab = event.widget.tab(event.widget.select(), "text")
            if tab == "Weekly":
                weekly_tab.refresh()
            elif tab == "Monthly":
                monthly_tab.refresh()
            elif tab == "Projects":
                projects_tab.refresh()

        notebook.bind("<<NotebookTabChanged>>", on_tab_changed)


if __name__ == "__main__":
    app = App()
    app.mainloop()
