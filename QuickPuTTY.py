#  Copyright (c) 2021 Nikita Paniukhin  |
#     Licensed under the MIT license    |
# --------------------------------------+

import sublime
import sublime_plugin
from subprocess import Popen
import os
from re import match as re_match
from copy import deepcopy
from json import dump as json_dump

# !!! The option below is currently disabled !!!
# If you want to edit default settings:
# Go to "class Session > def on_load" and change "view.set_read_only(True)" to False (or comment this line)

PACKAGE_NAME = "QuickPuTTY"

IPV4_REGEX = r"(?:https?:?[\/\\]{,2})?(\d+)[\.:,](\d+)[\.:,](\d+)[\.:,](\d+)(?::\d+)?"


def mkpath(*paths: str) -> str:
    '''Combines paths and normalizes the result'''
    return os.path.normpath(os.path.join(*paths))


USER_PACKAGE_PATH = mkpath(sublime.packages_path(), "User", PACKAGE_NAME)
SETTINGS_PATH = mkpath(sublime.packages_path(), PACKAGE_NAME, PACKAGE_NAME + ".sublime-settings")
SESSIONS_PATH = mkpath(USER_PACKAGE_PATH, "sessions.json")
MENU_PATH = mkpath(USER_PACKAGE_PATH, "Main.sublime-menu")


def makeSessionMenuFile(sessions: list) -> None:
    '''Creates a .sublime-menu file containing given sessions from a template'''

    def build(item):
        if "children" in item:
            return {
                "caption": item["name"],
                "children": [build(subitem) for subitem in item["children"]]
            }

        result = {
            "caption": item["name"],
            "command": "quickputty_open",
            "args": {
                "host": item["host"],
                "port": item["port"]
            }
        }

        if "login" in item and item["login"]:
            result["args"]["login"] = item["login"]

        if "password" in item and item["password"]:
            result["args"]["password"] = item["password"]

        return result

    data = deepcopy(TEMPLATE_MENU)

    data[0]["children"] += (build(item) for item in sessions)

    with open(MENU_PATH, 'w', encoding="utf-8") as file:
        json_dump(data, file, ensure_ascii=False, indent=4, sort_keys=False)

    print(MSG["reload"])
    sublime.status_message(MSG["reload"])


def checkSessions(sessions: list) -> list:
    '''Checks whether the format of the sessions is correct'''

    def check(sessions):
        if not isinstance(sessions, list):
            return None

        for item in sessions:
            if (
                not isinstance(item, dict) or
                "name" not in item or not isinstance(item["name"], str)
            ):
                return None

            if "children" in item:
                item["children"] = check(item["children"])
                if item is None:
                    return None
            else:
                if (
                    "host" not in item or not isinstance(item["host"], str) or
                    "port" not in item or not isinstance(item["port"], int) or
                    ("login" in item and not isinstance(item["login"], str)) or
                    ("password" in item and not isinstance(item["password"], str))
                ):
                    return None

        return sessions

    new_sessions = check(deepcopy(sessions))

    if new_sessions is None:
        sublime.error_message(MSG["invalid_sessions"])
        return None

    return new_sessions


def checkSettings() -> bool:
    '''Checks whether the format of the settings is correct'''

    settings = sublime.load_settings(PACKAGE_NAME + ".sublime-settings")

    # Check if all settings exist
    if not settings.has("PuTTY_run_command"):
        sublime.error_message(MSG["setting_not_found"])
        return False

    # Adding handler
    settings.clear_on_change("check_settings")
    settings.add_on_change("check_settings", checkSettings)

    # Checking "PuTTY_run_command" setting
    if not isinstance(settings.get("PuTTY_run_command"), str):
        sublime.error_message(MSG["bad_PuTTY_run_command"])
        return False

    print(PACKAGE_NAME + ": Settings checked")
    return True


def updateSesions(sessions):
    '''Stores sessions to "sessions.json" and creates a .sublime-menu file'''
    with open(SESSIONS_PATH, 'w', encoding="utf-8") as file:
        json_dump(sessions, file, ensure_ascii=False, indent=4, sort_keys=False)

    makeSessionMenuFile(sessions)


class QuickputtyOpen(sublime_plugin.WindowCommand):
    '''Responsible for opening PuTTY'''

    def run(self, host: str = None, port: int = 22, login: str = "", password: str = '0') -> None:
        run_command = sublime.load_settings(PACKAGE_NAME + ".sublime-settings").get("PuTTY_run_command")

        if host is None:
            Popen([run_command])
        else:
            command = [run_command, "-ssh", host, "-P", str(port)]
            if login:
                command += ["-l", login]
            if password:
                command += ["-pw", password]
            Popen(command)


