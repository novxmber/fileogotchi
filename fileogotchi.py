import customtkinter as ctk
from plyer import notification
import os
import winreg
import sys
import json
import shutil
import random
import psutil
from tkinterdnd2 import TkinterDnD, DND_FILES
from pycaw.pycaw import AudioUtilities, IAudioMeterInformation
import asyncio
from winsdk.windows.media.control import GlobalSystemMediaTransportControlsSessionManager as SessionManager

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
FEED_DIR = os.path.join(SCRIPT_DIR, "feed")
TOILET_DIR = os.path.join(SCRIPT_DIR, "toilet")
SAVE_FILE = os.path.join(SCRIPT_DIR, "fileo_save.json")

if getattr(sys, 'frozen', False):
    SCRIPT_DIR = os.path.dirname(sys.executable)
else:
    SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

for folder in [FEED_DIR, TOILET_DIR]:
    if not os.path.exists(folder): 
        os.makedirs(folder)
        if folder == FEED_DIR:
            startup_file = os.path.join(FEED_DIR, "foryou.txt")
            if not os.path.exists(startup_file):
                with open(startup_file, "w") as f:
                    f.write("heres your very own first fileogatchi, take good care of it!")

poopTime = 600000
randomEventTime = 483200
is_muted = False
is_transparent = False
movement_enabled = True
randomevents_enabled = True
current_appearance = "dark"
walk_direction_x = 1
walk_direction_y = 1
is_drifting = False
level = 0
xp = 0
happiness = 100
personalityType = "default"
stats = {"files_fed": 0, "text_files": 0, "image_files": 0, "video_files": 0, "executables": 0, "zips": 0, "audio_files": 0}
hover_job = None
is_blushing = False

poopmessages = {
    ".txt": ["this poop has a lot of words", "this tasted a bit like paper"],
    ".jpg": ["i felt the pixels in this food", "this poop is very colorful"],
    ".png": ["this poop has transparency", "i could see right through this food"],
    ".mp3": ["whyd you feed me a sound????", "i could really hear this one"],
    ".mp4": ["this poop was animated", "i watched this before eating"],
    ".pdf": ["this poop is very informative", "i read this food thoroughly"],
    ".exe": ["this ran well"],
    ".zip": ["this poop is compressed", "i had to unzip this poop"],
    "default": ["that was an unknown flavor...", "yummy"]
}

faces = {
    "default": {
        "happy": "(^ᴗ^)", 
        "blush": "(^//^)", 
        "music": "(♪^_^)",
        "stressed": "(>_<)"
    }, 
    "tech": {
        "happy": "(⌐■_■)", 
        "blush": "(⌐■//■)", 
        "music": "(⌐■_■)♪",
        "stressed": "(⌐■_■)!"
    }, 
    "artist": {
        "happy": "(🎨^_^)", 
        "blush": "(🎨^//^)", 
        "music": "(🎨^_^)♪",
        "stressed": "(🎨>_<)"
    }, 
    "musical": {
        "happy": "d[-_-]b", 
        "blush": "d[>//<]b", 
        "music": "d[-ᴗ-]b♪",
        "stressed": "d[>_<]b"
    }
}

def save_all():
    data = {
        "name": name.cget("text"), "is_muted": is_muted, "mode": current_appearance,
        "movement_enabled": movement_enabled, "level": level, "xp": xp,
        "type": personalityType, "stats": stats, "is_transparent": is_transparent,
        "randomevents_enabled": randomevents_enabled, "happiness": happiness
    }
    with open(SAVE_FILE, "w") as f: json.dump(data, f)

def load_data():
    global is_muted, current_appearance, movement_enabled, level, xp, personalityType, stats, is_transparent, randomevents_enabled, happiness
    if os.path.exists(SAVE_FILE):
        try:
            with open(SAVE_FILE, "r") as f:
                data = json.load(f)
                is_muted = data.get("is_muted", False)
                movement_enabled = data.get("movement_enabled", True)
                current_appearance = data.get("mode", "dark")
                level = data.get("level", 0); xp = data.get("xp", 0)
                personalityType = data.get("type", "default")
                stats = data.get("stats", stats)
                is_transparent = data.get("is_transparent", False)
                randomevents_enabled = data.get("randomevents_enabled", True)
                happiness = data.get("happiness", 100)
                ctk.set_appearance_mode(current_appearance)
                return data
        except: return None
    return None

