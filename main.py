"""
AutoClicker - by Napat
======================
Mode 1 : Mouse auto-click at current cursor position
Mode 2 : Keyboard key sequence (loop)
Mode 3 : Multi-position click (draggable overlay)
"""

import tkinter as tk
from tkinter import ttk
import threading
import time
from pynput.mouse import Button, Controller as MouseCtrl
from pynput.keyboard import Key, Controller as KeyboardCtrl, Listener as KbListener

# ─────────────────────────────────────────────
#  Helpers
# ─────────────────────────────────────────────
SPECIAL_KEYS = {
    'space': Key.space, 'enter': Key.enter, 'tab': Key.tab,
    'backspace': Key.backspace, 'delete': Key.delete,
    'esc': Key.esc, 'shift': Key.shift, 'ctrl': Key.ctrl,
    'alt': Key.alt, 'up': Key.up, 'down': Key.down,
    'left': Key.left, 'right': Key.right,
    'f1': Key.f1, 'f2': Key.f2, 'f3': Key.f3, 'f4': Key.f4,
    'f5': Key.f5, 'f6': Key.f6, 'f7': Key.f7, 'f8': Key.f8,
}

def key_to_label(key) -> str:
    try:
        if hasattr(key, 'char') and key.char:
            return key.char.upper()
        if hasattr(key, 'name'):
            return key.name.upper()
    except Exception:
        pass
    return str(key)

def key_to_press_value(key):
    try:
        if hasattr(key, 'char') and key.char:
            return key.char
        if hasattr(key, 'name'):
            name = key.name.lower()
            return SPECIAL_KEYS.get(name, key)
    except Exception:
        pass
    return key


# ─────────────────────────────────────────────
#  Overlay window (Mode 3)
# ─────────────────────────────────────────────
class OverlayWindow:
    MARKER_R     = 22
    COLOR_CIRCLE = '#00ffff'
    COLOR_NUM    = '#ffff00'
    COLOR_BG     = 'black'

    def __init__(self, root, positions: list, on_update):
        self.positions = positions
        self.on_update = on_update
        self.drag_data = {}

        sw = root.winfo_screenwidth()
        sh = root.winfo_screenheight()

        self.win = tk.Toplevel(root)
        self.win.geometry(f"{sw}x{sh}+0+0")
        self.win.overrideredirect(True)
        self.win.wm_attributes('-topmost', True)
        self.win.wm_attributes('-transparentcolor', self.COLOR_BG)
        self.win.config(bg=self.COLOR_BG)

        self.canvas = tk.Canvas(self.win, bg=self.COLOR_BG, highlightthickness=0)
        self.canvas.pack(fill='both', expand=True)

        close = tk.Button(self.win, text='✕ ปิด Overlay',
                          bg='#cc0000', fg='white', font=('Arial', 10, 'bold'),
                          relief='flat', padx=6, pady=3,
                          command=self.win.destroy)
        close.place(x=sw - 130, y=8)

        self.redraw()

    def redraw(self):
        self.canvas.delete('all')
        self.drag_data.clear()
        for i, pos in enumerate(self.positions):
            self._draw_marker(i, pos[0], pos[1])

    def _draw_marker(self, idx, x, y):
        r   = self.MARKER_R
        tag = f'mk{idx}'
        self.canvas.create_oval(x-r, y-r, x+r, y+r,
            outline=self.COLOR_CIRCLE, width=2, fill='', tags=tag)
        self.canvas.create_line(x-r, y, x+r, y,
            fill=self.COLOR_CIRCLE, width=2, tags=tag)
        self.canvas.create_line(x, y-r, x, y+r,
            fill=self.COLOR_CIRCLE, width=2, tags=tag)
        self.canvas.create_text(x+r+4, y-r+2, text=str(idx+1),
            fill=self.COLOR_NUM, font=('Arial', 11, 'bold'), tags=tag)
        self.canvas.tag_bind(tag, '<Button-1>',
                             lambda e, i=idx: self._drag_start(e, i))
        self.canvas.tag_bind(tag, '<B1-Motion>',
                             lambda e, i=idx: self._drag_move(e, i))

    def _drag_start(self, event, idx):
        self.drag_data[idx] = (event.x, event.y)

    def _drag_move(self, event, idx):
        if idx not in self.drag_data:
            return
        ox, oy = self.drag_data[idx]
        dx, dy = event.x - ox, event.y - oy
        self.canvas.move(f'mk{idx}', dx, dy)
        self.positions[idx][0] += dx
        self.positions[idx][1] += dy
        self.drag_data[idx] = (event.x, event.y)
        self.on_update()

    def hide(self):
        if self.alive: self.win.withdraw()

    def show(self):
        if self.alive: self.win.deiconify()

    def destroy(self):
        if self.alive: self.win.destroy()

    @property
    def alive(self):
        try:
            return self.win.winfo_exists()
        except Exception:
            return False


