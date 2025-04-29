import tkinter as tk
from tkinter import messagebox, simpledialog, font
import json
import os
import datetime
from win10toast import ToastNotifier
import threading
import time
from tkinter import ttk
import random

class TodoApp:
    def __init__(self, root):
        self.root = root
        self.root.title("モチベーション Todo アプリ")
        self.root.geometry("600x650")
        self.root.resizable(True, True)
        
        # 色の設定
        self.bg_color = "#f5f7fa"
        self.accent_color = "#4a86e8"
        self.completed_color = "#8BC34A"
        self.text_color = "#333333"
        self.root.configure(bg=self.bg_color)
        
        # フォント設定
        self.default_font = font.nametofont("TkDefaultFont")
        self.default_font.configure(family="Yu Gothic UI", size=10)
        
        # スタイル設定
        self.style = ttk.Style()
        self.style.theme_use('clam')
        self.style.configure("TButton", font=("Yu Gothic UI", 10), background=self.accent_color)
        self.style.configure("TFrame", background=self.bg_color)
        self.style.configure("Accent.TButton", background=self.accent_color, foreground="white")
        self.style.map("Accent.TButton", background=[('active', '#3a76d8')])
        
        # データファイルパス
        self.data_file = "todo_data.json"
        
        # 通知用オブジェクト
        self.toaster = ToastNotifier()
        
        # タスクリスト
        self.tasks = []
        self.load_tasks()
        
        # メインフレーム
        self.main_frame = ttk.Frame(root, padding=15)
        self.main_frame.pack(fill=tk.BOTH, expand=True)
        
        # ヘッダーフレーム
        header_frame = ttk.Frame(self.main_frame)
        header_frame.pack(fill=tk.X, pady=(0, 15))
        
        # アプリアイコン（絵文字で代用）
        icon_label = tk.Label(header_frame, text="✅", font=("Segoe UI Emoji", 24), bg=self.bg_color)
        icon_label.pack(side=tk.LEFT, padx=(0, 10))
        
        # タイトル
        title_label = tk.Label(header_frame, text="モチベーションTodo", font=("Yu Gothic UI", 24, "bold"), 
                              fg=self.accent_color, bg=self.bg_color)
        title_label.pack(side=tk.LEFT)

        # 日付表示
        today = datetime.datetime.now().strftime("%Y年%m月%d日 (%a)")
        date_label = tk.Label(header_frame, text=today, font=("Yu Gothic UI", 12), 
                             fg="#666666", bg=self.bg_color)
        date_label.pack(side=tk.RIGHT, padx=5)
        
        # モチベーションカード
        motivation_frame = tk.Frame(self.main_frame, bg="#ffffff", bd=1, relief=tk.SOLID, 
                                  highlightbackground="#dddddd", highlightthickness=1)
        motivation_frame.pack(fill=tk.X, pady=(0, 15), ipady=10)
        
        # モチベーションアイコン
        motiv_icon = tk.Label(motivation_frame, text="💪", font=("Segoe UI Emoji", 18), bg="#ffffff")
        motiv_icon.pack(side=tk.LEFT, padx=(15, 10))
        
        # モチベーションメッセージ
        self.motivation_msg = tk.StringVar()
        self.update_motivation_message()
        motivation_label = tk.Label(motivation_frame, textvariable=self.motivation_msg, 
                                  font=("Yu Gothic UI", 11), fg="#228B22", bg="#ffffff", 
                                  wraplength=500, justify=tk.LEFT)
        motivation_label.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 15))
        
        # 進捗表示フレーム
        progress_frame = ttk.Frame(self.main_frame)
        progress_frame.pack(fill=tk.X, pady=(0, 15))
        
        # 達成率ラベル
        self.progress_percent = tk.StringVar(value="0%")
        progress_label = tk.Label(progress_frame, textvariable=self.progress_percent, 
                                font=("Yu Gothic UI", 12, "bold"), fg=self.accent_color, bg=self.bg_color)
        progress_label.pack(side=tk.LEFT)
        
        # 進捗バー
        self.progress_var = tk.DoubleVar(value=0.0)
        self.style.configure("TProgressbar", thickness=20, background=self.completed_color)
        self.progress_bar = ttk.Progressbar(progress_frame, style="TProgressbar", 
                                          variable=self.progress_var, length=400, mode='determinate')
        self.progress_bar.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=10)
        
        # タスク追加フレーム - 白い背景のカード
        input_card = tk.Frame(self.main_frame, bg="#ffffff", bd=1, relief=tk.SOLID, 
                            highlightbackground="#dddddd", highlightthickness=1)
        input_card.pack(fill=tk.X, pady=(0, 15), ipady=5)
        
        # タスク入力エリア
        input_frame = ttk.Frame(input_card)
        input_frame.pack(fill=tk.X, padx=10, pady=5)
        
        self.task_entry = tk.Entry(input_frame, font=("Yu Gothic UI", 12), width=30, 
                                 bg="#ffffff", fg=self.text_color, insertbackground=self.text_color)
        self.task_entry.pack(side=tk.LEFT, padx=5, expand=True, fill=tk.X)
        self.task_entry.bind("<Return>", lambda e: self.add_task())  # Enter キーでタスク追加
        
        add_button = ttk.Button(input_frame, text="追加", style="Accent.TButton", command=self.add_task)
        add_button.pack(side=tk.LEFT, padx=5)
        
        # タスクリストフレーム - 白い背景のカード
        task_card = tk.Frame(self.main_frame, bg="#ffffff", bd=1, relief=tk.SOLID, 
                           highlightbackground="#dddddd", highlightthickness=1)
        task_card.pack(fill=tk.BOTH, expand=True, pady=(0, 15))
        
        # タスクヘッダー
        task_header = tk.Frame(task_card, bg="#f8f9fa", height=40)
        task_header.pack(fill=tk.X, ipady=5)
        task_header.pack_propagate(False)
        
        task_title = tk.Label(task_header, text="タスク一覧", font=("Yu Gothic UI", 12, "bold"), 
                            bg="#f8f9fa", fg=self.text_color)
        task_title.pack(side=tk.LEFT, padx=15)
        
        # タスクリストキャンバス（スクロール用）
        self.task_canvas = tk.Canvas(task_card, bg="#ffffff", highlightthickness=0)
        self.task_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # スクロールバー
        task_scrollbar = ttk.Scrollbar(task_card, orient=tk.VERTICAL, command=self.task_canvas.yview)
        task_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.task_canvas.configure(yscrollcommand=task_scrollbar.set)
        
        # スクロール可能なフレーム
        self.tasks_frame = tk.Frame(self.task_canvas, bg="#ffffff")
        self.tasks_frame_id = self.task_canvas.create_window((0, 0), window=self.tasks_frame, anchor="nw", tags="tasks_frame")
        
        # キャンバスのリサイズ設定
        self.task_canvas.bind("<Configure>", self.on_canvas_configure)
        self.tasks_frame.bind("<Configure>", self.on_frame_configure)
        
        # ステータスバー
        self.status_var = tk.StringVar()
        self.status_var.set("準備完了")
        status_bar = tk.Label(self.main_frame, textvariable=self.status_var, bd=1, relief=tk.SUNKEN, 
                            anchor=tk.W, font=("Yu Gothic UI", 9), bg="#f0f0f0", fg="#666666")
        status_bar.pack(side=tk.BOTTOM, fill=tk.X)
        
        # タスクの表示を更新
        self.update_task_list()
        
        # リマインダーチェックのスレッド
        reminder_thread = threading.Thread(target=self.check_reminders, daemon=True)
        reminder_thread.start()
        
        # 15分ごとにモチベーションメッセージを更新
        self.root.after(900000, self.update_motivation_message)
        
        # アプリ終了時の処理
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
    
    def on_canvas_configure(self, event):
        """キャンバスサイズ変更時の処理"""
        self.task_canvas.itemconfig(self.tasks_frame_id, width=event.width)
    
    def on_frame_configure(self, event):
        """タスクフレームサイズ変更時のスクロール領域更新"""
        self.task_canvas.configure(scrollregion=self.task_canvas.bbox("all"))
    
    def update_motivation_message(self):
        """モチベーションメッセージをランダムに更新"""
        messages = [
            "小さな一歩が、大きな成果につながります！",
            "今日の努力は、明日の自分への最高の贈り物です",
            "一度にすべてをする必要はありません。一つずつ進めましょう",
            "できないと思うことは、単にまだやり方を見つけていないだけです",
            "困難なことほど達成した時の喜びは大きいものです",
            "完璧を目指すよりも、前進することに集中しましょう",
            "継続は力なり。小さな進歩も積み重なれば大きな変化になります",
            "目標達成へのカギは、小さな勝利を重ねること",
            "自分を信じれば、不可能も可能になります",
            "一日一日が新しいチャンス。今日を大切に"
        ]
        self.motivation_msg.set(random.choice(messages))
        # 次回の更新をスケジュール
        self.root.after(900000, self.update_motivation_message)
    
    def load_tasks(self):
        """タスクデータをJSONファイルから読み込む"""
        if os.path.exists(self.data_file):
            try:
                with open(self.data_file, 'r', encoding='utf-8') as f:
                    self.tasks = json.load(f)
            except:
                self.tasks = []
        else:
            self.tasks = []
    
    def save_tasks(self):
        """タスクデータをJSONファイルに保存する"""
        with open(self.data_file, 'w', encoding='utf-8') as f:
            json.dump(self.tasks, f, ensure_ascii=False, indent=2)
    
    def update_task_list(self):
        """タスク表示を更新"""
        # 既存のタスク表示をクリア
        for widget in self.tasks_frame.winfo_children():
            widget.destroy()
        
        # タスクがない場合の表示
        if not self.tasks:
            empty_label = tk.Label(self.tasks_frame, text="タスクがありません。新しいタスクを追加しましょう！", 
                                 font=("Yu Gothic UI", 11), fg="#999999", bg="#ffffff")
            empty_label.pack(pady=20)
            self.progress_var.set(0)
            self.progress_percent.set("0%")
            self.status_var.set("タスクなし")
            return
        
        # タスクの表示
        completed_count = 0
        
        for i, task in enumerate(self.tasks):
            # タスク行フレーム
            task_row = tk.Frame(self.tasks_frame, bg="#ffffff")
            task_row.pack(fill=tk.X, pady=2)
            
            # チェックボックス変数
            var = tk.BooleanVar(value=task["completed"])
            
            # チェックボックス
            cb = tk.Checkbutton(task_row, variable=var, onvalue=True, offvalue=False, 
                              bg="#ffffff", activebackground="#ffffff",
                              command=lambda idx=i, v=var: self.toggle_task(idx, v.get()))
            cb.pack(side=tk.LEFT, padx=(10, 5))
            
            # タスクテキスト
            if task["completed"]:
                task_text = tk.Label(task_row, text=task["title"], font=("Yu Gothic UI", 11), 
                                  fg="#999999", bg="#ffffff", wraplength=400, justify=tk.LEFT)
                task_text.config(font=("Yu Gothic UI", 11, "overstrike"))  # 取り消し線
                completed_count += 1
            else:
                task_text = tk.Label(task_row, text=task["title"], font=("Yu Gothic UI", 11), 
                                  fg=self.text_color, bg="#ffffff", wraplength=400, justify=tk.LEFT)
            
            task_text.pack(side=tk.LEFT, fill=tk.X, expand=True, anchor="w")
            
            # リマインダーアイコン（設定されている場合）
            if "reminder" in task and not task["completed"]:
                reminder_time = datetime.datetime.fromisoformat(task["reminder"])
                time_str = reminder_time.strftime("%H:%M")
                
                reminder_frame = tk.Frame(task_row, bg="#ffffff")
                reminder_frame.pack(side=tk.LEFT, padx=5)
                
                reminder_icon = tk.Label(reminder_frame, text="⏰", font=("Segoe UI Emoji", 11), 
                                      bg="#ffffff", fg="#FF7043")
                reminder_icon.pack(side=tk.LEFT)
                
                time_label = tk.Label(reminder_frame, text=time_str, font=("Yu Gothic UI", 10), 
                                    bg="#ffffff", fg="#FF7043")
                time_label.pack(side=tk.LEFT, padx=(2, 0))
            
            # 操作ボタンフレーム
            action_frame = tk.Frame(task_row, bg="#ffffff")
            action_frame.pack(side=tk.RIGHT, padx=5)
            
            # リマインダーボタン（未完了タスクのみ）
            if not task["completed"]:
                reminder_btn = tk.Button(action_frame, text="⏰", font=("Segoe UI Emoji", 11), 
                                       bg="#ffffff", bd=0, highlightthickness=0, 
                                       activebackground="#f0f0f0", cursor="hand2",
                                       command=lambda idx=i: self.set_reminder(idx))
                reminder_btn.pack(side=tk.LEFT, padx=2)
            
            # 削除ボタン
            delete_btn = tk.Button(action_frame, text="🗑️", font=("Segoe UI Emoji", 11), 
                                 bg="#ffffff", bd=0, highlightthickness=0, 
                                 activebackground="#f0f0f0", cursor="hand2",
                                 command=lambda idx=i: self.delete_task(idx))
            delete_btn.pack(side=tk.LEFT, padx=2)
            
            # 区切り線
            if i < len(self.tasks) - 1:
                separator = ttk.Separator(self.tasks_frame, orient="horizontal")
                separator.pack(fill=tk.X, pady=5, padx=10)
        
        # 進捗バーとステータスの更新
        total_tasks = len(self.tasks)
        progress = 0 if total_tasks == 0 else completed_count / total_tasks
        self.progress_var.set(progress)
        self.progress_percent.set(f"{int(progress*100)}%")
        
        # ステータスバーの更新
        self.status_var.set(f"タスク: {total_tasks}個 / 完了: {completed_count}個 / 未完了: {total_tasks - completed_count}個")
    
    def toggle_task(self, index, is_completed):
        """タスクの完了状態を切り替え"""
        if index < len(self.tasks):
            # 完了状態を変更
            self.tasks[index]["completed"] = is_completed
            
            if is_completed:
                # 完了にした場合
                self.tasks[index]["completed_at"] = datetime.datetime.now().isoformat()
                self.show_notification("タスク完了！", f"「{self.tasks[index]['title']}」を完了しました。素晴らしい！")
                
                # リマインダーがあれば削除
                if "reminder" in self.tasks[index]:
                    self.tasks[index].pop("reminder")
            else:
                # 未完了に戻した場合
                if "completed_at" in self.tasks[index]:
                    self.tasks[index].pop("completed_at")
            
            self.save_tasks()
            self.update_task_list()
    
    def add_task(self):
        """新しいタスクを追加"""
        task_title = self.task_entry.get().strip()
        if task_title:
            new_task = {
                "title": task_title,
                "completed": False,
                "created_at": datetime.datetime.now().isoformat()
            }
            self.tasks.append(new_task)
            self.save_tasks()
            self.update_task_list()
            self.task_entry.delete(0, tk.END)
            self.show_notification("新しいタスクを追加しました", f"「{task_title}」が追加されました。頑張りましょう！")
    
    def delete_task(self, index):
        """タスクを削除"""
        if index < len(self.tasks):
            task_title = self.tasks[index]["title"]
            confirm = messagebox.askyesno("確認", f"「{task_title}」を削除してもよろしいですか？")
            if confirm:
                del self.tasks[index]
                self.save_tasks()
                self.update_task_list()
                self.status_var.set(f"「{task_title}」を削除しました")
    
    def set_reminder(self, index):
        """タスクにリマインダーを設定"""
        if index < len(self.tasks) and not self.tasks[index]["completed"]:
            # 時間入力ダイアログ
            time_str = simpledialog.askstring("リマインダー", 
                                           "時間を入力してください (HH:MM):",
                                           parent=self.root)
            if time_str:
                try:
                    # 入力された時間を解析
                    hour, minute = map(int, time_str.split(':'))
                    now = datetime.datetime.now()
                    reminder_time = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
                    
                    # 設定時間が過去の場合は翌日にする
                    if reminder_time < now:
                        reminder_time += datetime.timedelta(days=1)
                        
                    self.tasks[index]["reminder"] = reminder_time.isoformat()
                    self.save_tasks()
                    self.update_task_list()
                    self.status_var.set(f"「{self.tasks[index]['title']}」のリマインダーを {reminder_time.strftime('%H:%M')} に設定しました")
                except:
                    messagebox.showerror("エラー", "正しい時間形式（HH:MM）で入力してください")
    
    def check_reminders(self):
        """定期的にリマインダーをチェックして通知を表示"""
        while True:
            now = datetime.datetime.now()
            for task in self.tasks:
                if not task["completed"] and "reminder" in task:
                    reminder_time = datetime.datetime.fromisoformat(task["reminder"])
                    # 現在時刻とリマインダー時刻の差が1分以内なら通知
                    time_diff = abs((reminder_time - now).total_seconds())
                    if time_diff <= 60:
                        self.show_notification("タスクリマインダー", 
                                            f"「{task['title']}」の時間です。取り組みましょう！", 
                                            duration=10)
                        # リマインダーを削除（一度だけ通知）
                        task.pop("reminder", None)
                        self.save_tasks()
                        # UI更新はメインスレッドで行う
                        self.root.after(0, self.update_task_list)
            time.sleep(30)  # 30秒ごとにチェック
    
    def show_notification(self, title, message, duration=5):
        """Windows通知を表示"""
        try:
            self.toaster.show_toast(
                title,
                message,
                duration=duration,
                threaded=True  # 非同期で表示
            )
        except Exception as e:
            print(f"通知エラー: {e}")
    
    def on_closing(self):
        """アプリ終了時の処理"""
        self.save_tasks()
        self.root.destroy()

if __name__ == "__main__":
    # アプリケーション起動
    root = tk.Tk()
    app = TodoApp(root)
    root.mainloop()