import tkinter as tk
from tkinter import messagebox, simpledialog
import json
import os
import datetime
from win10toast import ToastNotifier
import threading
import time
from tkinter import ttk

class TodoApp:
    def __init__(self, root):
        self.root = root
        self.root.title("モチベーション Todo アプリ")
        self.root.geometry("500x600")
        self.root.resizable(True, True)
        
        # 色の設定
        self.bg_color = "#f0f0f0"
        self.accent_color = "#4a86e8"
        self.root.configure(bg=self.bg_color)
        
        # スタイル設定
        self.style = ttk.Style()
        self.style.configure("TButton", font=("Yu Gothic UI", 10), background=self.accent_color)
        self.style.configure("TFrame", background=self.bg_color)
        
        # データファイルパス
        self.data_file = "todo_data.json"
        
        # 通知用オブジェクト
        self.toaster = ToastNotifier()
        
        # タスクリスト
        self.tasks = []
        self.load_tasks()
        
        # メインフレーム
        main_frame = ttk.Frame(root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # タイトル
        title_label = tk.Label(main_frame, text="今日のタスク", font=("Yu Gothic UI", 18, "bold"), bg=self.bg_color)
        title_label.pack(pady=10)

        # モチベーションメッセージ
        self.motivation_msg = tk.StringVar()
        self.update_motivation_message()
        motivation_label = tk.Label(main_frame, textvariable=self.motivation_msg, font=("Yu Gothic UI", 10), fg="#228B22", bg=self.bg_color, wraplength=450)
        motivation_label.pack(pady=5)
        
        # 進捗バー
        self.progress_var = tk.DoubleVar(value=0.0)
        self.progress_bar = ttk.Progressbar(main_frame, variable=self.progress_var, length=400)
        self.progress_bar.pack(pady=10)
        
        # タスク入力フレーム
        input_frame = ttk.Frame(main_frame)
        input_frame.pack(fill=tk.X, pady=10)
        
        self.task_entry = tk.Entry(input_frame, font=("Yu Gothic UI", 12), width=30)
        self.task_entry.pack(side=tk.LEFT, padx=5, expand=True, fill=tk.X)
        
        add_button = ttk.Button(input_frame, text="タスク追加", command=self.add_task)
        add_button.pack(side=tk.LEFT, padx=5)
        
        # タスクリストフレーム
        task_frame = ttk.Frame(main_frame)
        task_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        
        self.task_listbox = tk.Listbox(task_frame, font=("Yu Gothic UI", 12), selectbackground=self.accent_color, 
                                    activestyle="none", height=10)
        self.task_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        scrollbar = ttk.Scrollbar(task_frame, orient=tk.VERTICAL, command=self.task_listbox.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.task_listbox.config(yscrollcommand=scrollbar.set)
        
        # ボタンフレーム
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=10)
        
        complete_button = ttk.Button(button_frame, text="完了にする", command=self.complete_task)
        complete_button.pack(side=tk.LEFT, padx=5)
        
        delete_button = ttk.Button(button_frame, text="削除", command=self.delete_task)
        delete_button.pack(side=tk.LEFT, padx=5)
        
        set_reminder_button = ttk.Button(button_frame, text="リマインダー設定", command=self.set_reminder)
        set_reminder_button.pack(side=tk.LEFT, padx=5)
        
        # ステータスバー
        self.status_var = tk.StringVar()
        self.status_var.set("準備完了")
        status_bar = tk.Label(main_frame, textvariable=self.status_var, bd=1, relief=tk.SUNKEN, anchor=tk.W)
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
    
    def update_motivation_message(self):
        """モチベーションメッセージをランダムに更新"""
        messages = [
            "小さな一歩が、大きな成果につながります！",
            "今日の努力は、明日の自分への最高の贈り物です",
            "一度にすべてをする必要はありません。一つずつ進めましょう",
            "できないと思うことは、単にまだやり方を見つけていないだけです",
            "困難なことほど達成した時の喜びは大きいものです",
            "完璧を目指すよりも、前進することに集中しましょう",
            "継続は力なり。小さな進歩も積み重なれば大きな変化になります"
        ]
        import random
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
        """リストボックスのタスク表示を更新"""
        self.task_listbox.delete(0, tk.END)
        completed_count = 0
        
        for task in self.tasks:
            status = "【完了】" if task["completed"] else "[ ]"
            task_text = f"{status} {task['title']}"
            if "reminder" in task and not task["completed"]:
                reminder_time = datetime.datetime.fromisoformat(task["reminder"])
                task_text += f" (⏰ {reminder_time.strftime('%H:%M')})"
            
            self.task_listbox.insert(tk.END, task_text)
            
            if task["completed"]:
                completed_count += 1
        
        # 進捗バーの更新
        total_tasks = len(self.tasks)
        progress = 0 if total_tasks == 0 else completed_count / total_tasks
        self.progress_var.set(progress)
        
        # ステータスバーの更新
        if total_tasks > 0:
            self.status_var.set(f"タスク: {total_tasks}個 / 完了: {completed_count}個 / 達成率: {int(progress*100)}%")
        else:
            self.status_var.set("タスクがありません。新しいタスクを追加しましょう！")
    
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
    
    def complete_task(self):
        """選択したタスクを完了状態に設定"""
        selected_idx = self.task_listbox.curselection()
        if selected_idx:
            idx = selected_idx[0]
            if not self.tasks[idx]["completed"]:
                self.tasks[idx]["completed"] = True
                self.tasks[idx]["completed_at"] = datetime.datetime.now().isoformat()
                self.save_tasks()
                self.update_task_list()
                self.show_notification("タスク完了！", f"「{self.tasks[idx]['title']}」を完了しました。素晴らしい！")
    
    def delete_task(self):
        """選択したタスクを削除"""
        selected_idx = self.task_listbox.curselection()
        if selected_idx:
            idx = selected_idx[0]
            task_title = self.tasks[idx]["title"]
            confirm = messagebox.askyesno("確認", f"「{task_title}」を削除してもよろしいですか？")
            if confirm:
                del self.tasks[idx]
                self.save_tasks()
                self.update_task_list()
                self.status_var.set(f"「{task_title}」を削除しました")
    
    def set_reminder(self):
        """選択したタスクにリマインダーを設定"""
        selected_idx = self.task_listbox.curselection()
        if selected_idx:
            idx = selected_idx[0]
            if not self.tasks[idx]["completed"]:
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
                            
                        self.tasks[idx]["reminder"] = reminder_time.isoformat()
                        self.save_tasks()
                        self.update_task_list()
                        self.status_var.set(f"「{self.tasks[idx]['title']}」のリマインダーを {reminder_time.strftime('%H:%M')} に設定しました")
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