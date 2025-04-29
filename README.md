# TodoApp

[![Python 3.12](https://img.shields.io/badge/python-3.12-blue)](https://www.python.org/)  
[![License: MIT](https://img.shields.io/badge/license-MIT-green)](LICENSE)

---

## 概要

Windows 向けに作成された、Python 製のシンプルなコマンドライン Todo アプリケーションです。  
タスクの追加・表示・削除を行い、Windows の通知機能でリマインドします。  
タスクデータは JSON ファイルに保存され、再起動後も保持されます。

---

## 特徴

- シンプルな Python 実装  
- タスクの追加 / 表示 / 削除  
- Windows 通知機能（`win10toast`）  
- JSON ファイルによるローカル保存  

---

## 動作環境

- OS：Windows 10 / 11  
- Python：3.12  

---

## セットアップ手順

### 1. リポジトリをクローン

```bash
git clone https://github.com/warabinbin/TodoApp.git
cd TodoApp
