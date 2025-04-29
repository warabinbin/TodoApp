import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import json
import os
from datetime import datetime, timedelta
import threading
import time
from win10toast import ToastNotifier

class TodoApp:
    def __init__(self, root):
        self.root = root
        self.root.title("ToDo アプリ")
        self.root.geometry("600x500")
        
        # Windows通知の初期化
        self.toaster = ToastNotifier()
        
        # タスクリスト
        self.tasks = []
        
        # カテゴリのリスト（初期値）
        self.categories = ["仕事", "家事", "趣味", "勉強", "その他"]
        
        # 優先度のリスト
        self.priorities = ["高", "中", "低"]
        
        # タスクデータのロード
        self.load_tasks()
        
        # UIの設定
        self.setup_ui()
        
        # リマインダースレッド
        self.reminder_active = True
        self.reminder_thread = threading.Thread(target=self.check_reminders)
        self.reminder_thread.daemon = True
        self.reminder_thread.start()
        
        # クローズ時の処理
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

    def setup_ui(self):
        # フレームの作成
        input_frame = ttk.Frame(self.root, padding=10)
        input_frame.pack(fill=tk.X)
        
        button_frame = ttk.Frame(self.root, padding=10)
        button_frame.pack(fill=tk.X)
        
        list_frame = ttk.Frame(self.root, padding=10)
        list_frame.pack(fill=tk.BOTH, expand=True)
        
        # タスク入力欄
        ttk.Label(input_frame, text="新しいタスク:").grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)
        self.task_entry = ttk.Entry(input_frame, width=30)
        self.task_entry.grid(row=0, column=1, padx=5, pady=5, sticky=tk.W)
        
        # カテゴリ選択
        ttk.Label(input_frame, text="カテゴリ:").grid(row=0, column=2, padx=5, pady=5, sticky=tk.W)
        self.category_var = tk.StringVar()
        self.category_var.set(self.categories[0])
        self.category_combobox = ttk.Combobox(input_frame, textvariable=self.category_var, values=self.categories, width=10)
        self.category_combobox.grid(row=0, column=3, padx=5, pady=5, sticky=tk.W)
        
        # 優先度選択
        ttk.Label(input_frame, text="優先度:").grid(row=0, column=4, padx=5, pady=5, sticky=tk.W)
        self.priority_var = tk.StringVar()
        self.priority_var.set(self.priorities[1])  # デフォルトは「中」
        self.priority_combobox = ttk.Combobox(input_frame, textvariable=self.priority_var, values=self.priorities, width=5)
        self.priority_combobox.grid(row=0, column=5, padx=5, pady=5, sticky=tk.W)
        
        # ボタン
        ttk.Button(button_frame, text="追加", command=self.add_task).grid(row=0, column=0, padx=5, pady=5)
        ttk.Button(button_frame, text="削除", command=self.delete_task).grid(row=0, column=1, padx=5, pady=5)
        ttk.Button(button_frame, text="完了", command=self.complete_task).grid(row=0, column=2, padx=5, pady=5)
        ttk.Button(button_frame, text="リマインド設定", command=self.set_reminder).grid(row=0, column=3, padx=5, pady=5)
        ttk.Button(button_frame, text="すべて表示", command=self.show_all_tasks).grid(row=0, column=4, padx=5, pady=5)
        ttk.Button(button_frame, text="未完了のみ", command=self.show_active_tasks).grid(row=0, column=5, padx=5, pady=5)
        ttk.Button(button_frame, text="完了済のみ", command=self.show_completed_tasks).grid(row=0, column=6, padx=5, pady=5)
        ttk.Button(button_frame, text="カテゴリ管理", command=self.manage_categories).grid(row=0, column=7, padx=5, pady=5)
        
        # フィルター用のフレーム
        filter_frame = ttk.Frame(self.root, padding=10)
        filter_frame.pack(fill=tk.X)
        
        # カテゴリでフィルター
        ttk.Label(filter_frame, text="カテゴリでフィルター:").grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)
        self.filter_category_var = tk.StringVar()
        self.filter_category_var.set("すべて")
        filter_categories = ["すべて"] + self.categories
        self.filter_category_combobox = ttk.Combobox(filter_frame, textvariable=self.filter_category_var, 
                                                    values=filter_categories, width=10)
        self.filter_category_combobox.grid(row=0, column=1, padx=5, pady=5, sticky=tk.W)
        self.filter_category_combobox.bind("<<ComboboxSelected>>", lambda e: self.apply_filters())
        
        # 優先度でフィルター
        ttk.Label(filter_frame, text="優先度でフィルター:").grid(row=0, column=2, padx=5, pady=5, sticky=tk.W)
        self.filter_priority_var = tk.StringVar()
        self.filter_priority_var.set("すべて")
        filter_priorities = ["すべて"] + self.priorities
        self.filter_priority_combobox = ttk.Combobox(filter_frame, textvariable=self.filter_priority_var, 
                                                   values=filter_priorities, width=5)
        self.filter_priority_combobox.grid(row=0, column=3, padx=5, pady=5, sticky=tk.W)
        self.filter_priority_combobox.bind("<<ComboboxSelected>>", lambda e: self.apply_filters())
        
        # タスク一覧
        columns = ('id', 'title', 'category', 'priority', 'status', 'created_at', 'reminder')
        self.tree = ttk.Treeview(list_frame, columns=columns, show='headings')
        
        # 列の設定
        self.tree.heading('id', text='ID')
        self.tree.heading('title', text='タスク')
        self.tree.heading('category', text='カテゴリ')
        self.tree.heading('priority', text='優先度')
        self.tree.heading('status', text='状態')
        self.tree.heading('created_at', text='作成日時')
        self.tree.heading('reminder', text='リマインド')
        
        self.tree.column('id', width=40, anchor=tk.CENTER)
        self.tree.column('title', width=180)
        self.tree.column('category', width=70, anchor=tk.CENTER)
        self.tree.column('priority', width=50, anchor=tk.CENTER)
        self.tree.column('status', width=50, anchor=tk.CENTER)
        self.tree.column('created_at', width=100, anchor=tk.CENTER)
        self.tree.column('reminder', width=100, anchor=tk.CENTER)
        
        # スクロールバー
        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscroll=scrollbar.set)
        
        # 配置
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # タスクの表示
        self.display_tasks()
        
        # Enterキーでタスク追加
        self.task_entry.bind('<Return>', lambda event: self.add_task())

    def load_tasks(self):
        # タスクデータのロード
        try:
            if os.path.exists('tasks.json'):
                with open('tasks.json', 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.tasks = data.get('tasks', [])
                    # 保存されているカテゴリをロード（もし存在すれば）
                    if 'categories' in data:
                        self.categories = data['categories']
        except Exception as e:
            messagebox.showerror("エラー", f"タスクのロード中にエラーが発生しました: {e}")
            self.tasks = []

    def save_tasks(self):
        # タスクデータの保存
        try:
            with open('tasks.json', 'w', encoding='utf-8') as f:
                data = {
                    'tasks': self.tasks,
                    'categories': self.categories
                }
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            messagebox.showerror("エラー", f"タスクの保存中にエラーが発生しました: {e}")

    def display_tasks(self, filter_status=None):
        # タスク一覧のクリア
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        # フィルター条件の取得
        filter_category = self.filter_category_var.get()
        filter_priority = self.filter_priority_var.get()
        
        # タスクの表示
        for task in self.tasks:
            # ステータスフィルター
            if filter_status is not None and task['status'] != filter_status:
                continue
            
            # カテゴリフィルター
            if filter_category != "すべて" and task['category'] != filter_category:
                continue
                
            # 優先度フィルター
            if filter_priority != "すべて" and task['priority'] != filter_priority:
                continue
                
            # タスクの追加
            self.tree.insert('', tk.END, values=(
                task['id'],
                task['title'],
                task['category'],
                task['priority'],
                '完了' if task['status'] == 'completed' else '未完了',
                task['created_at'],
                task.get('reminder', '未設定')
            ))
            
        # 優先度に応じて行の色を変更
        for item in self.tree.get_children():
            task_id = self.tree.item(item, 'values')[0]
            task = next((t for t in self.tasks if t['id'] == int(task_id)), None)
            if task:
                if task['priority'] == '高':
                    self.tree.item(item, tags=('high_priority',))
                elif task['priority'] == '中':
                    self.tree.item(item, tags=('medium_priority',))
                elif task['priority'] == '低':
                    self.tree.item(item, tags=('low_priority',))
                    
        # タグの設定
        self.tree.tag_configure('high_priority', background='#ffcccc')
        self.tree.tag_configure('medium_priority', background='#ffffcc')
        self.tree.tag_configure('low_priority', background='#ccffcc')

    def add_task(self):
        # タスクの追加
        title = self.task_entry.get().strip()
        if not title:
            messagebox.showwarning("警告", "タスクを入力してください")
            return
        
        category = self.category_var.get()
        priority = self.priority_var.get()
        
        # IDの生成（最大ID + 1）
        task_id = 1
        if self.tasks:
            task_id = max([task['id'] for task in self.tasks]) + 1
            
        # 現在の日時を取得
        now = datetime.now().strftime('%Y-%m-%d %H:%M')
        
        # タスクの追加
        task = {
            'id': task_id,
            'title': title,
            'category': category,
            'priority': priority,
            'status': 'active',
            'created_at': now,
            'reminder': '未設定'
        }
        
        self.tasks.append(task)
        self.save_tasks()
        self.display_tasks()
        
        # 通知
        notification_title = "新しいタスクが追加されました"
        notification_message = f"タスク: {title}\nカテゴリ: {category}\n優先度: {priority}"
        self.toaster.show_toast(notification_title, notification_message, duration=5, threaded=True)
        
        # 入力欄のクリア
        self.task_entry.delete(0, tk.END)

    def delete_task(self):
        # タスクの削除
        selected_items = self.tree.selection()
        if not selected_items:
            messagebox.showwarning("警告", "削除するタスクを選択してください")
            return
            
        if messagebox.askyesno("確認", "選択したタスクを削除しますか？"):
            for item in selected_items:
                values = self.tree.item(item, 'values')
                task_id = int(values[0])  # 文字列から整数に変換
                task_title = values[1]
                
                # 該当するタスクを削除
                for i, task in enumerate(self.tasks):
                    if task['id'] == task_id:
                        del self.tasks[i]
                        
                        # 通知
                        notification_title = "タスクが削除されました"
                        notification_message = f"タスク「{task_title}」を削除しました。"
                        self.toaster.show_toast(notification_title, notification_message, duration=5, threaded=True)
                        break
                
            self.save_tasks()
            self.display_tasks()

    def complete_task(self):
        # タスクの完了
        selected_items = self.tree.selection()
        if not selected_items:
            messagebox.showwarning("警告", "完了するタスクを選択してください")
            return
            
        for item in selected_items:
            values = self.tree.item(item, 'values')
            task_id = int(values[0])
            task_title = values[1]
            for task in self.tasks:
                if task['id'] == task_id:
                    # ステータスの切り替え
                    new_status = 'completed' if task['status'] == 'active' else 'active'
                    task['status'] = new_status
                    
                    # 通知
                    if new_status == 'completed':
                        notification_title = "タスクが完了しました"
                        notification_message = f"タスク「{task_title}」を完了しました。"
                    else:
                        notification_title = "タスクが未完了に戻されました"
                        notification_message = f"タスク「{task_title}」を未完了に戻しました。"
                        
                    self.toaster.show_toast(notification_title, notification_message, duration=5, threaded=True)
                    break
                    
        self.save_tasks()
        self.display_tasks()

    def show_all_tasks(self):
        # すべてのタスクを表示
        self.display_tasks()

    def show_active_tasks(self):
        # 未完了のタスクのみ表示
        self.display_tasks('active')

    def show_completed_tasks(self):
        # 完了済のタスクのみ表示
        self.display_tasks('completed')
        
    def apply_filters(self):
        # フィルターの適用
        self.display_tasks()
        
    def manage_categories(self):
        # カテゴリ管理ダイアログ
        category_window = tk.Toplevel(self.root)
        category_window.title("カテゴリ管理")
        category_window.geometry("300x400")
        category_window.transient(self.root)
        category_window.grab_set()
        
        # カテゴリリストのフレーム
        list_frame = ttk.Frame(category_window, padding=10)
        list_frame.pack(fill=tk.BOTH, expand=True)
        
        # カテゴリリスト
        self.category_listbox = tk.Listbox(list_frame, width=20, height=10)
        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.category_listbox.yview)
        self.category_listbox.configure(yscrollcommand=scrollbar.set)
        
        self.category_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # カテゴリの表示
        for category in self.categories:
            self.category_listbox.insert(tk.END, category)
        
        # 操作ボタンのフレーム
        button_frame = ttk.Frame(category_window, padding=10)
        button_frame.pack(fill=tk.X)
        
        # カテゴリ追加
        ttk.Label(button_frame, text="新しいカテゴリ:").grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)
        self.new_category_entry = ttk.Entry(button_frame, width=15)
        self.new_category_entry.grid(row=0, column=1, padx=5, pady=5, sticky=tk.W)
        
        ttk.Button(button_frame, text="追加", command=self.add_category).grid(row=0, column=2, padx=5, pady=5)
        ttk.Button(button_frame, text="削除", command=self.delete_category).grid(row=1, column=0, padx=5, pady=5)
        ttk.Button(button_frame, text="閉じる", command=category_window.destroy).grid(row=1, column=2, padx=5, pady=5)

    def add_category(self):
        # カテゴリの追加
        new_category = self.new_category_entry.get().strip()
        if not new_category:
            messagebox.showwarning("警告", "カテゴリ名を入力してください")
            return
            
        if new_category in self.categories:
            messagebox.showwarning("警告", "同じ名前のカテゴリが既に存在します")
            return
            
        self.categories.append(new_category)
        self.category_listbox.insert(tk.END, new_category)
        self.new_category_entry.delete(0, tk.END)
        
        # コンボボックスの更新
        self.category_combobox['values'] = self.categories
        filter_categories = ["すべて"] + self.categories
        self.filter_category_combobox['values'] = filter_categories
        
        self.save_tasks()

    def delete_category(self):
        # カテゴリの削除
        selected = self.category_listbox.curselection()
        if not selected:
            messagebox.showwarning("警告", "削除するカテゴリを選択してください")
            return
            
        category = self.category_listbox.get(selected[0])
        
        # 使用中のカテゴリかどうかチェック
        in_use = any(task['category'] == category for task in self.tasks)
        if in_use:
            if not messagebox.askyesno("確認", f"カテゴリ「{category}」は使用中です。削除すると関連タスクのカテゴリが「その他」に変更されます。続行しますか？"):
                return
                
            # タスクのカテゴリを変更
            for task in self.tasks:
                if task['category'] == category:
                    task['category'] = "その他"
        
        # カテゴリの削除
        self.categories.remove(category)
        self.category_listbox.delete(selected[0])
        
        # コンボボックスの更新
        self.category_combobox['values'] = self.categories
        filter_categories = ["すべて"] + self.categories
        self.filter_category_combobox['values'] = filter_categories
        
        # もしカテゴリリストが空なら「その他」を追加
        if not self.categories:
            self.categories.append("その他")
            self.category_listbox.insert(tk.END, "その他")
            self.category_combobox['values'] = self.categories
        
        self.save_tasks()
        self.display_tasks()
        
    def on_close(self):
        # アプリケーション終了時の処理
        self.reminder_active = False  # リマインダースレッドを停止
        self.root.destroy()
        
    def set_reminder(self):
        # リマインドを設定
        selected_items = self.tree.selection()
        if not selected_items:
            messagebox.showwarning("警告", "リマインドを設定するタスクを選択してください")
            return
        
        # 選択されたタスクを取得
        item = selected_items[0]  # 最初の選択項目のみ処理
        values = self.tree.item(item, 'values')
        task_id = int(values[0])
        task_title = values[1]
        
        # リマインド設定ダイアログ
        reminder_window = tk.Toplevel(self.root)
        reminder_window.title("リマインド設定")
        reminder_window.geometry("300x200")
        reminder_window.transient(self.root)
        reminder_window.grab_set()
        
        # リマインド時間設定フレーム
        frame = ttk.Frame(reminder_window, padding=10)
        frame.pack(fill=tk.BOTH, expand=True)
        
        # ラベル
        ttk.Label(frame, text=f"タスク: {task_title}").grid(row=0, column=0, columnspan=2, padx=5, pady=5, sticky=tk.W)
        
        # 時間設定
        ttk.Label(frame, text="何分後にリマインドしますか？").grid(row=1, column=0, columnspan=2, padx=5, pady=5, sticky=tk.W)
        
        minutes_var = tk.IntVar(value=30)
        minutes_options = [5, 10, 15, 30, 60]
        minutes_combobox = ttk.Combobox(frame, textvariable=minutes_var, values=minutes_options, width=5)
        minutes_combobox.grid(row=2, column=0, padx=5, pady=5, sticky=tk.W)
        ttk.Label(frame, text="分後").grid(row=2, column=1, padx=5, pady=5, sticky=tk.W)
        
        # ボタン
        def set_reminder_for_task():
            minutes = minutes_var.get()
            
            # 現在時刻を取得
            now = datetime.now()
            
            # リマインド時刻を計算
            reminder_time = now + timedelta(minutes=minutes)
            reminder_time_str = reminder_time.strftime('%Y-%m-%d %H:%M')
            
            # タスクのリマインド時刻を設定
            for task in self.tasks:
                if task['id'] == task_id:
                    task['reminder'] = reminder_time_str
                    break
            
            # 保存と表示の更新
            self.save_tasks()
            self.display_tasks()
            
            # 通知
            notification_title = "リマインドが設定されました"
            notification_message = f"タスク「{task_title}」のリマインドを{reminder_time_str}に設定しました。"
            self.toaster.show_toast(notification_title, notification_message, duration=5, threaded=True)
            
            reminder_window.destroy()
        
        ttk.Button(frame, text="設定", command=set_reminder_for_task).grid(row=3, column=0, padx=5, pady=20)
        ttk.Button(frame, text="キャンセル", command=reminder_window.destroy).grid(row=3, column=1, padx=5, pady=20)
        
    def check_reminders(self):
        # 定期的にリマインドをチェック
        while self.reminder_active:
            current_time = datetime.now()
            current_time_str = current_time.strftime('%Y-%m-%d %H:%M')
            
            # 全タスクをチェック
            for task in self.tasks:
                if task['status'] == 'active' and 'reminder' in task and task['reminder'] != '未設定':
                    reminder_time = task['reminder']
                    
                    # 現在時刻がリマインド時刻と一致または過ぎた場合
                    if current_time_str >= reminder_time:
                        # 通知
                        notification_title = "リマインド: タスクの時間です"
                        notification_message = f"タスク「{task['title']}」の時間になりました。\nカテゴリ: {task['category']}\n優先度: {task['priority']}"
                        self.toaster.show_toast(notification_title, notification_message, duration=10, threaded=True)
                        
                        # リマインドをリセット
                        task['reminder'] = '未設定'
                        self.save_tasks()
                        
                        # UIを更新（メインスレッドで実行）
                        self.root.after(0, self.display_tasks)
            
            # 1分ごとにチェック
            time.sleep(60)

if __name__ == "__main__":
    root = tk.Tk()
    app = TodoApp(root)
    root.mainloop()