async def get_media_info():
    try:
        sessions = await SessionManager.request_async()
        current_session = sessions.get_current_session()
        if current_session:
            info = await current_session.try_get_media_properties_async()
            if info:
                return f"{info.artist} - {info.title}"
    except: pass
    return None

def apply_transparency():
    if is_transparent:
        root.overrideredirect(True)
        root.configure(fg_color='#000001') 
        root.wm_attributes("-transparentcolor", '#000001')
        for w in [fileo, name, status]: w.configure(fg_color='#000001')
    else:
        root.overrideredirect(False)
        root.wm_attributes("-transparentcolor", "")
        mode_idx = 0 if current_appearance == "light" else 1
        theme_bg = ctk.ThemeManager.theme["CTk"]["fg_color"][mode_idx]
        root.configure(fg_color=theme_bg)
        for w in [fileo, name, status]: w.configure(fg_color="transparent")
    save_all()

def check_music():
    playing = False
    ignore_list = ["discord.exe", "systemsettings.exe", "svchost.exe"]
    
    try:
        sessions = AudioUtilities.GetAllSessions()
        for session in sessions:
            if session.Process:
                proc_name = session.Process.name().lower()
                
                if proc_name in ignore_list:
                    continue
                
                meter = session._ctl.QueryInterface(IAudioMeterInformation)
                if meter and meter.GetPeakValue() > 0.01:
                    playing = True
                    break
    except: pass
    
    if playing:
        try:
            song = asyncio.run(get_media_info())
            return True, song
        except:
            return True, None
    return False, None

def drift_logic():
    global walk_direction_x, walk_direction_y, is_drifting
    txt = status.cget("text").lower()
    if ("bored" in txt or "hungry" in txt) and movement_enabled:
        is_drifting = True
        x, y = root.winfo_x(), root.winfo_y()
        sw, sh = root.winfo_screenwidth(), root.winfo_screenheight()
        if x + 200 >= sw or x <= 0: walk_direction_x *= -1
        if y + 250 >= sh or y <= 0: walk_direction_y *= -1
        root.geometry(f"+{x + (walk_direction_x * 2)}+{y + (walk_direction_y * 2)}")
        root.after(30, drift_logic) 
    else:
        is_drifting = False
        root.after(2000, drift_logic)

def update_logic():
    try:
        cpu = psutil.cpu_percent()
        feed_count = len(os.listdir(FEED_DIR))
        toilet_count = len(os.listdir(TOILET_DIR))
        is_playing, song_name = check_music()

        if level < 3: fileo.configure(font=("Helvetica", 25))
        elif 3 <= level < 6: fileo.configure(font=("Helvetica", 35))
        else: fileo.configure(font=("Helvetica", 45))

        if is_blushing:
            fileo.configure(text=faces.get(personalityType, faces['default']).get("blush"))
            status.configure(text=f"status: blushing~\nit appreciates you")
            root.after(2000, lambda: globals().update(is_blushing=False))
            save_all()
            root.update_idletasks()
        elif cpu > 80:
            fileo.configure(text="(°ロ°)") 
            status.configure(text=f"status: OVERHEATING!\nCPU is at {cpu}%")
        
        elif toilet_count > 5:
            fileo.configure(text="(X_X)")
            status.configure(text="status: disgusted\nclean the toilet")
        
        elif feed_count > 8:
            fileo.configure(text=faces.get(personalityType, faces['default']).get("stressed"))
            status.configure(text="status: stressed\nfull!")

        elif is_playing:
            fileo.configure(text=faces.get(personalityType, faces['default']).get("music"))
            display_song = song_name if song_name else "vibing to music"
            status.configure(text=f"status: enjoying music\n{display_song}")

            if movement_enabled:
                current_x, current_y = root.winfo_x(), root.winfo_y()
                root.geometry(f"+{current_x}+{current_y - 5}")
                root.update_idletasks()
                root.after(100, lambda: root.geometry(f"+{current_x}+{current_y}"))

        elif feed_count == 0:
            fileo.configure(text="(⇀_↼)")
            status.configure(text="status: bored/hungry\nfeed it some files!")

        else:
            fileo.configure(text=faces.get(personalityType, faces["default"]).get("happy"))
            status.configure(text="status: happy!")

    except Exception as e:
        print(f"Update error: {e}")
        fileo.configure(text="(X_X)")
        
    root.after(2000, update_logic)

