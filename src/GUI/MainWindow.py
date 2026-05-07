
import tkinter as tk
from tkinter import ttk, messagebox, font as tkfont

from src.model.process import Process
from src.scheduler.RoundRobin import round_robin_scheduler
from src.scheduler.SRTF import srtf_scheduler
from src.metrics.calculator import averages_from_metrics
from src.util.InputValidator import validate_quantum, ValidationError


# ─────────────────────────────────────────────────────────────────────────────
# Constants
# ─────────────────────────────────────────────────────────────────────────────

COLORS = {
    'bg_dark':        '#0a0e27',
    'bg_medium':      '#141834',
    'bg_light':       '#1a1f3e',
    'bg_card':        '#1e2348',
    'accent_primary': '#6c63ff',
    'accent_cyan':    '#00d2ff',
    'accent_green':   '#28a745',
    'accent_warning': '#ff9800',
    'accent_danger':  '#dc3545',
    'text_primary':   '#ffffff',
    'text_secondary': '#b0b3c9',
    'text_muted':     '#6c7293',
}

GANTT_COLORS = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4',
                '#FFEAA7', '#DDA0DD', '#98D8C8', '#F7B731',
                '#a29bfe', '#fd79a8']


# ─────────────────────────────────────────────────────────────────────────────
# Main Application Class
# ─────────────────────────────────────────────────────────────────────────────