# ─────────────────────────────────────────────
#  Main Application
# ─────────────────────────────────────────────
class AutoClickerApp:
    DEFAULT_HOTKEY_NAME = 'F6'

    def __init__(self):
        self.root = tk.Tk()
        self.root.title('AutoClicker')
        self.root.resizable(False, False)
        self.root.wm_attributes('-topmost', True)

        self.running          = False
        self.hotkey_key       = Key.f6
        self.hotkey_name      = self.DEFAULT_HOTKEY_NAME
        self.capturing_hotkey = False

        self.cps           = tk.IntVar(value=10)
        self.mode          = tk.IntVar(value=1)
        self.mouse_btn_var = tk.StringVar(value='left')

        self.key_seq       = []
        self.capturing_key = False

        self.positions     = []
        self.overlay       = None

        self.mouse_ctrl    = MouseCtrl()
        self.keyboard_ctrl = KeyboardCtrl()
        self._click_thread = None

        self._build_ui()
        self._start_kb_listener()

    # ══════════════════════════════════════════
    #  UI
    # ══════════════════════════════════════════
    def _build_ui(self):
        PAD  = dict(padx=8, pady=4)
        root = self.root

        # Status bar
        self.status_var = tk.StringVar(value='⏹  หยุดทำงาน')
        self.status_lbl = tk.Label(root, textvariable=self.status_var,
                          font=('Arial', 13, 'bold'), fg='#cc0000',
                          bg='#f0f0f0', anchor='center', relief='sunken')
        self.status_lbl.pack(fill='x', ipady=4)

        # Hotkey
        hk = tk.LabelFrame(root, text=' Hotkey เปิด / ปิด ', **PAD)
        hk.pack(fill='x', padx=8, pady=(6, 2))
        self.hk_lbl = tk.Label(hk, text=f'ปุ่ม: {self.hotkey_name}', font=('Arial', 11))
        self.hk_lbl.pack(side='left', padx=6)
        self.hk_btn = tk.Button(hk, text='เปลี่ยนปุ่ม', command=self._capture_hotkey_start)
        self.hk_btn.pack(side='right', padx=6)

        # Speed
        sp = tk.LabelFrame(root, text=' ความเร็ว ', **PAD)
        sp.pack(fill='x', padx=8, pady=2)
        self.speed_lbl = tk.Label(sp, text='')
        self.speed_lbl.pack()
        tk.Scale(sp, from_=1, to=100, orient='horizontal',
                 variable=self.cps, command=self._refresh_speed_lbl,
                 length=280).pack()

        # Tabs
        nb = ttk.Notebook(root)
        nb.pack(fill='both', padx=8, pady=4)
        self.notebook = nb
        self._build_mode1_tab(nb)
        self._build_mode2_tab(nb)
        self._build_mode3_tab(nb)
        nb.bind('<<NotebookTabChanged>>', self._on_tab_change)

        # Toggle button
        self.toggle_btn = tk.Button(root, text='▶  เริ่ม',
                                    font=('Arial', 12, 'bold'),
                                    bg='#28a745', fg='white',
                                    activebackground='#218838',
                                    relief='flat', pady=6,
                                    command=self.toggle)
        self.toggle_btn.pack(fill='x', padx=8, pady=(0, 8))
        self._refresh_speed_lbl()

    def _build_mode1_tab(self, nb):
        f = tk.Frame(nb, padx=8, pady=8)
        nb.add(f, text='  Mode 1: เมาส์  ')
        tk.Label(f, text='คลิกด้วยปุ่ม:', anchor='w').pack(fill='x')
        for text, val in [('ซ้าย (Left)', 'left'), ('ขวา (Right)', 'right'), ('กลาง (Middle)', 'middle')]:
            tk.Radiobutton(f, text=text, variable=self.mouse_btn_var, value=val, anchor='w').pack(fill='x')
        tk.Label(f, text='\n💡 เมาส์จะคลิกตำแหน่งที่ cursor อยู่', fg='gray', font=('Arial', 9)).pack()

    def _build_mode2_tab(self, nb):
        f = tk.Frame(nb, padx=8, pady=8)
        nb.add(f, text='  Mode 2: Keyboard  ')
        tk.Label(f, text='ลำดับปุ่ม (วน Loop):', font=('Arial', 10, 'bold')).pack(anchor='w')
        seq_wrap = tk.Frame(f, bg='#e8e8e8', relief='sunken', bd=1, height=36)
        seq_wrap.pack(fill='x', pady=(2, 4))
        seq_wrap.pack_propagate(False)
        self.seq_frame = seq_wrap
        btn_row = tk.Frame(f)
        btn_row.pack(fill='x')
        tk.Button(btn_row, text='+ เพิ่มปุ่ม', command=self._capture_key_start).pack(side='left', padx=2)
        tk.Button(btn_row, text='− ลบสุดท้าย', command=self._remove_last_key).pack(side='left', padx=2)
        tk.Button(btn_row, text='ล้างทั้งหมด', command=self._clear_keys).pack(side='left', padx=2)
        self.key_hint_lbl = tk.Label(f, text='', fg='#0066cc', font=('Arial', 9, 'italic'))
        self.key_hint_lbl.pack(pady=(4, 0))
        self._refresh_seq_display()

    def _build_mode3_tab(self, nb):
        f = tk.Frame(nb, padx=8, pady=8)
        nb.add(f, text='  Mode 3: หลายตำแหน่ง  ')
        tk.Label(f, text='คลิกหลายตำแหน่งตามลำดับ (Loop)', font=('Arial', 10, 'bold')).pack(anchor='w')
        tk.Label(f, text='กด + เพื่อเพิ่มตำแหน่ง แล้วลากวาง\nบน Overlay ที่ต้องการให้คลิก',
                 fg='gray', font=('Arial', 9)).pack(pady=(0, 4))
        btn_row = tk.Frame(f)
        btn_row.pack()
        tk.Button(btn_row, text='＋ เพิ่มตำแหน่ง', command=self._add_position).pack(side='left', padx=4)
        tk.Button(btn_row, text='－ ลบสุดท้าย', command=self._remove_position).pack(side='left', padx=4)
        tk.Button(btn_row, text='📍 แสดง Overlay', command=self._show_overlay).pack(side='left', padx=4)
        self.pos_lbl = tk.Label(f, text='(ยังไม่มีตำแหน่ง)', fg='gray', font=('Arial', 9))
        self.pos_lbl.pack(pady=(6, 0))

    # ══════════════════════════════════════════
    #  Keyboard listener
    # ══════════════════════════════════════════
    def _start_kb_listener(self):
        def on_press(key):
            if self.capturing_hotkey:
                self.hotkey_key  = key
                self.hotkey_name = key_to_label(key)
                self.capturing_hotkey = False
                self.root.after(0, lambda: [
                    self.hk_lbl.config(text=f'ปุ่ม: {self.hotkey_name}'),
                    self.hk_btn.config(text='เปลี่ยนปุ่ม', state='normal')
                ])
                return
            if self.capturing_key:
                label = key_to_label(key)
                val   = key_to_press_value(key)
                self.key_seq.append((label, val))
                self.capturing_key = False
                self.root.after(0, lambda: [
                    self.key_hint_lbl.config(text=''),
                    self._refresh_seq_display()
                ])
                return
            try:
                if key == self.hotkey_key:
                    self.root.after(0, self.toggle)
            except Exception:
                pass

        self._kb_listener = KbListener(on_press=on_press)
        self._kb_listener.daemon = True
        self._kb_listener.start()

    # ══════════════════════════════════════════
    #  Helpers
    # ══════════════════════════════════════════
    def _capture_hotkey_start(self):
        self.capturing_hotkey = True
        self.hk_lbl.config(text='รอ… กดปุ่มที่ต้องการ')
        self.hk_btn.config(text='รอ...', state='disabled')

    def _refresh_speed_lbl(self, *_):
        cps = self.cps.get()
        ms  = round(1000 / cps)
        self.speed_lbl.config(text=f'{cps} ครั้ง / วินาที  ({ms} ms / ครั้ง)')

    def _on_tab_change(self, _event):
        self.mode.set(self.notebook.index('current') + 1)

    def _capture_key_start(self):
        self.capturing_key = True
        self.key_hint_lbl.config(text='กดปุ่มที่ต้องการเพิ่ม…')

    def _remove_last_key(self):
        if self.key_seq:
            self.key_seq.pop()
            self._refresh_seq_display()

    def _clear_keys(self):
        self.key_seq.clear()
        self._refresh_seq_display()

    def _refresh_seq_display(self):
        for w in self.seq_frame.winfo_children():
            w.destroy()
        if not self.key_seq:
            tk.Label(self.seq_frame, text='(ว่าง)', fg='gray', bg='#e8e8e8').pack(side='left', padx=8, pady=4)
            return
        for i, (label, _) in enumerate(self.key_seq):
            if i:
                tk.Label(self.seq_frame, text='→', bg='#e8e8e8', fg='gray').pack(side='left')
            tk.Label(self.seq_frame, text=f' {label} ', bg='#d0d0d0', relief='raised',
                     font=('Consolas', 10, 'bold'), padx=4, pady=2).pack(side='left', padx=2, pady=3)

    def _add_position(self):
        sw = self.root.winfo_screenwidth()
        sh = self.root.winfo_screenheight()
        offset = len(self.positions) * 40
        self.positions.append([sw // 2 + offset, sh // 2 + offset])
        self._refresh_pos_label()
        self._show_overlay()

    def _remove_position(self):
        if self.positions:
            self.positions.pop()
            self._refresh_pos_label()
            if self.overlay and self.overlay.alive:
                self.overlay.redraw()

    def _refresh_pos_label(self):
        if not self.positions:
            self.pos_lbl.config(text='(ยังไม่มีตำแหน่ง)', fg='gray')
        else:
            lines = [f'#{i+1}: ({x}, {y})' for i, (x, y) in enumerate(self.positions)]
            self.pos_lbl.config(text='\n'.join(lines), fg='black')

    def _show_overlay(self):
        if self.overlay and self.overlay.alive:
            self.overlay.win.lift()
            self.overlay.redraw()
            return
        self.overlay = OverlayWindow(self.root, self.positions, self._refresh_pos_label)

    # ══════════════════════════════════════════
    #  Toggle
    # ══════════════════════════════════════════
    def toggle(self):
        if self.running: self._stop()
        else: self._start()

    def _start(self):
        mode = self.mode.get()
        if mode == 2 and not self.key_seq:
            self.key_hint_lbl.config(text='⚠ กรุณาเพิ่มปุ่มอย่างน้อย 1 ปุ่มก่อน', fg='red')
            return
        if mode == 3 and not self.positions:
            self.pos_lbl.config(text='⚠ กรุณาเพิ่มตำแหน่งอย่างน้อย 1 จุดก่อน', fg='red')
            return
        if mode == 3 and self.overlay and self.overlay.alive:
            self.overlay.hide()
        self.running = True
        self._set_status(True)
        self._click_thread = threading.Thread(target=self._click_loop, daemon=True)
        self._click_thread.start()

    def _stop(self):
        self.running = False
        self._set_status(False)
        if self.mode.get() == 3 and self.overlay and self.overlay.alive:
            self.overlay.show()

    def _set_status(self, running: bool):
        if running:
            self.status_var.set('▶  กำลังทำงาน…')
            self.status_lbl.config(fg='#28a745')
            self.toggle_btn.config(text='⏹  หยุด', bg='#dc3545', activebackground='#c82333')
        else:
            self.status_var.set('⏹  หยุดทำงาน')
            self.status_lbl.config(fg='#cc0000')
            self.toggle_btn.config(text='▶  เริ่ม', bg='#28a745', activebackground='#218838')

    # ══════════════════════════════════════════
    #  Click loop
    # ══════════════════════════════════════════
    def _click_loop(self):
        mode     = self.mode.get()
        interval = 1.0 / self.cps.get()

        if mode == 1:
            btn_map = {'left': Button.left, 'right': Button.right, 'middle': Button.middle}
            btn = btn_map.get(self.mouse_btn_var.get(), Button.left)
            while self.running:
                self.mouse_ctrl.click(btn)
                time.sleep(interval)

        elif mode == 2:
            seq = list(self.key_seq)
            idx = 0
            while self.running:
                _, press_val = seq[idx % len(seq)]
                try:
                    self.keyboard_ctrl.press(press_val)
                    time.sleep(min(0.05, interval * 0.4))
                    self.keyboard_ctrl.release(press_val)
                except Exception:
                    pass
                idx += 1
                time.sleep(interval)

        elif mode == 3:
            positions = [tuple(p) for p in self.positions]
            idx = 0
            while self.running:
                x, y = positions[idx % len(positions)]
                self.mouse_ctrl.position = (int(x), int(y))
                time.sleep(0.02)
                self.mouse_ctrl.click(Button.left)
                idx += 1
                time.sleep(interval)

    def run(self):
        self.root.mainloop()


if __name__ == '__main__':
    app = AutoClickerApp()
    app.run()