class QuickputtyNew(sublime_plugin.WindowCommand):
    '''Responsible for creating new sessions.
       Handles "quickputty_new" command.'''

    def run(self):
        with open(SESSIONS_PATH, 'r', encoding="utf-8") as file:
            try:
                self.sessions = sublime.decode_value(file.read().strip())
            except Exception:
                sublime.error_message(MSG["invalid_json"])
                raise

        if checkSessions(self.sessions) is None:
            sublime.status_message(MSG["cancel"])
            return

        self.window.show_quick_panel(["Session", "Folder"], self.choose_type)

    def choose_type(self, index):
        # If nothing is chosen
        if index == -1:
            print(MSG["cancel"])
            sublime.status_message(MSG["cancel"])
            return

        if index == 0:
            self.new_session = {}
            self.choose_location(self.window.show_input_panel, "Session name", "", self.choose_host, 0, lambda: sublime.status_message(MSG["cancel"]))
        else:
            self.choose_location(self.window.show_input_panel, "Folder name", "", self.save_folder, 0, lambda: sublime.status_message(MSG["cancel"]))

    def save_folder(self, folder_name):
        # Saving folder name
        self.cur_location.append({"name": folder_name, "children": []})

        updateSesions(self.sessions)

    def choose_location(self, callback, *args):

        self.cur_location = self.sessions
        self.cur_folders = [i for i in range(len(self.cur_location)) if "children" in self.cur_location[i]]

        def choose(index):
            # If nothing is chosen
            if index == -1:
                print(MSG["cancel"])
                sublime.status_message(MSG["cancel"])
                return

            if index == 0:  # Click on the title...
                pass
            elif index == 1:  # If "HERE" is chosen
                callback(*args)
                return
            else:
                self.cur_location = self.cur_location[self.cur_folders[index - 2]]["children"]

            self.cur_folders = [i for i in range(len(self.cur_location)) if "children" in self.cur_location[i]]

            self.window.show_quick_panel(["### Choose location ###", "<HERE>"] + [self.cur_location[i]["name"] for i in self.cur_folders], choose)

        choose(0)

    def choose_host(self, session_name):
        # Session name check
        session_name = session_name.strip()

        if not session_name:
            print(MSG["cancel"])
            sublime.status_message(MSG["cancel"])
            return

        if session_name in self.sessions:
            sublime.error_message(MSG["already_has_this"])
            raise

        # Saving and asking for host
        self.new_session["name"] = session_name
        self.window.show_input_panel("Server host", "127.0.0.1", self.choose_port, 0, lambda: sublime.status_message(MSG["cancel"]))

    def choose_port(self, session_host):
        # Session host check
        session_host = session_host.strip()
        if not session_host:
            print(MSG["cancel"])
            sublime.status_message(MSG["cancel"])
            return

        # If ipv4 is recognized:
        ipv4_match = re_match(IPV4_REGEX, session_host)
        if ipv4_match is not None:
            session_host = ".".join(ipv4_match.group(i) for i in range(1, 5))

        # Saving host and asking for port
        self.new_session["host"] = session_host
        self.window.show_input_panel("Connection port", "22", self.choose_login, 0, lambda: sublime.status_message(MSG["cancel"]))

    def choose_login(self, session_port):
        # Session port check
        try:
            session_port = int(session_port)
            wrong = session_port <= 0
        except Exception:
            wrong = True

        if wrong:
            print(MSG["cancel"])
            sublime.status_message(MSG["cancel"])
            sublime.error_message(MSG["wrong_port"])
            raise

        # Saving port and asking for username
        self.new_session["port"] = session_port
        self.window.show_input_panel("Username (optional)", "", self.choose_password, 0, lambda: sublime.status_message(MSG["cancel"]))

    def choose_password(self, session_login):
        # Saving login
        if session_login.strip():
            self.new_session["login"] = session_login.strip()

        # Asking for password
        self.window.show_input_panel("Password (optional)", "", self.save_session, 0, lambda: sublime.status_message(MSG["cancel"]))

    def save_session(self, session_password):
        # Saving password
        if session_password.strip():
            self.new_session["password"] = session_password.strip()

        self.cur_location.append(self.new_session)

        updateSesions(self.sessions)


