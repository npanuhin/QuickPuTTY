import sublime
import sublime_plugin
from subprocess import Popen, PIPE
import os
from re import match as re_match
from copy import deepcopy

# If you want to edit default settings:
# Go to "class Session > def on_load" and change "view.set_read_only(True)" to False (or comment this line)

PACKAGE_NAME = "QuickPuTTY"

MSG = {
    "cancel": "QuickPuTTY: Canceled",
    "reload": "QuickPuTTY: Sessions reloaded",
    "remove": "QuickPuTTY: Session \"{session_name}\" was removed",
    "already_has_name": "A session with that name already exists. Please choose a different name or change an existing one.",
    "empty_host": "Server host cannot be empty. Please enter the server IP address or URL.",
    "wrong_port": "Server port must be a natural number.",
    "no_sessions": "You have not saved any sessions :(\nGo to \"PuTTY > New session\" to add one!"
}

IPV4_REGEX = r"(?:https?:?[\/\\]{,2})?(\d+)[\.:,](\d+)[\.:,](\d+)[\.:,](\d+)(?::\d+)?"

TEMPLATE_MENU = r"""
[
    {
        "caption": "Preferences",
        "mnemonic": "n",
        "id": "preferences",
        "children": [
            {
                "caption": "Package Settings",
                "mnemonic": "P",
                "id": "package-settings",
                "children": [
                    {
                        "caption": "QuickPuTTY Settings",
                        "command": "edit_settings",
                        "args": {
                            "base_file": "${packages}/QuickPuTTY/QuickPuTTY.sublime-settings",
                            "default": "{\n\t$0\n}\n"
                        }
                    }
                ]
            }
        ]
    },
    {
        "caption": "PuTTY",
        "mnemonic": "P",
        "id": "putty",
        "children": [
            // If you want, you can add an option to only run PuTTY (without connecting to certain server):
            // {
            //     "caption": "Open PuTTY",
            //     "command": "quickputty_open"
            // },
            // { "caption": "-" },
            {
                "caption": "New session",
                "command": "quickputty_new"
            },
            {
                "caption": "Manage sessions",
                "command": "open_file",
                "args": {"file": "${packages}/User/QuickPuTTY/sessions.json"},
            },
            {
                "caption": "Remove session",
                "command": "quickputty_remove"
            },
            { "caption": "-" }
        ]
    }
]"""


def mkpath(*paths):
    return os.path.normpath(os.path.join(*paths))


def runCommand(command, result=False):
    if type(command) is str:
        command = list(command.split())
    if result:
        return Popen(command, stdout=PIPE, stderr=PIPE).communicate()
    Popen(command)


def makeSessionMenuFile(sessions):
    data = deepcopy(TEMPLATE_MENU)

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

        data[1]["children"].append(to_write)

    with open(MENU_PATH, "w", encoding="utf-8") as file:
        file.write(sublime.encode_value(data, True))

    print(MSG["reload"])
    sublime.status_message(MSG["reload"])


class QuickputtyOpen(sublime_plugin.WindowCommand):

    def run(self, host=None, port=22, login="", password=""):
        run_command = sublime.load_settings(PACKAGE_NAME + ".sublime-settings").get("PuTTY_run_command")

        if host is None:
            runCommand(run_command)
        else:
            runCommand("{putty} -ssh {host} -P {port}{login}{password}".format(
                putty=run_command,
                host=host,
                port=port,
                login=" -l " + str(login) if login else "",
                password=" -pw " + str(password) if password else "",
            ))


class QuickputtyNew(sublime_plugin.WindowCommand):

    def run(self):
        with open(SESSIONS_PATH, "r", encoding="utf-8") as file:
            self.sessions = sublime.decode_value(file.read().strip())

        self.new_session = {key: None for key in ("name", "host", "port", "login", "password")}

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
        with open(SESSIONS_PATH, "w", encoding="utf-8") as file:
            file.write(sublime.encode_value(self.sessions, True))

        # Writing to sublime-menu file
        makeSessionMenuFile(self.sessions)


class QuickputtyRemove(sublime_plugin.WindowCommand):

    def run(self):
        with open(SESSIONS_PATH, "r", encoding="utf-8") as file:
            self.sessions = sublime.decode_value(file.read().strip())

        if not self.sessions:
            sublime.message_dialog(MSG["no_sessions"])
            return

        self.session_names = [[name, self.sessions[name]["host"]] for name in self.sessions]

        self.window.show_quick_panel(["{} ({})".format(name, host) for name, host in self.session_names], self.confirm)

    def confirm(self, index):
        # If nothing is chosen
        if index == -1:
            print(MSG["cancel"])
            sublime.status_message(MSG["cancel"])
            return

        name, host = self.session_names[index]
        if sublime.yes_no_cancel_dialog("Session \"{}\" ({}) will be deleted. Are you sure?".format(name, host)) == sublime.DIALOG_YES:
            del self.sessions[name]

            print(MSG["remove"].format(session_name=name))

            # Saving to "sessions.json"
            with open(SESSIONS_PATH, "w", encoding="utf-8") as file:
                file.write(sublime.encode_value(self.sessions, True))

            makeSessionMenuFile(self.sessions)

        else:
            print(MSG["cancel"])
            sublime.status_message(MSG["cancel"])


class Sessions(sublime_plugin.EventListener):

    def on_load(self, view):
        if view.file_name() == SETTINGS_PATH:
            view.set_read_only(True)

    def on_post_save_async(self, view):
        if view.file_name() == SESSIONS_PATH:
            with open(SESSIONS_PATH, "r", encoding="utf-8") as file:
                makeSessionMenuFile(sublime.decode_value(file.read().strip()))


def plugin_loaded():
    global USER_DATA_PATH
    global USER_PACKAGE_PATH
    global SETTINGS_PATH
    global SESSIONS_PATH
    global MENU_PATH
    global TEMPLATE_MENU

    TEMPLATE_MENU = sublime.decode_value(TEMPLATE_MENU)

    USER_DATA_PATH = mkpath(sublime.packages_path(), "User")
    USER_PACKAGE_PATH = mkpath(USER_DATA_PATH, "QuickPuTTY")
    SETTINGS_PATH = mkpath(sublime.packages_path(), PACKAGE_NAME, "QuickPuTTY.sublime-settings")
    SESSIONS_PATH = mkpath(USER_PACKAGE_PATH, "sessions.json")
    MENU_PATH = mkpath(USER_PACKAGE_PATH, "Main.sublime-menu")

    # Creating "User file"
    if not os.path.isdir(USER_PACKAGE_PATH):
        os.mkdir(mkpath(USER_PACKAGE_PATH))

    # (Re-)Creating file for storing sessions
    if os.path.isfile(SESSIONS_PATH):
        with open(SESSIONS_PATH, "r", encoding="utf-8") as file:
            rewrite = (len(file.read().strip()) < 2)
    else:
        rewrite = True

    if rewrite:
        with open(SESSIONS_PATH, "w", encoding="utf-8") as file:
            file.write(r"{}")

    if not os.path.isfile(MENU_PATH):
        with open(SESSIONS_PATH, "r", encoding="utf-8") as file:
            makeSessionMenuFile(sublime.decode_value(file.read().strip()))


def plugin_unloaded():
    if os.path.exists(MENU_PATH):
        os.remove(MENU_PATH)

    if sublime.load_settings(PACKAGE_NAME + ".sublime-settings").get("clear_on_remove", False):
        os.remove(SESSIONS_PATH)
        os.rmdir(USER_PACKAGE_PATH)
