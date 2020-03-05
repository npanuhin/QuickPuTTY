import sublime
import sublime_plugin
from subprocess import Popen, PIPE
import os
from re import match as re_match

PACKAGE_NAME = "QuickPuTTY"

MSG = {
    "cancel": "QuickPuTTY: Canceled",
    "reload": "QuickPuTTY: Sessions reloaded",
    "remove": "QuickPuTTY: Session \"{session_name}\" was removed",
    "already_has_name": "A session with that name already exists. Please choose a different name or change an existing one.",
    "empty_host": "Server host cannot be empty. Please enter the server IP address or URL.",
    "wrong_port": "Server port must be a natural number.",
    "no_sessions": "You have not saved any sessions :(\nGo to \"PuTTY> New session\" to add one!"
}

IPV4_REGEX = r"(?:https?:?[\/\\]{,2})?(\d+)[\.:,](\d+)[\.:,](\d+)[\.:,](\d+)(?::\d+)?"


def mkpath(*paths):
    return os.path.normpath(os.path.join(*paths))


def runCommand(command, result=False):
    if type(command) is str:
        command = list(command.split())
    if result:
        return Popen(command, stdout=PIPE, stderr=PIPE).communicate()
    Popen(command)


def makeSessionMenuFile(sessions):
    with open(mkpath(sublime.packages_path(), PACKAGE_NAME, "template-menu.json"), "r", encoding="utf-8") as file:
        menu_data = sublime.decode_value(file.read().strip())

    for name in sessions:
        to_write = {
            "caption": name,
            "command": "quickputty_open",
            "args": {
                "host": sessions[name]["host"],
                "port": sessions[name]["port"]
            }
        }

        if sessions[name]["login"]:
            to_write["args"]["login"] = sessions[name]["login"]
        if sessions[name]["password"]:
            to_write["args"]["password"] = sessions[name]["password"]

        menu_data[1]["children"].append(to_write)

    with open(mkpath(sublime.packages_path(), PACKAGE_NAME, "Main.sublime-menu"), "w", encoding="utf-8") as file:
        file.write(sublime.encode_value(menu_data, True))


class QuickputtyOpen(sublime_plugin.WindowCommand):

    def __init__(self, window):
        settings = sublime.load_settings(PACKAGE_NAME)
        self.run_command = settings.get("PuTTY_run_command", "putty")

    def run(self, host=None, port=22, login="", password=""):
        if host is None:
            runCommand(self.run_command)
        else:
            runCommand("{putty} -ssh {host} -P {port}{login}{password}".format(
                putty=self.run_command,
                host=host,
                port=port,
                login=" -l " + str(login) if login else "",
                password=" -pw " + str(password) if password else "",
            ))


class QuickputtyNew(sublime_plugin.WindowCommand):

    def run(self):
        with open(SESSION_FILE_PATH, "r", encoding="utf-8") as file:
            self.sessions = sublime.decode_value(file.read().strip())

        self.new_session = {
            "name": None,
            "host": None,
            "port": None,
            "login": None,
            "password": None
        }

        self.window.show_input_panel("Session name", "", self.choose_host, 0, lambda: sublime.status_message(MSG["cancel"]))

    def choose_host(self, session_name):
        # Session name check
        session_name = session_name.strip()

        if not session_name:
            print(MSG["cancel"])
            sublime.status_message(MSG["cancel"])
            return

        if session_name in self.sessions:
            sublime.error_message(MSG["already_has_name"])
            return

        self.new_session["name"] = session_name
        # Asking for host
        self.window.show_input_panel("Server host", "127.0.0.1", self.choose_port, 0, lambda: sublime.status_message(MSG["cancel"]))

    def choose_port(self, session_host):
        # Session host check
        session_host = session_host.strip()
        if not session_host:
            sublime.error_message(MSG["empty_host"])
            print(MSG["cancel"])
            sublime.status_message(MSG["cancel"])
            return

        # If ipv4 is recognized:
        ipv4_match = re_match(IPV4_REGEX, session_host)
        if ipv4_match is not None:
            session_host = ".".join(ipv4_match.group(i) for i in range(1, 5))

        self.new_session["host"] = session_host
        # Asking for port
        self.window.show_input_panel("Connection port", "22", self.choose_login, 0, lambda: sublime.status_message(MSG["cancel"]))

    def choose_login(self, session_port):
        # Session port check
        try:
            session_port = int(session_port.strip())
            wrong = session_port <= 0
        except Exception:
            wrong = True

        if wrong:
            sublime.error_message(MSG["wrong_port"])
            print(MSG["cancel"])
            sublime.status_message(MSG["cancel"])
            return

        self.new_session["port"] = session_port
        # Asking for username
        self.window.show_input_panel("Username (optional)", "", self.choose_password, 0, lambda: sublime.status_message(MSG["cancel"]))

    def choose_password(self, session_login):
        # Session login check
        self.new_session["login"] = session_login.strip()
        # Asking for password
        self.window.show_input_panel("Password (optional)", "", self.save, 0, lambda: sublime.status_message(MSG["cancel"]))

    def save(self, session_password):
        self.new_session["password"] = session_password.strip()
        name = self.new_session["name"]
        del self.new_session["name"]

        self.sessions[name] = self.new_session

        # Saving to "sessions.json"
        with open(SESSION_FILE_PATH, "w", encoding="utf-8") as file:
            file.write(sublime.encode_value(self.sessions, True))

        # Writing to sublime-menu file
        makeSessionMenuFile(self.sessions)


