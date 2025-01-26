import customtkinter as ctk
import telebot
import threading
import datetime
import traceback
import time
from tkinter import Toplevel, messagebox, filedialog, Menu, Text, END, Scrollbar
import queue
import json
import os
import re
import inspect


class CommandManager:
    def __init__(self):
        self.commands = {}

    def add_command(self, command, response):
        self.commands[command] = response

    def remove_command(self, command):
        if command in self.commands:
            del self.commands[command]

    def edit_command(self, old_command, new_command, new_response):
        if old_command in self.commands:
            del self.commands[old_command]
            self.commands[new_command] = new_response

    def get_commands(self):
        return self.commands

    def load_commands(self, data):
        self.commands = data

    def get_data(self):
        return self.commands

    def save_commands(self, filename):
        with open(filename, "w") as f:
            json.dump(self.commands, f)


class BotApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("BackBots")
        self.geometry("1280x720")
        self.is_running = False
        self.bot = None
        self.command_manager = CommandManager()
        self.command_manager.load_commands({})
        self.selected_command = None
        self.queue = queue.Queue()
        self.command_buttons = {}
        self.bot_token = ""
        self.bot_saved = True  # Изначально считаем, что бот сохранен
        self.current_view = "main"
        self.testmenu = None
        self.chat_messages = []

        # =main menu
        self.bot_frame = None
        self.token_input = None
        self.start_stop_button = None
        self.command_frame = None
        self.command_input = None
        self.response_input = None
        self.style_frame = None
        self.bold_button = None
        self.italic_button = None
        self.underline_button = None
        self.line_button = None
        self.mono_button = None
        self.hidden_button = None
        self.command_list_label = None
        self.command_list_frame = None
        self.command_edit_delete_frame = None
        self.edit_button = None
        self.delete_button = None
        self.console_label = None
        self.console_output = None
        self.add_button = None

        # Теstovoye window
        self.test_chat_frame = None
        self.chat_area = None
        self.chat_input_frame = None
        self.chat_input = None
        self.send_button = None
        self.menubar = None
        self.chat_scroll = None

        self.create_ui()
        self.create_menu()
        self.protocol("WM_DELETE_WINDOW", self.on_close)
        self.after(100, self.process_queue)

    def create_menu(self):
        self.menubar = Menu(self)

        # File menu
        filemenu = Menu(self.menubar, tearoff=0)
        filemenu.add_command(label="Сохранить как", command=self.save_bot)
        filemenu.add_command(label="Открыть", command=self.load_bot)
        filemenu.add_command(label="Удалить", command=self.remove_bot)
        self.menubar.add_cascade(label="Файл", menu=filemenu)

        # Code menu
        self.code_menu = Menu(self.menubar, tearoff=0)
        self.code_menu.add_command(label="Код", command=self.toggle_code_view)
        self.menubar.add_cascade(label="Код", menu=self.code_menu)

        self.config(menu=self.menubar)

    def toggle_code_view(self):
        self.show_code_view()

    def show_code_view(self):
        # Создание нового окна для отображения кода
        code_window = Toplevel(self)
        code_window.title("Код бота")
        code_window.geometry("900x600")

        # Создание текстового поля для отображения кода
        code_text = Text(code_window, bg="#212325", fg="white", bd=0, wrap="word", font=("Consolas", 10), highlightthickness=0)
        code_text.pack(side="left", fill="both", expand=True, padx=10, pady=10)

        # Scrollbar для кода
        code_scroll = Scrollbar(code_window, command=code_text.yview)
        code_scroll.pack(side="right", fill="y", pady=10)
        code_text.configure(yscrollcommand=code_scroll.set)

        # Получение кода бота
        bot_code = self.generate_bot_code()

        # Добавление кода в текстовое поле
        code_text.insert(END, bot_code)
        code_text.config(state="normal")  # Разрешаем выделение текста, но не редактирование

        # Создание кнопки "Копировать"
        copy_button = ctk.CTkButton(code_window, text="Копировать",
                                    command=lambda: self.copy_code(code_text.get("1.0", END)))
        copy_button.pack(side="left", padx=10, pady=10)
         # Создание кнопки "Сохранить как"
        save_button = ctk.CTkButton(code_window, text="Сохранить как", command=lambda: self.save_code(code_text.get("1.0", END)))
        save_button.pack(side="left", padx=10, pady=10)

    def generate_bot_code(self):
        bot_code = f"""
import telebot
import re

bot_token = '{self.bot_token}'
bot = telebot.TeleBot(bot_token)


def parse_markdown(text):
        text = re.sub(r'\.', r'\.', text)
        text = re.sub(r'!', r'\!', text)
        text = re.sub(r'-', r'\-', text)
        text = re.sub(r'\)', r'\)', text)
        text = re.sub(r'\(', r'\(', text)
        text = re.sub(r'\+', r'\+', text)
        text = re.sub(r'=', r'\=', text)
        text = re.sub(r'#', r'\#', text)
        text = re.sub(r'>', r'\>', text)
        text = re.sub(r'{{', r'{{', text)
        text = re.sub(r'}}', r'}}', text)
        text = re.sub(r'\[', r'\[', text)
        text = re.sub(r'\]', r'\]', text)

        return text
"""

        for command, response in self.command_manager.get_commands().items():
            # Удаляем начальный слэш из команды для определения функции-обработчика
            command_name = command.lstrip('/')
            bot_code += f"""
@bot.message_handler(commands=['{command_name}'])
def command_{command_name.replace(' ', '_')}(message):
    response = parse_markdown(\"\"\"{response}\"\"\")
    bot.reply_to(message, response, parse_mode="MarkdownV2")
"""

        bot_code += """
@bot.message_handler(func=lambda message: True)
def handle_all_messages(message):
    command = message.text
    response = bot_commands.get(command)
    if response:
        styled_response = parse_markdown(response)
        bot.reply_to(message, styled_response, parse_mode="MarkdownV2")
    else:
        bot.reply_to(message, "Неизвестная команда.", parse_mode="MarkdownV2")


if __name__ == '__main__':
    bot_commands = {
"""
        for command, response in self.command_manager.get_commands().items():
            bot_code += f"        '{command}': \"\"\"{response}\"\"\",\n"
        bot_code += """
    }
    bot.polling(none_stop=True)
"""
        return bot_code

    def remove_code_comments(self, code):
        # Удаление однострочных комментариев (начинающихся с #)
        code = re.sub(r'#.*', '', code)
        # Удаление многострочных комментариев (начинающихся с ''' или """)
        code = re.sub(r"(\"\"\"|\'\'\').*?(\"\"\"|\'\'\')", '', code, flags=re.DOTALL)
        return code

    def remove_empty_lines(self, code):
        # Удаление пустых строк
        code = os.linesep.join([line for line in code.splitlines() if line.strip()])
        return code

    def copy_code(self, code):
        self.clipboard_clear()
        self.clipboard_append(code)
        self.update()
        messagebox.showinfo("Копирование", "Код скопирован в буфер обмена.")

    def save_code(self, code):
        filename = filedialog.asksaveasfilename(defaultextension=".py", filetypes=[("Python Files", "*.py")])
        if filename:
            with open(filename, "w", encoding="utf-8") as f:
                f.write(code)
            messagebox.showinfo("Сохранение", f"Код сохранен в файл: {filename}")

    def show_main_view(self):
        self.clear_code_view()
        self.create_ui()
        self.create_menu()

    def clear_code_view(self):
        if hasattr(self, "code_window") and self.code_window:
            self.code_window.destroy()
            self.code_window = None

    def clear_test_view(self):
        if self.test_chat_frame:
            self.test_chat_frame.destroy()
            self.test_chat_frame = None
        if self.chat_area:
            self.chat_area.destroy()
            self.chat_area = None
        if self.chat_input_frame:
            self.chat_input_frame.destroy()
            self.chat_input_frame = None
        if self.chat_input:
            self.chat_input.destroy()
            self.chat_input = None
        if self.send_button:
            self.send_button.destroy()
            self.send_button = None
        if self.chat_scroll:
            self.chat_scroll.destroy()
            self.chat_scroll = None

    def clear_main_view(self):
        if self.bot_frame:
            self.bot_frame.destroy()
            self.bot_frame = None
        if self.token_input:
            self.token_input.destroy()
            self.token_input = None
        if self.start_stop_button:
            self.start_stop_button.destroy()
            self.start_stop_button = None
        if self.command_frame:
            self.command_frame.destroy()
            self.command_frame = None
        if self.command_input:
            self.command_input.destroy()
            self.command_input = None
        if self.response_input:
            self.response_input.destroy()
            self.response_input = None
        if self.style_frame:
            self.style_frame.destroy()
            self.style_frame = None
        if self.bold_button:
            self.bold_button.destroy()
            self.bold_button = None
        if self.italic_button:
            self.italic_button.destroy()
            self.italic_button = None
        if self.underline_button:
            self.underline_button.destroy()
            self.underline_button = None
        if self.line_button:
            self.line_button.destroy()
            self.line_button = None
        if self.mono_button:
            self.mono_button.destroy()
            self.mono_button = None
        if self.hidden_button:
            self.hidden_button.destroy()
            self.hidden_button = None
        if self.command_list_label:
            self.command_list_label.destroy()
            self.command_list_label = None
        if self.command_list_frame:
            self.command_list_frame.destroy()
            self.command_list_frame = None
        if self.command_edit_delete_frame:
            self.command_edit_delete_frame.destroy()
            self.command_edit_delete_frame = None
        if self.edit_button:
            self.edit_button.destroy()
            self.edit_button = None
        if self.delete_button:
            self.delete_button.destroy()
            self.delete_button = None
        if self.console_label:
            self.console_label.destroy()
            self.console_label = None
        if self.console_output:
            self.console_output.destroy()
            self.console_output = None
        if self.add_button:
            self.add_button.destroy()
            self.add_button = None

    def send_test_message(self):
        message = self.chat_input.get().strip()
        if message:
            self.display_message("Вы", message, is_bot=False)
            response = self.command_manager.get_commands().get(message)
            if response:
                styled_response = self.parse_markdown(response)
                self.display_message("Бот", styled_response, is_bot=True)
            else:
                self.display_message("Бот", "Неизвестная команда.", is_bot=True)
        self.chat_input.delete(0, ctk.END)

    def display_message(self, sender, message, is_bot):
        timestamp = datetime.datetime.now().strftime("%H:%M:%S")
        if is_bot:
            formatted_message = f"{sender} [{timestamp}]:\n{message}\n\n"
            self.chat_area.configure(state='normal')
            self.chat_area.insert("end", formatted_message)
            self.chat_area.configure(state='disabled')
        else:
            formatted_message = f"{sender} [{timestamp}]:\n{message}\n\n"
            self.chat_area.configure(state='normal')
            self.chat_area.insert("end", formatted_message, "user_message")
            self.chat_area.configure(state='disabled')
        self.chat_area.see("end")

    def create_ui(self):
        self.bot_frame = ctk.CTkFrame(self)
        self.bot_frame.pack(pady=10, padx=10, fill="x")

        ctk.CTkLabel(self.bot_frame, text="Токен бота:").pack(side="left", padx=5)
        self.token_input = ctk.CTkEntry(self.bot_frame, width=300)
        self.token_input.pack(side="left", padx=5, expand=True, fill="x")
        # Задаем событие для отслеживания изменений
        self.token_input.bind("<FocusOut>", self.update_bot_token)


        self.start_stop_button = ctk.CTkButton(self.bot_frame, text="Запустить бота", command=self.toggle_bot)
        self.start_stop_button.pack(side="right", padx=5)

        self.command_frame = ctk.CTkFrame(self)
        self.command_frame.pack(pady=10, padx=10, fill="x")

        ctk.CTkLabel(self.command_frame, text="Команда:").pack(side="left", padx=5)
        self.command_input = ctk.CTkEntry(self.command_frame, width=150)
        self.command_input.pack(side="left", padx=5, expand=True, fill="x")

        ctk.CTkLabel(self.command_frame, text="Ответ:").pack(side="left", padx=5)
        self.response_input = ctk.CTkTextbox(self.command_frame, width=150, height=50)
        self.response_input.pack(side="left", padx=5, expand=True, fill="both")

        self.style_frame = ctk.CTkFrame(self.command_frame)
        self.style_frame.pack(side="left", padx=5)

        self.bold_button = ctk.CTkButton(self.style_frame, text="Жирный", width=50, command=lambda: self.apply_style("bold"))
        self.bold_button.pack(side="left", padx=2)

        self.italic_button = ctk.CTkButton(self.style_frame, text="Курсив", width=50, command=lambda: self.apply_style("italic"))
        self.italic_button.pack(side="left", padx=2)

        self.underline_button = ctk.CTkButton(self.style_frame, text="Подчёркнутый", width=50,
                                            command=lambda: self.apply_style("underline"))
        self.underline_button.pack(side="left", padx=2)

        self.line_button = ctk.CTkButton(self.style_frame, text="Зачёркнутый", width=50, command=lambda: self.apply_style("line"))
        self.line_button.pack(side="left", padx=2)

        self.mono_button = ctk.CTkButton(self.style_frame, text="Моно", width=50, command=lambda: self.apply_style("mono"))
        self.mono_button.pack(side="left", padx=2)

        self.hidden_button = ctk.CTkButton(self.style_frame, text="Скрытый", width=50,
                                            command=lambda: self.apply_style("hidden"))
        self.hidden_button.pack(side="left", padx=2)

        self.add_button = ctk.CTkButton(self.command_frame, text="Добавить", command=self.add_command)
        self.add_button.pack(side="right", padx=5)

        self.command_list_label = ctk.CTkLabel(self, text="Список команд:")
        self.command_list_label.pack(pady=2, anchor="w", padx=10)

        self.command_list_frame = ctk.CTkScrollableFrame(self, width=680, height=200)
        self.command_list_frame.pack(pady=5, padx=10, fill="both", expand=True)

        self.command_edit_delete_frame = ctk.CTkFrame(self)
        self.command_edit_delete_frame.pack(pady=1, padx=10, fill="x")

        self.edit_button = ctk.CTkButton(self.command_edit_delete_frame, text="Редактировать",
                                          command=self.edit_selected_command)
        self.edit_button.pack(side="left", padx=5)

        self.delete_button = ctk.CTkButton(self.command_edit_delete_frame, text="Удалить",
                                            command=self.delete_selected_command)
        self.delete_button.pack(side="left", padx=5)

        self.console_label = ctk.CTkLabel(self, text="Консоль:")
        self.console_label.pack(pady=2, anchor="w", padx=10)
        self.console_output = ctk.CTkTextbox(self, width=680, height=150)
        self.console_output.pack(pady=5, padx=10, fill="both", expand=True)

        self.update_command_list()

    def toggle_bot(self):
        if self.is_running:
            self.stop_bot()
        else:
            self.start_bot()

    def start_bot(self):
        bot_token = self.token_input.get()
        if bot_token:
            self.bot_token = bot_token
        self.bot_saved = False # Считаем, что произошли изменения
        try:
            self.bot = telebot.TeleBot(bot_token)
            self.is_running = True
            self.start_stop_button.configure(text="Остановить бота")
            threading.Thread(target=self.run_bot, daemon=True).start()
            self.log_to_console("Бот запущен.")
        except telebot.apihelper.ApiException as e:
            self.log_to_console(f"Ошибка при инициализации бота (API): {str(e)}")
        except Exception as e:
            self.log_to_console(f"Ошибка при инициализации бота: {str(e)}")

    def stop_bot(self):
        self.is_running = False
        if self.bot:
            self.bot.stop_polling()
            self.bot = None
        self.start_stop_button.configure(text="Запустить бота")
        self.log_to_console("Бот остановлен.")

    def run_bot(self):
        @self.bot.message_handler(func=lambda message: True)
        def handle_messages(message):
            command = message.text
            response = self.command_manager.get_commands().get(command)
            if response:
                styled_response = self.parse_markdown(response)
                self.bot.reply_to(message, styled_response, parse_mode="MarkdownV2")
                self.queue.put(f"Ответ на команду '{command}': '{response}'")
            else:
                self.queue.put(f"Неизвестная команда: '{command}'")

        try:
            self.bot.polling(non_stop=False, interval=1, timeout=20)
        except Exception as e:
            self.queue.put(f"Ошибка в работе бота: {str(e)}")
            traceback.print_exc()
            time.sleep(10)

    def apply_style(self, style):
        try:
            selected_text = self.response_input.selection_get()
            start_index = self.response_input.index("sel.first")
            end_index = self.response_input.index("sel.last")

            if style == "bold":
                styled_text = f"*{selected_text}*"
            elif style == "italic":
                styled_text = f"_{selected_text}_"
            elif style == "underline":
                styled_text = f"__ {selected_text} __"
            elif style == "line":
                styled_text = f"~{selected_text}~"
            elif style == "mono":
                styled_text = f"`{selected_text}`"
            elif style == "hidden":
                styled_text = f"||{selected_text}||"
            else:
                return

            self.response_input.delete(start_index, end_index)
            self.response_input.insert(start_index, styled_text)
        except Exception:
            pass

    def process_queue(self):
        while not self.queue.empty():
            message = self.queue.get()
            self.log_to_console(message)
            self.after(100, self.process_queue)

    def log_to_console(self, message):
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.console_output.insert(ctk.END, f"{timestamp} - {message}\n")
        self.console_output.see(ctk.END)

    def add_command(self):
        command = self.command_input.get().strip()
        response = self.response_input.get("1.0", ctk.END).strip()

        if command and response:
            if command in self.command_manager.get_commands():
                messagebox.showerror("Ошибка", "Такая команда уже существует!")
                return
            self.command_manager.add_command(command, response)
            self.update_command_list()
            self.command_input.delete(0, ctk.END)
            self.response_input.delete("1.0", ctk.END)
            self.log_to_console(f"Добавлена команда: {command} -> {response}")
            self.bot_saved = False
        else:
            messagebox.showerror("Ошибка", "Заполните поля команды и ответа!")

    def select_command(self, command):
        self.selected_command = command

    def edit_selected_command(self):
        if not self.selected_command:
            messagebox.showinfo("Внимание", "Выберете команду для редактирования!")
            return

        edit_window = Toplevel(self)
        edit_window.title("Редактирование команды")
        edit_window.geometry("300x300")

        ctk.CTkLabel(edit_window, text="Старая команда:", text_color="black").pack(pady=5)
        old_command_entry = ctk.CTkEntry(edit_window, width=200)
        old_command_entry.insert(0, self.selected_command)
        old_command_entry.configure(state='readonly')
        old_command_entry.pack(pady=5)

        ctk.CTkLabel(edit_window, text="Новая команда:", text_color="black").pack(pady=5)
        new_command_entry = ctk.CTkEntry(edit_window, width=200)
        new_command_entry.pack(pady=5)

        ctk.CTkLabel(edit_window, text="Новый ответ:", text_color="black").pack(pady=5)
        new_response_entry = ctk.CTkTextbox(edit_window, width=200, height=50)
        new_response_entry.pack(pady=5)

        if self.selected_command:
            old_response = self.command_manager.get_commands().get(self.selected_command)
            if old_response:
                new_response_entry.insert("1.0", old_response)

        def save_edit():
            new_command = new_command_entry.get().strip()
            new_response = new_response_entry.get("1.0", ctk.END).strip()

            if new_command and new_response:
                if new_command in self.command_manager.get_commands() and new_command != self.selected_command:
                    messagebox.showerror("Ошибка", "Такая команда уже существует!")
                    return

                self.command_manager.edit_command(self.selected_command, new_command, new_response)
                self.update_command_list()
                self.log_to_console(f"Команда '{self.selected_command}' изменена на: {new_command} -> {new_response}")
                edit_window.destroy()
                self.selected_command = None
                self.bot_saved = False
            else:
                messagebox.showerror("Ошибка", "Заполните поля команды и ответа!")

        save_button = ctk.CTkButton(edit_window, text="Сохранить", command=save_edit)
        save_button.pack(pady=10)

    def delete_selected_command(self):
        if not self.selected_command:
            messagebox.showinfo("Внимание", "Выберете команду для удаления!")
            return

        if messagebox.askokcancel("Удалить", f"Удалить команду '{self.selected_command}'?"):
            self.command_manager.remove_command(self.selected_command)
            self.update_command_list()
            self.log_to_console(f"Команда '{self.selected_command}' удалена.")
            self.selected_command = None
            self.bot_saved = False

    def update_command_list(self):
        if not self.command_list_frame:
            return
        for button in self.command_buttons.values():
            button.destroy()
        self.command_buttons.clear()

        for command, response in self.command_manager.get_commands().items():
            button = ctk.CTkButton(self.command_list_frame, text=f"Команда: {command} | Ответ: {response}",
                                  command=lambda cmd=command: self.select_command(cmd))
            button.pack(pady=2, fill='x')
            self.command_buttons[command] = button

    def save_bot(self):
        filename = filedialog.asksaveasfilename(defaultextension=".tbb", filetypes=[("Telegram BackBots", "*.tbb")])
        if filename:
            data = self.command_manager.get_data()
            with open(filename, "w") as f:
                json.dump({"commands": data, "bot_token": self.bot_token}, f)
            self.log_to_console(f"Бот сохранен в {filename}")
            self.bot_saved = True # Устанавливаем bot_saved в True после успешного сохранения

    def load_bot(self):
        filename = filedialog.askopenfilename(defaultextension=".tbb", filetypes=[("Telegram BackBots", "*.tbb")])
        if filename:
            try:
                with open(filename, "r") as f:
                    data = json.load(f)
                    self.command_manager.load_commands(data.get("commands", {}))
                    self.bot_token = data.get("bot_token", "")
                    self.token_input.delete(0, ctk.END)
                    self.token_input.insert(0, self.bot_token)
                    self.update_command_list()
                    self.log_to_console(f"Боты загружены из {filename}")
                    self.bot_saved = True # Устанавливаем bot_saved в True после загрузки
            except FileNotFoundError:
                messagebox.showerror("Ошибка", "Файл не найден!")
            except json.JSONDecodeError:
                messagebox.showerror("Ошибка", "Неверный формат файла!")

    def remove_bot(self):
        filename = filedialog.askopenfilename(defaultextension=".tbb", filetypes=[("Telegram BackBots", "*.tbb")])
        if filename:
            try:
                os.remove(filename)
                self.command_manager.load_commands({})
                self.update_command_list()
                self.bot_token = ""
                self.token_input.delete(0, ctk.END)
                self.log_to_console(f"Бот удален {filename}")
                self.bot_saved = True  # Считаем, что после удаления нет несохраненных изменений
            except FileNotFoundError:
                messagebox.showerror("Ошибка", "Файл не найден!")
            except OSError as e:
                messagebox.showerror("Ошибка", f"Не удалось удалить файл: {e}")
    
    def update_bot_token(self, event):
        """Обновляет self.bot_token при изменении поля ввода токена."""
        self.bot_token = self.token_input.get()
        self.bot_saved = False # Помечаем, что есть несохраненные изменения

    def on_close(self):
        self.is_running = False
        if self.bot:
            self.bot.stop_polling()

        if not self.bot_saved:  # Проверка флага bot_saved
            if messagebox.askyesno("Сохранить?", "Вы не сохранили бота, хотите сохранить?"):
                self.save_bot()
                self.log_to_console("Бот сохранен перед выходом")

        self.destroy()


    def parse_markdown(self, text):
        text = re.sub(r'\.', r'\.', text)
        text = re.sub(r'!', r'\!', text)
        text = re.sub(r'-', r'\-', text)
        text = re.sub(r'\)', r'\)', text)
        text = re.sub(r'\(', r'\(', text)
        text = re.sub(r'\+', r'\+', text)
        text = re.sub(r'=', r'\=', text)
        text = re.sub(r'#', r'\#', text)
        text = re.sub(r'>', r'\>', text)
        text = re.sub(r'{', r'\{', text)
        text = re.sub(r'}', r'\}', text)
        text = re.sub(r'\[', r'\[', text)
        text = re.sub(r'\]', r'\]', text)

        return text


if __name__ == "__main__":
    app = BotApp()
    app.mainloop()