class QuickputtyRemove(sublime_plugin.WindowCommand):
    '''Responsible for removing sessions.
       Handles "quickputty_remove" command.'''

    def run(self):
        # Get sessions
        with open(SESSIONS_PATH, 'r', encoding="utf-8") as file:
            try:
                self.sessions = sublime.decode_value(file.read().strip())
            except Exception:
                sublime.error_message(MSG["invalid_json"])
                return

        # Check sessions
        if checkSessions(self.sessions) is None:
            sublime.status_message(MSG["cancel"])
            return

        # If sessions list is empty
        if not self.sessions:
            sublime.message_dialog(MSG["no_sessions"])
            return

        self.last_index = -1
        self.last_location = None
        self.cur_location = self.sessions

        def choose(index):
            if index == -1:
                return

            if index >= 0:

                if self.last_location is None:
                    index += 1

                # "***THIS FOLDER***" selected
                if index == 0:
                    item = self.last_location[self.last_index - 1]

                    if sublime.yes_no_cancel_dialog(
                        "Folder \"{}\" ({} subitems) will be deleted. Are you sure?".format(item["name"], len(item["children"]))
                    ) == sublime.DIALOG_YES:
                        # User agreed to remove, removing:
                        del self.last_location[self.last_index - 1]

                        print(MSG["remove_folder"].format(name=item["name"]))
                        sublime.status_message(MSG["remove_folder"].format(name=item["name"]))

                        updateSesions(self.sessions)
                    else:
                        print(MSG["cancel"])
                        sublime.status_message(MSG["cancel"])
                    return

                item = self.cur_location[index - 1]

                # If this is a session:
                if "children" not in item:
                    if sublime.yes_no_cancel_dialog(
                        "Session \"{}\" ({}) will be deleted. Are you sure?".format(item["name"], item["host"])
                    ) == sublime.DIALOG_YES:

                        # User agreed to remove, removing:
                        del self.cur_location[index - 1]

                        print(MSG["remove_session"].format(name=item["name"]))
                        sublime.status_message(MSG["remove_session"].format(name=item["name"]))

                        updateSesions(self.sessions)

                    else:
                        print(MSG["cancel"])
                        sublime.status_message(MSG["cancel"])

                    return

                # Else: it is a folder:
                self.last_index = index
                self.last_location = self.cur_location
                self.cur_location = item["children"]

            if self.cur_location == self.sessions:
                # This is the root of the sessions -> Not asking "***THIS FOLDER***"
                self.window.show_quick_panel([item["name"] for item in self.cur_location], choose)
            else:
                self.window.show_quick_panel(["***THIS FOLDER***"] + [item["name"] for item in self.cur_location], choose)

        choose(-2)


class Files(sublime_plugin.EventListener):
    '''Controls the behavior of settings file and sessions file and updates the .sublime-menu file.'''

    # Does not work in sublime-package file :(
    # Currently disabled
    # def on_load(self, view):
    #     if view.file_name() == SETTINGS_PATH:
    #         # Preventing the user from changing the default settings.
    #         print("YES")
    #         view.set_read_only(True)

    def on_post_save_async(self, view):

        # If the saved file is QuickPuTTY's sessions.json
        if view.file_name() == SESSIONS_PATH:

            # (Re-)Creating file for storing sessions

            # Check if this is a file (just in case)
            if os.path.isfile(SESSIONS_PATH):

                # Reading sessions
                with open(SESSIONS_PATH, 'r', encoding="utf-8") as file:
                    try:
                        sessions = sublime.decode_value(file.read().strip())
                    except Exception:
                        sublime.error_message(MSG["invalid_sessions_json"])
                        raise

            else:
                sessions = []

            # Checking sessiosn
            sessions = checkSessions(sessions)
            if sessions is None:
                return

            updateSesions(sessions)


class QuickputtyReadme(sublime_plugin.WindowCommand):
    '''Responsible for showing the README file when installing the package.
       Handles "quickputty_readme" command.'''

    def run(self):
        view = sublime.active_window().new_file()
        view.set_read_only(True)
        view.set_name(PACKAGE_NAME)
        view.add_phantom("test", sublime.Region(0, 0), INSTALL_HTML, sublime.LAYOUT_BELOW, lambda url: sublime.run_command("open_url", args={"url": url}))


def onLoad() -> None:
    '''This function can run asynchronously at startup'''
    # Check settings
    if not checkSettings():
        return

    # Creating "User file"
    os.makedirs(mkpath(USER_PACKAGE_PATH), exist_ok=True)

    # (Re-)Creating file for storing sessions
    if os.path.isfile(SESSIONS_PATH):
        with open(SESSIONS_PATH, 'r', encoding="utf-8") as file:
            try:
                sessions = sublime.decode_value(file.read().strip())
            except Exception:
                sublime.error_message(MSG["invalid_sessions_json"])
                raise
            sessions = checkSessions(sessions)
            if sessions is None:
                return
    else:
        sessions = []

    # Checking sessiosn
    sessions = checkSessions(sessions)
    if sessions is None:
        return

    updateSesions(sessions)


def plugin_loaded() -> None:
    # from package_control import events

    global MSG
    global TEMPLATE_MENU
    global INSTALL_HTML

    MSG = sublime.decode_value(sublime.load_resource("Packages/QuickPuTTY/communication.json"))
    TEMPLATE_MENU = sublime.decode_value(sublime.load_resource("Packages/QuickPuTTY/template_menu.json"))
    INSTALL_HTML = sublime.load_resource("Packages/QuickPuTTY/installation.html")

    # Show README
    try:
        sublime.load_resource("Packages/User/QuickPuTTY/sessions.json")
    except FileNotFoundError:
        QuickputtyReadme(sublime.active_window()).run()

    # if events.install(PACKAGE_NAME):
    #     QuickputtyReadme(sublime.active_window()).run()

    onLoad()
    # sublime.set_timeout_async(onLoad, 800)


def plugin_unloaded() -> None:
    # Disable settings check (after saving the file)
    sublime.load_settings(PACKAGE_NAME + ".sublime-settings").clear_on_change("check_settings")

    # Removing menu file
    if os.path.exists(MENU_PATH):
        os.remove(MENU_PATH)
