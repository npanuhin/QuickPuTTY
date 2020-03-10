import sublime
import sublime_plugin
from subprocess import Popen
import os
from re import match as re_match
from copy import deepcopy

from .QuickPuTTY_encryption import QuickPuTTYEncryption
from .QuickPuTTY_text import *

# If you want to edit default settings:
# Go to "class Session > def on_load" and change "view.set_read_only(True)" to False (or comment this line)

PACKAGE_NAME = "QuickPuTTY"

IPV4_REGEX = r"(?:https?:?[\/\\]{,2})?(\d+)[\.:,](\d+)[\.:,](\d+)[\.:,](\d+)(?::\d+)?"


def mkpath(*paths):
    '''Combines paths and normalizes the result'''
    return os.path.normpath(os.path.join(*paths))


def runCommand(command, result=False):
    '''Runs a system command'''
    if type(command) is str:
        command = list(command.split())
    if result:
        return Popen(command).communicate()
    Popen(command)


def makeSessionMenuFile(sessions):
    '''Creates a .sublime-menu file containing given sessions (from a template).
       Takes an encrypted password'''
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


def checkSessions(sessions):
    '''Checks whether the session format is correct and encrypts the password'''
    if not isinstance(sessions, dict):
        sublime.error_message(MSG["bad_json"])

    for name in sessions:
        if not isinstance(sessions[name], dict) or "host" not in sessions[name] or "port" not in sessions[name]:
            sublime.error_message(MSG["bad_json"])
            break

        if "encrypt" in sessions[name]:
            del sessions[name]["encrypt"]
            sessions[name]["password"] = encryption.encrypt(sessions[name]["password"])
    else:
        return sessions


def checkSettings():
    '''Checks whether the session format is correct'''
    settings = sublime.load_settings(PACKAGE_NAME + ".sublime-settings")

    if not settings.has("encryption_key_one") \
            or not settings.has("encryption_key_two") \
            or not settings.has("PuTTY_run_command") \
            or not settings.has("clear_on_remove"):
        return False

    settings.clear_on_change("check_settings")
    settings.add_on_change("check_settings", checkSettings)

    if not isinstance(settings.get("encryption_key_one"), int) or not isinstance(settings.get("encryption_key_two"), str):
        sublime.error_message(MSG["bad_keys"])
        return False

    if not isinstance(settings.get("clear_on_remove"), bool):
        sublime.error_message(MSG["bad_clear_on_remove"])
        return False

    if not isinstance(settings.get("PuTTY_run_command"), str):
        sublime.error_message(MSG["bad_PuTTY_run_command"])
        return False

    print("QuickPuTTY: Settings checked")
    return True


class QuickputtyOpen(sublime_plugin.WindowCommand):
    '''Responsible for opening PuTTY.
       Handles "quickputty_open" command.'''

    def run(self, host=None, port=22, login="", password=""):
        run_command = sublime.load_settings(PACKAGE_NAME + ".sublime-settings").get("PuTTY_run_command")

        if host is None:
            runCommand(run_command)
        else:
            password = encryption.decrypt(password)
            runCommand("{putty} -ssh {host} -P {port}{login}{password}".format(
                putty=run_command,
                host=host,
                port=port,
                login=" -l " + str(login) if login else "",
                password=" -pw " + password if password else "",
            ))


class QuickputtyNew(sublime_plugin.WindowCommand):
    '''Responsible for creating new sessions.
       Handles "quickputty_new" command.'''

    def run(self):
        with open(SESSIONS_PATH, "r", encoding="utf-8") as file:
            try:
                self.sessions = sublime.decode_value(file.read().strip())
            except Exception:
                sublime.error_message(MSG["bad_json"])
                return

        if checkSessions(self.sessions) is None:
            sublime.status_message(MSG["cancel"])
            return

        self.new_session = {key: None for key in ("host", "port", "login", "password")}

        # Asking for name
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

        # Saving and asking for host
        self.session_name = session_name
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

        # Saving and asking for port
        self.new_session["host"] = session_host
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

        # Saving and asking for username
        self.new_session["port"] = session_port
        self.window.show_input_panel("Username (optional)", "", self.choose_password, 0, lambda: sublime.status_message(MSG["cancel"]))

    def choose_password(self, session_login):
        # Saving and asking for password
        self.new_session["login"] = session_login.strip()
        self.window.show_input_panel("Password (optional)", "", self.save, 0, lambda: sublime.status_message(MSG["cancel"]))

    def save(self, session_password):
        # Saving
        self.new_session["password"] = encryption.encrypt(session_password.strip())

        self.sessions[self.session_name] = self.new_session

        # Saving to "sessions.json"
        with open(SESSIONS_PATH, "w", encoding="utf-8") as file:
            file.write(MSG["encrypt_changed_password"] + sublime.encode_value(self.sessions, True))

        # Writing to sublime-menu file
        makeSessionMenuFile(self.sessions)