def on_hover_enter(event):
    global hover_job
    hover_job = root.after(1500, start_blush)

def on_hover_leave(event):
    global hover_job, is_blushing
    if hover_job:
        root.after_cancel(hover_job)
        hover_job = None
    is_blushing = False

def start_blush():
    global is_blushing
    is_blushing = True

def poop():
    try:
        files = [f for f in os.listdir(FEED_DIR) if os.path.isfile(os.path.join(FEED_DIR, f))]
        if files:
            target_file = random.choice(files)
            old_path = os.path.join(FEED_DIR, target_file)
            new_name = f"poop_{random.randint(1, 999)}.txt"
            new_path = os.path.join(TOILET_DIR, new_name)
            ext = os.path.splitext(target_file)[1].lower()
            options = poopmessages.get(ext, poopmessages["default"])
            shutil.move(old_path, new_path)
            with open(new_path, "w") as f: f.write(random.choice(options))
            if not is_muted: os.startfile(new_path)
            notification.notify(title="fileogatchi", message="i just pooped.", timeout=3)
        else:
            if happiness > 0:
                happiness -= 30
                
                notification.notify(title="fileogatchi", message="i'm feeling hungry...", timeout=3)

                save_all()
    except Exception as e: print(f"Poop error: {e}")
    root.after(poopTime, poop)

def flush():
    files = os.listdir(TOILET_DIR)
    count = 0
    for f in files:
        file_path = os.path.join(TOILET_DIR, f)
        if os.path.isfile(file_path):
            os.remove(file_path); count += 1
    notification.notify(title="fileogatchi", message=f"flushed {count} files!!")

def pet_message(message):
    if getattr(sys, 'frozen', False):
        SCRIPT_DIR = os.path.dirname(sys.executable)
    else:
        SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
    
    note_path = os.path.join(SCRIPT_DIR, "pet_note.txt")

    with open(note_path, "w") as f:
        f.write(message)

    os.startfile(note_path)

def randomEvent():
    if randomevents_enabled:
        event_type = random.choice(["gratitude"])
        if event_type == "gratitude":
            pet_message("thank u for taking care of me <3\n- your fileogatchi")
    root.after(randomEventTime, randomEvent)

def settingsOpen():
    swin = ctk.CTkToplevel(root)
    swin.title("settings"); swin.geometry("250x300")
    swin.attributes("-topmost", True); swin.grab_set()
    ctk.CTkSwitch(swin, text="light mode", command=toggle_appearance).pack(pady=10)
    m_sw = ctk.CTkSwitch(swin, text="mute poop notes", command=lambda: [globals().update(is_muted=m_sw.get()), save_all()])
    if is_muted: m_sw.select()
    m_sw.pack(pady=10)
    mv_sw = ctk.CTkSwitch(swin, text="enable movement", command=lambda: [globals().update(movement_enabled=mv_sw.get()), save_all()])
    if movement_enabled: mv_sw.select()
    mv_sw.pack(pady=10)
    t_sw = ctk.CTkSwitch(swin, text="transparent mode", command=lambda: [globals().update(is_transparent=t_sw.get()), apply_transparency()])
    if is_transparent: t_sw.select()
    t_sw.pack(pady=10)
    re_sw = ctk.CTkSwitch(swin, text="enable random events", command=lambda: [globals().update(randomevents_enabled=re_sw.get()), save_all()])
    if randomevents_enabled: re_sw.select()
    re_sw.pack(pady=10)
    ctk.CTkButton(swin, text="Quit App", command=root.quit).pack(pady=10)

def toggle_appearance():
    global current_appearance
    current_appearance = "light" if ctk.get_appearance_mode() == "Dark" else "dark"
    ctk.set_appearance_mode(current_appearance)
    root.update(); apply_transparency()