class QuickputtyRemove(sublime_plugin.WindowCommand):

    def run(self):
        with open(SESSION_FILE_PATH, "r", encoding="utf-8") as file:
            self.sessions = sublime.decode_value(file.read().strip())
        if not self.sessions:
            sublime.message_dialog(MSG["no_sessions"])
            return

        self.session_names = [[name, self.sessions[name]["host"]] for name in self.sessions]

        self.window.show_quick_panel(["{name} ({host})".format(name=name, host=host) for name, host in self.session_names], self.confirm)

    def confirm(self, index):
        # If nothing is chosen
        if index == -1:
            print(MSG["cancel"])
            sublime.status_message(MSG["cancel"])
            return

        name, host = self.session_names[index]
        if sublime.yes_no_cancel_dialog("Session \"{name}\" ({host}) will be deleted. Are you sure?".format(name=name, host=host)) == sublime.DIALOG_YES:
            del self.sessions[name]

            print(MSG["remove"].format(session_name=name))

            # Saving to "sessions.json"
            with open(SESSION_FILE_PATH, "w", encoding="utf-8") as file:
                file.write(sublime.encode_value(self.sessions, True))

            makeSessionMenuFile(self.sessions)

            print(MSG["reload"])
            sublime.status_message(MSG["reload"])

        else:
            print(MSG["cancel"])
            sublime.status_message(MSG["cancel"])


class Sessions(sublime_plugin.EventListener):

    def on_load(self, view):
        if view.file_name() == SETTINGS_PATH:
            view.set_read_only(True)

    def on_post_save_async(self, view):
        if view.file_name() == SESSION_FILE_PATH:
            with open(SESSION_FILE_PATH, "r", encoding="utf-8") as file:
                makeSessionMenuFile(sublime.decode_value(file.read().strip()))
            print(MSG["reload"])
            # sublime.status_message(MSG["reload"])


def plugin_loaded():
    global USER_DATA_PATH
    global SETTINGS_PATH
    global SESSION_FILE_PATH
    global USER_PACKAGE_PATH

    USER_DATA_PATH = mkpath(sublime.packages_path(), "User")
    USER_PACKAGE_PATH = mkpath(USER_DATA_PATH, "QuickPuTTY")
    SETTINGS_PATH = mkpath(sublime.packages_path(), PACKAGE_NAME, "QuickPuTTY.sublime-settings")
    SESSION_FILE_PATH = mkpath(USER_PACKAGE_PATH, "sessions.json")

    # Creating "User file"
    if not os.path.isdir(USER_PACKAGE_PATH):
        os.mkdir(mkpath(USER_PACKAGE_PATH))

    # (Re-)Creating file for storing sessions
    if not os.path.isfile(SESSION_FILE_PATH):
        with open(SESSION_FILE_PATH, "r", encoding="utf-8") as file:
            rewrite = (len(file.read().strip()) < 2)
    else:
        rewrite = True

    if rewrite:
        with open(SESSION_FILE_PATH, "w", encoding="utf-8") as file:
            file.write(r"{}")