class SchedulerGUI:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Process Scheduler Comparison — Round Robin vs SRTF")
        self.root.geometry("1600x900")
        self.root.minsize(1200, 750)
        self.root.configure(bg=COLORS['bg_dark'])

        # App state
        self.processes:      list[Process] = []
        self.current_quantum: int          = 2

        self._setup_fonts()
        self._setup_styles()
        self._build_ui()

    # ══════════════════════════════════════════════════════════════════════════
    # Setup
    # ══════════════════════════════════════════════════════════════════════════

    def _setup_fonts(self):
        self.fonts = {
            'title':      tkfont.Font(family='Segoe UI', size=18, weight='bold'),
            'heading':    tkfont.Font(family='Segoe UI', size=14, weight='bold'),
            'subheading': tkfont.Font(family='Segoe UI', size=12, weight='bold'),
            'body':       tkfont.Font(family='Segoe UI', size=11),
            'body_bold':  tkfont.Font(family='Segoe UI', size=11, weight='bold'),
            'large':      tkfont.Font(family='Segoe UI', size=13, weight='bold'),
            'button':     tkfont.Font(family='Segoe UI', size=11, weight='bold'),
            'gantt':      tkfont.Font(family='Segoe UI', size=10),
            'mono':       tkfont.Font(family='Consolas', size=11),
        }

    def _setup_styles(self):
        s = ttk.Style()
        s.theme_use('clam')

        s.configure("Dark.Treeview",
                    background=COLORS['bg_light'], foreground=COLORS['text_primary'],
                    fieldbackground=COLORS['bg_light'], rowheight=30,
                    font=self.fonts['body'])
        s.configure("Dark.Treeview.Heading",
                    background=COLORS['accent_primary'], foreground=COLORS['text_primary'],
                    font=self.fonts['body_bold'], relief='flat')
        s.map("Dark.Treeview.Heading",
              background=[('active', COLORS['accent_cyan'])])
        s.map("Dark.Treeview",
              background=[('selected', COLORS['accent_primary'])],
              foreground=[('selected', COLORS['text_primary'])])

        s.configure("Dark.TNotebook", background=COLORS['bg_dark'], borderwidth=0)
        s.configure("Dark.TNotebook.Tab",
                    background=COLORS['bg_medium'], foreground=COLORS['text_primary'],
                    padding=[16, 8], font=self.fonts['body_bold'])
        s.map("Dark.TNotebook.Tab",
              background=[('selected', COLORS['accent_primary']),
                          ('active',   COLORS['accent_cyan'])])

    # ══════════════════════════════════════════════════════════════════════════
    # UI construction
    # ══════════════════════════════════════════════════════════════════════════

    def _build_ui(self):
        # Header
        self._build_header()

        # Main split: left input | right results
        paned = tk.PanedWindow(self.root, bg=COLORS['bg_dark'],
                               orient=tk.HORIZONTAL, sashwidth=5)
        paned.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))

        left = tk.Frame(paned, bg=COLORS['bg_dark'])
        paned.add(left, width=420)

        right = tk.Frame(paned, bg=COLORS['bg_dark'])
        paned.add(right)

        self._build_left(left)
        self._build_right(right)

    # ── Header ────────────────────────────────────────────────────────────────

    def _build_header(self):
        hdr = tk.Frame(self.root, bg=COLORS['bg_medium'], height=80)
        hdr.pack(fill=tk.X)
        hdr.pack_propagate(False)

        left_hdr = tk.Frame(hdr, bg=COLORS['bg_medium'])
        left_hdr.pack(side=tk.LEFT, padx=20, pady=12)

        tk.Label(left_hdr, text="PROCESS SCHEDULER COMPARISON",
                 font=self.fonts['title'], fg=COLORS['accent_cyan'],
                 bg=COLORS['bg_medium']).pack(anchor='w')
        tk.Label(left_hdr, text="Round Robin  vs  Shortest Remaining Time First (SRTF)",
                 font=self.fonts['body'], fg=COLORS['text_secondary'],
                 bg=COLORS['bg_medium']).pack(anchor='w')

        right_hdr = tk.Frame(hdr, bg=COLORS['bg_medium'])
        right_hdr.pack(side=tk.RIGHT, padx=20, pady=12)

        self._status_lbl = tk.Label(right_hdr, text="Ready to simulate",
                                    font=self.fonts['body_bold'],
                                    fg=COLORS['accent_green'],
                                    bg=COLORS['bg_medium'])
        self._status_lbl.pack()

        self._proc_count_lbl = tk.Label(right_hdr, text="Processes: 0",
                                        font=self.fonts['body'],
                                        fg=COLORS['text_secondary'],
                                        bg=COLORS['bg_medium'])
        self._proc_count_lbl.pack()

    # ── Left panel ────────────────────────────────────────────────────────────

    def _build_left(self, parent):
        canvas = tk.Canvas(parent, bg=COLORS['bg_dark'], highlightthickness=0)
        sb     = ttk.Scrollbar(parent, orient=tk.VERTICAL, command=canvas.yview)
        inner  = tk.Frame(canvas, bg=COLORS['bg_dark'])

        inner.bind("<Configure>", lambda e: canvas.configure(
            scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=inner, anchor="nw", width=400)
        canvas.configure(yscrollcommand=sb.set)

        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        sb.pack(side=tk.RIGHT, fill=tk.Y)

        self._build_input_card(inner)
        self._build_quantum_card(inner)
        self._build_process_list_card(inner)
        self._build_control_card(inner)

    def _build_input_card(self, parent):
        card = self._card(parent, "INPUT PANEL")

        self._pid_entry     = self._field(card, "Process ID",  "1")
        self._arrival_entry = self._field(card, "Arrival Time", "0")
        self._burst_entry   = self._field(card, "Burst Time",  "5")

        self._btn(card, "ADD PROCESS", self._add_process,
                  COLORS['accent_primary']).pack(pady=10)

    def _build_quantum_card(self, parent):
        card = self._card(parent, "ROUND ROBIN — TIME QUANTUM")

        row = tk.Frame(card, bg=COLORS['bg_card'])
        row.pack(fill=tk.X, padx=15, pady=10)

        tk.Label(row, text="Time Quantum (q):", font=self.fonts['body_bold'],
                 fg=COLORS['text_primary'], bg=COLORS['bg_card']).pack(side=tk.LEFT)

        self._quantum_entry = tk.Entry(row, font=self.fonts['large'], width=8,
                                       bg=COLORS['bg_light'], fg=COLORS['text_primary'],
                                       insertbackground=COLORS['accent_cyan'],
                                       relief=tk.FLAT, bd=4)
        self._quantum_entry.insert(0, "2")
        self._quantum_entry.pack(side=tk.LEFT, padx=(12, 0))

        tk.Label(card,
                 text="Small q → more fairness / better RT\n"
                      "Large q → closer to FCFS behaviour",
                 font=self.fonts['body'], fg=COLORS['text_muted'],
                 bg=COLORS['bg_card'], justify=tk.LEFT).pack(
                     anchor='w', padx=15, pady=(0, 10))

    def _build_process_list_card(self, parent):
        card = self._card(parent, "PROCESS LIST")

        tf = tk.Frame(card, bg=COLORS['bg_card'])
        tf.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        sb = ttk.Scrollbar(tf)
        sb.pack(side=tk.RIGHT, fill=tk.Y)

        self._proc_tree = ttk.Treeview(
            tf, columns=('PID', 'AT', 'BT'), show='headings',
            style="Dark.Treeview", yscrollcommand=sb.set, height=7)
        self._proc_tree.heading('PID', text='Process ID')
        self._proc_tree.heading('AT',  text='Arrival Time')
        self._proc_tree.heading('BT',  text='Burst Time')
        for col in ('PID', 'AT', 'BT'):
            self._proc_tree.column(col, width=110, anchor='center')
        self._proc_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        sb.config(command=self._proc_tree.yview)

        self._btn(card, "REMOVE SELECTED", self._remove_selected,
                  COLORS['text_muted']).pack(pady=(0, 8))

    def _build_control_card(self, parent):
        card = self._card(parent, "CONTROL PANEL")
        bf   = tk.Frame(card, bg=COLORS['bg_card'])
        bf.pack(fill=tk.X, padx=15, pady=12)

        self._btn(bf, "RUN SIMULATION", self._run_simulation,
                  COLORS['accent_green']).pack(fill=tk.X, pady=5)
        self._btn(bf, "LOAD SAMPLE DATA", self._load_sample,
                  COLORS['accent_primary']).pack(fill=tk.X, pady=5)
        self._btn(bf, "CLEAR ALL", self._clear_all,
                  COLORS['accent_danger']).pack(fill=tk.X, pady=5)

    # ── Right panel (notebook) ────────────────────────────────────────────────

    def _build_right(self, parent):
        self._nb = ttk.Notebook(parent, style="Dark.TNotebook")
        self._nb.pack(fill=tk.BOTH, expand=True)

        self._build_rr_tab()
        self._build_srtf_tab()
        self._build_comparison_tab()

    def _build_rr_tab(self):
        frame = tk.Frame(self._nb, bg=COLORS['bg_dark'])
        self._nb.add(frame, text="  ROUND ROBIN  ")

        # Ready-queue indicator
        qcard = self._card(frame, "READY QUEUE")
        self._rr_queue_lbl = tk.Label(qcard, text="Ready Queue: (empty)",
                                      font=self.fonts['body_bold'],
                                      fg=COLORS['accent_green'],
                                      bg=COLORS['bg_card'])
        self._rr_queue_lbl.pack(pady=10)

        # Gantt
        gc = self._card(frame, "GANTT CHART — ROUND ROBIN")
        self._rr_canvas = self._gantt_canvas(gc)

        # Results table
        rc = self._card(frame, "RESULTS TABLE — ROUND ROBIN")
        self._rr_tree, self._rr_avg_lbl = self._results_table(rc)

    def _build_srtf_tab(self):
        frame = tk.Frame(self._nb, bg=COLORS['bg_dark'])
        self._nb.add(frame, text="  SRTF  ")

        gc = self._card(frame, "GANTT CHART — SRTF")
        self._srtf_canvas = self._gantt_canvas(gc)

        rc = self._card(frame, "RESULTS TABLE — SRTF")
        self._srtf_tree, self._srtf_avg_lbl = self._results_table(rc)

    def _build_comparison_tab(self):
        outer = tk.Frame(self._nb, bg=COLORS['bg_dark'])
        self._nb.add(outer, text="  COMPARISON & ANALYSIS  ")

        # ── Scrollable canvas wrapper ──────────────────────────────────────
        vbar  = tk.Scrollbar(outer, orient=tk.VERTICAL)
        vbar.pack(side=tk.RIGHT, fill=tk.Y)

        scroll_cv = tk.Canvas(outer, bg=COLORS['bg_dark'],
                              highlightthickness=0,
                              yscrollcommand=vbar.set)
        scroll_cv.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        vbar.config(command=scroll_cv.yview)

        # Inner frame that holds all content
        frame = tk.Frame(scroll_cv, bg=COLORS['bg_dark'])
        frame_id = scroll_cv.create_window((0, 0), window=frame, anchor='nw')

        def _on_frame_configure(e):
            scroll_cv.configure(scrollregion=scroll_cv.bbox('all'))
        def _on_canvas_configure(e):
            scroll_cv.itemconfig(frame_id, width=e.width)

        frame.bind('<Configure>', _on_frame_configure)
        scroll_cv.bind('<Configure>', _on_canvas_configure)

        # Mouse-wheel scrolling
        def _on_mousewheel(e):
            scroll_cv.yview_scroll(int(-1 * (e.delta / 120)), 'units')
        scroll_cv.bind_all('<MouseWheel>', _on_mousewheel)

        # ── Performance metrics table ──────────────────────────────────────
        mc = self._card(frame, "PERFORMANCE METRICS COMPARISON")
        mf = tk.Frame(mc, bg=COLORS['bg_card'])
        mf.pack(fill=tk.X, padx=15, pady=12)

        headers = ["Metric", "Round Robin", "SRTF", "Better"]
        for col, h in enumerate(headers):
            tk.Label(mf, text=h, font=self.fonts['subheading'],
                     fg=COLORS['accent_cyan'], bg=COLORS['bg_card']).grid(
                row=0, column=col, padx=20, pady=8, sticky='w')

        self._cmp_labels = {}
        rows = [("Avg Waiting Time", "WT"),
                ("Avg Turnaround Time", "TAT"),
                ("Avg Response Time", "RT")]
        for i, (label, key) in enumerate(rows, 1):
            tk.Label(mf, text=label, font=self.fonts['body_bold'],
                     fg=COLORS['text_primary'], bg=COLORS['bg_card']).grid(
                row=i, column=0, padx=20, pady=6, sticky='w')

            rr_lbl = tk.Label(mf, text="--", font=self.fonts['mono'],
                              fg=COLORS['accent_cyan'], bg=COLORS['bg_card'])
            rr_lbl.grid(row=i, column=1, padx=20, pady=6, sticky='w')

            st_lbl = tk.Label(mf, text="--", font=self.fonts['mono'],
                              fg=COLORS['accent_cyan'], bg=COLORS['bg_card'])
            st_lbl.grid(row=i, column=2, padx=20, pady=6, sticky='w')

            winner_lbl = tk.Label(mf, text="--", font=self.fonts['body_bold'],
                                  fg=COLORS['accent_green'], bg=COLORS['bg_card'])
            winner_lbl.grid(row=i, column=3, padx=20, pady=6, sticky='w')

            self._cmp_labels[key] = (rr_lbl, st_lbl, winner_lbl)

        # ── Fairness analysis ──────────────────────────────────────────────
        fc = self._card(frame, "FAIRNESS & ALGORITHM ANALYSIS")
        ff = tk.Frame(fc, bg=COLORS['bg_card'])
        ff.pack(fill=tk.X, padx=15, pady=12)

        for label, attr in [("Round Robin:", '_rr_fairness_lbl'),
                              ("SRTF:",        '_srtf_fairness_lbl')]:
            row = tk.Frame(ff, bg=COLORS['bg_light'])
            row.pack(fill=tk.X, pady=5)
            tk.Label(row, text=label, font=self.fonts['body_bold'],
                     fg=COLORS['accent_cyan'], bg=COLORS['bg_light'],
                     width=14, anchor='w').pack(side=tk.LEFT, padx=10, pady=8)
            lbl = tk.Label(row, text="—", font=self.fonts['body'],
                           fg=COLORS['text_primary'], bg=COLORS['bg_light'],
                           wraplength=700, justify=tk.LEFT)
            lbl.pack(side=tk.LEFT, padx=10, pady=8, fill=tk.X, expand=True)
            setattr(self, attr, lbl)

        # ── Quantum effect ─────────────────────────────────────────────────
        qc = self._card(frame, "QUANTUM EFFECT ANALYSIS")
        self._quantum_analysis_lbl = tk.Label(
            qc, text="Set quantum and run simulation to see analysis.",
            font=self.fonts['body'], fg=COLORS['text_muted'],
            bg=COLORS['bg_card'], wraplength=850, justify=tk.LEFT)
        self._quantum_analysis_lbl.pack(anchor='w', padx=15, pady=12)

        # ── Recommendation ─────────────────────────────────────────────────
        # Custom card with gradient-like layered design
        rec_outer = tk.Frame(frame, bg='#2d1b4e', relief=tk.RAISED, bd=0)   # deep violet bg
        rec_outer.pack(fill=tk.X, pady=6, padx=4)

        # Coloured left accent bar (3-colour split to feel like a badge)
        accent_bar = tk.Frame(rec_outer, width=6, bg='#c084fc')             # soft purple
        accent_bar.pack(side=tk.LEFT, fill=tk.Y)

        rec_inner = tk.Frame(rec_outer, bg='#2d1b4e')
        rec_inner.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Title row with icon
        title_row = tk.Frame(rec_inner, bg='#3b2060')
        title_row.pack(fill=tk.X)
        tk.Label(title_row, text="  RECOMMENDATION",
                 font=self.fonts['subheading'],
                 fg='#e9d5ff',                                               # lavender
                 bg='#3b2060').pack(side=tk.LEFT, padx=12, pady=6)

        # Text body — multi-line, clearly visible
        self._recommendation_lbl = tk.Label(
            rec_inner,
            text="Run a simulation to see recommendations.",
            font=self.fonts['body'],
            fg='#f0e6ff',                                                    # very light lavender
            bg='#2d1b4e',
            wraplength=850,
            justify=tk.LEFT,
            anchor='w')
        self._recommendation_lbl.pack(anchor='w', padx=18, pady=14, fill=tk.X)

    # ══════════════════════════════════════════════════════════════════════════
    # Widget factory helpers
    # ══════════════════════════════════════════════════════════════════════════

    def _card(self, parent, title: str) -> tk.Frame:
        outer = tk.Frame(parent, bg=COLORS['bg_card'], relief=tk.RAISED, bd=0)
        outer.pack(fill=tk.X, pady=6, padx=4)

        title_bar = tk.Frame(outer, bg=COLORS['accent_primary'], height=32)
        title_bar.pack(fill=tk.X)
        title_bar.pack_propagate(False)
        tk.Label(title_bar, text=title, font=self.fonts['subheading'],
                 fg=COLORS['text_primary'], bg=COLORS['accent_primary']).pack(
                     side=tk.LEFT, padx=12, pady=4)
        return outer

    def _field(self, parent, label: str, placeholder: str) -> tk.Entry:
        row = tk.Frame(parent, bg=COLORS['bg_card'])
        row.pack(fill=tk.X, padx=15, pady=6)
        tk.Label(row, text=label + ":", font=self.fonts['body_bold'],
                 fg=COLORS['text_primary'], bg=COLORS['bg_card'],
                 width=14, anchor='w').pack(side=tk.LEFT)
        entry = tk.Entry(row, font=self.fonts['body'], bg=COLORS['bg_light'],
                         fg=COLORS['text_primary'],
                         insertbackground=COLORS['accent_cyan'],
                         relief=tk.FLAT, bd=4)
        entry.insert(0, placeholder)
        entry.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=(8, 0))
        return entry

    def _btn(self, parent, text: str, cmd, color: str) -> tk.Button:
        return tk.Button(parent, text=text, font=self.fonts['button'],
                         bg=color, fg=COLORS['text_primary'],
                         activebackground=COLORS['accent_cyan'],
                         activeforeground=COLORS['text_primary'],
                         relief=tk.FLAT, cursor='hand2',
                         command=cmd, padx=12, pady=6)

    def _gantt_canvas(self, parent) -> tk.Canvas:
        wrapper = tk.Frame(parent, bg='#1a1a2e', height=120)
        wrapper.pack(fill=tk.X, padx=10, pady=10)
        wrapper.pack_propagate(False)
        # xscrollbar so long charts are scrollable
        xbar = tk.Scrollbar(wrapper, orient=tk.HORIZONTAL)
        xbar.pack(side=tk.BOTTOM, fill=tk.X)
        cvs = tk.Canvas(wrapper, bg='#1a1a2e', highlightthickness=0,
                        xscrollcommand=xbar.set)
        cvs.pack(fill=tk.BOTH, expand=True)
        xbar.config(command=cvs.xview)
        return cvs

    def _results_table(self, parent):
        tf = tk.Frame(parent, bg=COLORS['bg_card'])
        tf.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        sb_y = ttk.Scrollbar(tf)
        sb_y.pack(side=tk.RIGHT, fill=tk.Y)
        sb_x = ttk.Scrollbar(tf, orient=tk.HORIZONTAL)
        sb_x.pack(side=tk.BOTTOM, fill=tk.X)

        tree = ttk.Treeview(tf, columns=('PID', 'WT', 'TAT', 'RT'),
                             show='headings', style="Dark.Treeview",
                             yscrollcommand=sb_y.set,
                             xscrollcommand=sb_x.set, height=5)
        tree.heading('PID', text='Process')
        tree.heading('WT',  text='Waiting Time')
        tree.heading('TAT', text='Turnaround Time')
        tree.heading('RT',  text='Response Time')
        for col in ('PID', 'WT', 'TAT', 'RT'):
            tree.column(col, width=130, anchor='center')
        tree.pack(fill=tk.BOTH, expand=True)
        sb_y.config(command=tree.yview)
        sb_x.config(command=tree.xview)

        avg_lbl = tk.Label(parent, text="", font=self.fonts['body_bold'],
                           fg=COLORS['accent_green'], bg=COLORS['bg_card'])
        avg_lbl.pack(pady=8)
        return tree, avg_lbl

    # ══════════════════════════════════════════════════════════════════════════
    # Process management
    # ══════════════════════════════════════════════════════════════════════════

    def _add_process(self):
        pid     = self._pid_entry.get().strip()
        arr_str = self._arrival_entry.get().strip()
        bst_str = self._burst_entry.get().strip()

        if not pid:
            messagebox.showerror("Validation Error", "Process ID cannot be empty.")
            return
        
         # PID must be a positive integer
        if not pid.isdigit():
           messagebox.showerror("Validation Error","Process ID must be a positive integer." )
           return

        if int(pid) <= 0:
            messagebox.showerror("Validation Error", "Process ID must be greater than zero.")
            return
    
        if any(p.pid == pid for p in self.processes):
            messagebox.showerror("Validation Error",
                                 f"Process '{pid}' already exists. IDs must be unique.")
            return
        try:
            arr = int(arr_str)
            bst = int(bst_str)
        except ValueError:
            messagebox.showerror("Validation Error",
                                 "Arrival and Burst times must be whole numbers.")
            return
        if arr < 0:
            messagebox.showerror("Validation Error", "Arrival time must be ≥ 0.")
            return
        if bst <= 0:
            messagebox.showerror("Validation Error", "Burst time must be > 0.")
            return

        p = Process(pid, arr, bst)
        self.processes.append(p)
        self._proc_tree.insert('', 'end', values=(pid, arr, bst))
        self._proc_count_lbl.config(text=f"Processes: {len(self.processes)}")
        self._rr_queue_lbl.config(
            text="Ready Queue: " + " → ".join(p.pid for p in self.processes))

        # Clear entries
        for entry, default in [(self._pid_entry, ""), (self._arrival_entry, ""),
                                (self._burst_entry, "")]:
            entry.delete(0, tk.END)
            entry.insert(0, default)

        self._set_status("Process added.", COLORS['accent_green'])

    def _remove_selected(self):
        sel = self._proc_tree.selection()
        if not sel:
            messagebox.showinfo("Remove", "Select a process in the list first.")
            return
        for item in sel:
            idx = self._proc_tree.index(item)
            self._proc_tree.delete(item)
            if 0 <= idx < len(self.processes):
                self.processes.pop(idx)
        self._proc_count_lbl.config(text=f"Processes: {len(self.processes)}")

    def _load_sample(self):
        self._clear_all()
        sample = [("P1", 0, 6), ("P2", 1, 4), ("P3", 2, 2),
                  ("P4", 3, 8), ("P5", 4, 3)]
        for pid, arr, bst in sample:
            p = Process(pid, arr, bst)
            self.processes.append(p)
            self._proc_tree.insert('', 'end', values=(pid, arr, bst))
        self._quantum_entry.delete(0, tk.END)
        self._quantum_entry.insert(0, "3")
        self._proc_count_lbl.config(text=f"Processes: {len(self.processes)}")
        self._rr_queue_lbl.config(
            text="Ready Queue: " + " → ".join(p.pid for p in self.processes))
        self._set_status("Sample data loaded.", COLORS['accent_cyan'])

    def _clear_all(self):
        self.processes.clear()
        for tree in (self._proc_tree, self._rr_tree, self._srtf_tree):
            for item in tree.get_children():
                tree.delete(item)
        for cvs in (self._rr_canvas, self._srtf_canvas):
            cvs.delete("all")
        self._rr_avg_lbl.config(text="")
        self._srtf_avg_lbl.config(text="")
        self._rr_queue_lbl.config(text="Ready Queue: (empty)")
        self._proc_count_lbl.config(text="Processes: 0")
        self._quantum_entry.delete(0, tk.END)
        self._quantum_entry.insert(0, "2")

        for key in self._cmp_labels:
            rr_l, st_l, w_l = self._cmp_labels[key]
            rr_l.config(text="--")
            st_l.config(text="--")
            w_l.config(text="--", fg=COLORS['accent_green'])

        self._rr_fairness_lbl.config(text="—")
        self._srtf_fairness_lbl.config(text="—")
        self._quantum_analysis_lbl.config(
            text="Set quantum and run simulation to see analysis.",
            fg=COLORS['text_muted'])
        self._recommendation_lbl.config(
            text="Run a simulation to see recommendations.")
        self._set_status("All data cleared.", COLORS['accent_warning'])

    # ══════════════════════════════════════════════════════════════════════════
    # Simulation
    # ══════════════════════════════════════════════════════════════════════════

    def _run_simulation(self):
        if len(self.processes) < 2:
            messagebox.showwarning("Not Enough Processes",
                                   "Please add at least 2 processes.")
            return

        # Validate quantum using InputValidator
        try:
            q = validate_quantum(self._quantum_entry.get().strip())
        except ValidationError as e:
            messagebox.showerror("Invalid Quantum", str(e))
            return

        self.current_quantum = q

        # ── Call the external schedulers ──────────────────────────────────
        rr_gantt,   rr_metrics   = round_robin_scheduler(self.processes, q)
        srtf_gantt, srtf_metrics = srtf_scheduler(self.processes)

        # ── Update Gantt charts ───────────────────────────────────────────
        self._draw_gantt(self._rr_canvas,   rr_gantt)
        self._draw_gantt(self._srtf_canvas, srtf_gantt)

        # ── Update metrics tables ─────────────────────────────────────────
        self._fill_results(self._rr_tree,   self._rr_avg_lbl,   rr_metrics)
        self._fill_results(self._srtf_tree, self._srtf_avg_lbl, srtf_metrics)

        # ── Update comparison tab ─────────────────────────────────────────
        self._update_comparison(rr_metrics, srtf_metrics)

        # Ready queue label
        self._rr_queue_lbl.config(
            text="Ready Queue: " + " → ".join(p.pid for p in self.processes))

        self._set_status("Simulation complete!", COLORS['accent_green'])

    # ══════════════════════════════════════════════════════════════════════════
    # Gantt chart drawing
    # ══════════════════════════════════════════════════════════════════════════

    def _draw_gantt(self, canvas: tk.Canvas, gantt: list):
        """Schedule the actual drawing after the canvas is fully laid out."""
        canvas.delete("all")
        if not gantt:
            canvas.create_text(400, 80, text="No data — run the simulation first.",
                               font=self.fonts['body'], fill=COLORS['text_muted'])
            return
        # Delay until the canvas has its real size from the geometry manager
        canvas.after(50, lambda: self._do_draw_gantt(canvas, gantt))

    def _do_draw_gantt(self, canvas: tk.Canvas, gantt: list):
        """Actual drawing — called after the canvas width is known."""
        canvas.delete("all")

        # Force geometry update so winfo_width() is accurate
        canvas.update_idletasks()
        w = canvas.winfo_width()

        # Fallback: walk up to the parent notebook tab for its width
        if w < 200:
            w = canvas.winfo_toplevel().winfo_width() - 450  # subtract left panel
        w = max(w, 600)  # absolute minimum

        max_time = max(end for _, _, end in gantt)
        if max_time <= 0:
            return

        # Leave 50px left margin and 30px right margin
        usable_w = w - 80
        scale    = usable_w / max_time

        # Enforce a minimum cell width of 40px per time unit — use scrollable canvas if needed
        MIN_CELL = 40
        if scale < MIN_CELL:
            scale   = MIN_CELL
            total_w = 80 + int(max_time * scale)
            canvas.config(scrollregion=(0, 0, total_w, 160))
        else:
            canvas.config(scrollregion=(0, 0, w, 160))

        y  = 18   # top of bar
        bh = 55   # bar height
        color_map = {}

        for (pid, start, end) in gantt:
            if pid not in color_map:
                color_map[pid] = GANTT_COLORS[len(color_map) % len(GANTT_COLORS)]

            x1  = 40 + start * scale
            x2  = 40 + end   * scale
            col = color_map[pid] if pid != "Idle" else '#444466'

            # Shadow rectangle for depth
            canvas.create_rectangle(x1 + 3, y + 3, x2 + 1, y + bh + 1,
                                    fill='#111133', outline='')
            # Main bar
            canvas.create_rectangle(x1, y, x2 - 1, y + bh,
                                    fill=col, outline='#0a0e27', width=2)

            # PID label inside bar (always show — clip with canvas if needed)
            label_text = str(pid)
            canvas.create_text((x1 + x2) / 2, y + bh / 2,
                               text=label_text, font=self.fonts['body_bold'],
                               fill='white', anchor='center')

        # ── Time axis ────────────────────────────────────────────────────────
        axis_y = y + bh + 6
        seen_x: set = set()

        for (pid, start, end) in gantt:
            for t in (start, end):
                x = 40 + t * scale
                rx = round(x)
                if rx not in seen_x:
                    seen_x.add(rx)
                    # Tick line
                    canvas.create_line(x, axis_y, x, axis_y + 8,
                                       fill=COLORS['text_secondary'], width=1)
                    # Time label
                    canvas.create_text(x, axis_y + 10, text=str(t),
                                       font=self.fonts['gantt'],
                                       fill=COLORS['text_secondary'], anchor='n')

    # ══════════════════════════════════════════════════════════════════════════
    # Results table
    # ══════════════════════════════════════════════════════════════════════════

    def _fill_results(self, tree: ttk.Treeview, avg_lbl: tk.Label, metrics: dict):
        for item in tree.get_children():
            tree.delete(item)
        for pid, data in sorted(metrics.items()):
            tree.insert('', 'end', values=(pid, data['WT'], data['TAT'], data['RT']))

        # Use calculator module for averages
        avgs = averages_from_metrics(metrics)
        avg_lbl.config(
            text=f"Averages   WT: {avgs['WT']}   TAT: {avgs['TAT']}   RT: {avgs['RT']}")

    # ══════════════════════════════════════════════════════════════════════════
    # Comparison tab update
    # ══════════════════════════════════════════════════════════════════════════

    def _update_comparison(self, rr_metrics: dict, srtf_metrics: dict):
        rr_avg  = averages_from_metrics(rr_metrics)
        st_avg  = averages_from_metrics(srtf_metrics)

        for key, (rr_l, st_l, w_l) in self._cmp_labels.items():
            rv = rr_avg[key]
            sv = st_avg[key]
            rr_l.config(text=str(rv))
            st_l.config(text=str(sv))
            if rv < sv:
                winner, col = "Round Robin", COLORS['accent_warning']
            elif sv < rv:
                winner, col = "SRTF",        COLORS['accent_green']
            else:
                winner, col = "Tie",         COLORS['text_secondary']
            w_l.config(text=winner, fg=col)

        # Fairness analysis
        rr_wt, st_wt = rr_avg['WT'], st_avg['WT']
        if rr_wt <= st_wt:
            rr_fair = (f"Provides equal or better waiting time ({rr_wt} vs {st_wt}). "
                       "Guarantees every process gets CPU — no starvation.")
            st_fair = (f"Higher waiting time ({st_wt} vs {rr_wt}). "
                       "May starve long-burst processes when short ones keep arriving.")
        else:
            rr_fair = (f"Waiting time {rr_wt} (vs SRTF {st_wt}). "
                       "Ensures fair CPU distribution — no starvation.")
            st_fair = (f"Lower waiting time ({st_wt} vs {rr_wt}). "
                       "Optimal for minimising average WT but may cause starvation.")

        self._rr_fairness_lbl.config(text=rr_fair)
        self._srtf_fairness_lbl.config(text=st_fair)

        # Quantum effect
        q = self.current_quantum
        if q <= 2:
            qtext = (f"Small quantum (q={q}) → very high responsiveness and fairness, "
                     "but frequent context switches increase overhead.")
        elif q <= 5:
            qtext = (f"Moderate quantum (q={q}) → balanced trade-off between "
                     "responsiveness and context-switch overhead.")
        else:
            qtext = (f"Large quantum (q={q}) → Round Robin behaves closer to FCFS. "
                     "Less overhead but worse response time for waiting processes.")
        self._quantum_analysis_lbl.config(text=qtext, fg=COLORS['text_primary'])

        # Recommendation
        if st_wt < rr_wt and st_avg['TAT'] < rr_avg['TAT']:
            rec = ("RECOMMENDATION: Use SRTF for throughput-oriented / batch systems.\n"
                   "Lower waiting and turnaround times.\n"
                   "Use Round Robin for interactive / time-sharing systems "
                   "where fairness and bounded response time matter.")
        elif rr_avg['RT'] < st_avg['RT']:
            rec = ("RECOMMENDATION: Use Round Robin for interactive systems.\n"
                   f"Better response time ({rr_avg['RT']} vs {st_avg['RT']}).\n"
                   "Fair CPU distribution prevents starvation.")
        else:
            rec = ("RECOMMENDATION: Both algorithms perform similarly on this workload.\n"
                   f"Round Robin (q={q}) is preferred for its predictability and "
                   "starvation-free behaviour.")
        self._recommendation_lbl.config(text=rec)

    # ══════════════════════════════════════════════════════════════════════════
    # Utilities
    # ══════════════════════════════════════════════════════════════════════════

    def _set_status(self, msg: str, color: str = COLORS['accent_green']):
        self._status_lbl.config(text=msg, fg=color)
        self.root.after(3000, lambda: self._status_lbl.config(
            text="Ready to simulate", fg=COLORS['accent_green']))


# ─────────────────────────────────────────────────────────────────────────────
# Entry point
# ─────────────────────────────────────────────────────────────────────────────

def main():
    root = tk.Tk()
    app  = SchedulerGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()