def interactOpen():
    iw = ctk.CTkToplevel(root)
    iw.title("interact"); iw.geometry("200x280")
    iw.attributes("-topmost", True); iw.grab_set()
    ctk.CTkLabel(iw, text=f"level: {level}\nxp: {xp}\npersonality: {personalityType}\nhappiness: {happiness}").pack(pady=10)
    ctk.CTkButton(iw, text="flush toilet", command=flush).pack(pady=10)
    ctk.CTkButton(iw, text="stats", command=lambda: statsOpen()).pack(pady=10)
    ctk.CTkButton(iw, text="settings", command=lambda: settingsOpen()).pack(pady=10)

def statsOpen():
    s = ctk.CTkToplevel(root)
    s.title("stats"); s.geometry("200x200")
    s.attributes("-topmost", True); s.grab_set()
    ctk.CTkLabel(s, text=f"files fed: {stats['files_fed']}\ntext: {stats['text_files']}\nimg: {stats['image_files']}\nvid: {stats['video_files']}\nexe: {stats['executables']}\nzip: {stats['zips']}\naudio: {stats['audio_files']}").pack(pady=10)

def handle_drop(event):
    global xp, level, personalityType, stats
    path = event.data.strip().strip('{}')

    if os.path.exists(path):
        dest = os.path.join(FEED_DIR, os.path.basename(path))

        try:
            shutil.move(path, dest)
            fileo.configure(text="(^O^)")
            stats["files_fed"] += 1
            ext = os.path.splitext(path)[1].lower()
            if ext in [".txt", ".md"]: stats["text_files"] += 1
            elif ext in [".jpg", ".png", ".gif"]: stats["image_files"] += 1
            elif ext in [".mp4", ".mov"]: stats["video_files"] += 1
            elif ext in [".exe", ".bat"]: stats["executables"] += 1
            elif ext in [".zip", ".rar"]: stats["zips"] += 1
            elif ext in [".mp3", ".wav", ".ogg"]: stats["audio_files"] += 1

            diet = stats.copy(); diet.pop("files_fed", None)

            top = max(diet, key=diet.get)

            if diet[top] >= 3:
                if top == "image_files": personalityType = "artist"
                elif top == "executables": personalityType = "tech"
                elif top == "audio_files": personalityType = "musical"
                else: personalityType = "default"

            xp += 1

            if xp >= 5: xp = 0; level += 1; notification.notify(title="fileogatchi", message="Level Up!")

            save_all()

        except: pass

class App(ctk.CTk, TkinterDnD.DnDWrapper):
    def __init__(self):
        super().__init__()
        self.TkdndVersion = TkinterDnD._require(self)

        self.drop_target_register(DND_FILES)
        self.dnd_bind('<<Drop>>', handle_drop)

if __name__ == "__main__":
    root = App()
    root.title("fileogatchi"); root.minsize(200, 250); root.attributes("-topmost", True)

    fileo = ctk.CTkLabel(root, text="(^_^)", font=("Helvetica", 45))
    fileo.pack(pady=10)

    fileo.bind("<Enter>", on_hover_enter)
    fileo.bind("<Leave>", on_hover_leave)

    name = ctk.CTkLabel(root, text="file-o"); name.pack(pady=10)
    status = ctk.CTkLabel(root, text="status:"); status.pack(pady=10)
    ctk.CTkButton(root, text="interact", command=interactOpen).pack(pady=10)

    saved = load_data()
    if saved:
        name.configure(text=saved["name"]); root.title(saved["name"])
        apply_transparency()
    else:
        setup = ctk.CTkToplevel(root); setup.geometry("250x150"); setup.grab_set()
        ctk.CTkLabel(setup, text="name your pet:").pack(pady=10)
        ne = ctk.CTkEntry(setup); ne.pack(pady=5)
        def set_n():
            if ne.get().strip():
                name.configure(text=ne.get()); root.title(ne.get()); save_all(); setup.destroy()
        ctk.CTkButton(setup, text="begin life", command=set_n).pack(pady=10)

    update_logic(); root.after(poopTime, poop); root.after(randomEventTime, randomEvent); drift_logic()
    root.mainloop()