class QuickputtyRemove(sublime_plugin.WindowCommand):
    '''Responsible for removing sessions.
       Handles "quickputty_remove" command.'''

    def run(self):
        with open(SESSIONS_PATH, "r", encoding="utf-8") as file:
            try:
                self.sessions = sublime.decode_value(file.read().strip())
            except Exception:
                sublime.error_message(MSG["bad_json"])
                return

        if checkSessions(self.sessions) is None:
            sublime.status_message(MSG["cancel"])
            return

        if not self.sessions:
            sublime.message_dialog(MSG["no_sessions"])
            return

        self.sessions_data = [[name, self.sessions[name]["host"]] for name in self.sessions]

        self.window.show_quick_panel(["{} ({})".format(name, host) for name, host in self.sessions_data], self.confirm)

    def confirm(self, index):
        # If nothing is chosen
        if index == -1:
            print(MSG["cancel"])
            sublime.status_message(MSG["cancel"])
            return

        name, host = self.sessions_data[index]
        if sublime.yes_no_cancel_dialog("Session \"{}\" ({}) will be deleted. Are you sure?".format(name, host)) == sublime.DIALOG_YES:
            del self.sessions[name]

            print(MSG["remove"].format(session_name=name))

            # Saving to "sessions.json"
            with open(SESSIONS_PATH, "w", encoding="utf-8") as file:
                file.write(MSG["encrypt_changed_password"] + sublime.encode_value(self.sessions, True))

            makeSessionMenuFile(self.sessions)

        else:
            print(MSG["cancel"])
            sublime.status_message(MSG["cancel"])


class Sessions(sublime_plugin.EventListener):
    '''Controls the behavior of the settings file and updates the .sublime-menu file.'''

    def on_load(self, view):
        if view.file_name() == SETTINGS_PATH:
            # Preventing the user from changing the default settings.
            view.set_read_only(True)

    def on_post_save_async(self, view):
        if view.file_name() == SESSIONS_PATH:
            # Updating menu file
            with open(SESSIONS_PATH, "r", encoding="utf-8") as file:
                try:
                    sessions = sublime.decode_value(file.read().strip())
                except Exception:
                    sublime.error_message(MSG["bad_json"])
                    return

            sessions = checkSessions(sessions)
            if sessions is None:
                return

            with open(SESSIONS_PATH, "w", encoding="utf-8") as file:
                file.write(MSG["encrypt_changed_password"] + sublime.encode_value(sessions, True))
            makeSessionMenuFile(sessions)


class QuickputtyReadme(sublime_plugin.WindowCommand):
    '''Responsible for showing the README file when installing the package.
       Handles "quickputty_readme" command.'''

    def run(self):
        view = sublime.active_window().new_file()
        view.set_read_only(True)
        view.set_name("QuickPuTTY")
        view.add_phantom("test", sublime.Region(0, 0), INSTALL_HTML, sublime.LAYOUT_BELOW, lambda url: sublime.run_command("open_url", args={"url": url}))


def plugin_loaded():
    # Initialization
    from package_control import events

    global USER_DATA_PATH
    global USER_PACKAGE_PATH
    global SETTINGS_PATH
    global SESSIONS_PATH
    global MENU_PATH
    global TEMPLATE_MENU
    global encryption

    TEMPLATE_MENU = sublime.decode_value(TEMPLATE_MENU)

    USER_DATA_PATH = mkpath(sublime.packages_path(), "User")
    USER_PACKAGE_PATH = mkpath(USER_DATA_PATH, "QuickPuTTY")
    SETTINGS_PATH = mkpath(sublime.packages_path(), PACKAGE_NAME, "QuickPuTTY.sublime-settings")
    SESSIONS_PATH = mkpath(USER_PACKAGE_PATH, "sessions.json")
    MENU_PATH = mkpath(USER_PACKAGE_PATH, "Main.sublime-menu")

    # Show README
    if events.install(PACKAGE_NAME):
        QuickputtyReadme(sublime.active_window()).run()

    # Check settings
    if not checkSettings():
        return

    settings = sublime.load_settings(PACKAGE_NAME + ".sublime-settings")

    encryption = QuickPuTTYEncryption(settings.get("encryption_key_one"), settings.get("encryption_key_two"))

    # Creating "User file"
    if not os.path.isdir(USER_PACKAGE_PATH):
        os.mkdir(mkpath(USER_PACKAGE_PATH))

    # (Re-)Creating file for storing sessions
    if os.path.isfile(SESSIONS_PATH):
        with open(SESSIONS_PATH, "r", encoding="utf-8") as file:
            try:
                sessions = sublime.decode_value(file.read().strip())
            except Exception:
                sublime.error_message(MSG["bad_json"])
                return
            sessions = checkSessions(sessions)
            if sessions is None:
                return
    else:
        sessions = {}

    # Updating sessions.json
    with open(SESSIONS_PATH, "w", encoding="utf-8") as file:
        file.write(MSG["encrypt_changed_password"] + sublime.encode_value(sessions, True))

    # Making menu file
    makeSessionMenuFile(sessions)


def plugin_unloaded():
    from package_control import events

    # Removing unnecessary menu file
    if os.path.exists(MENU_PATH):
        os.remove(MENU_PATH)

    if events.remove(PACKAGE_NAME):
        # If setting "clear_on_remove" is True:
        if sublime.load_settings(PACKAGE_NAME + ".sublime-settings").get("clear_on_remove", False):
            # Removing sessions.json
            os.remove(SESSIONS_PATH)
            # Trying to remove QuickPuTTY user directory
            try:
                os.rmdir(USER_PACKAGE_PATH)
            except Exception:
                sublime.error_message("Can not remove QuickPuTTY user directory.")
