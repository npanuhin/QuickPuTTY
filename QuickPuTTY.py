#  Copyright (c) 2020-2022 Nikita Paniukhin  │
#       Licensed under the MIT license       │
# ───────────────────────────────────────────┘

import sublime_plugin
import sublime

from json import dump as json_dump
from re import match as re_match, sub as re_sub
from subprocess import Popen
from copy import deepcopy
from time import sleep
import os


# ================================================ USER PART =================================================

PACKAGE_NAME = "QuickPuTTY"

# If you want to edit default settings:  (!!! Does not work in sublime-package file. Help wanted !!!)
EDIT_DEFAULT_SETTINGS = True

# TODO: Preventing the user from changing the default settings (in .sublime-package file)

# =============================================================================================================


# IPV4_REGEX is used to prettify IP addresses, optional enhancement
IPV4_REGEX = r"(?:https?:?[\/\\]{,2})?(\d+)[\.:,](\d+)[\.:,](\d+)[\.:,](\d+)(?::\d+)?"


def mkpath(*paths):
    '''Combines paths and normalizes the result'''
    return os.path.normpath(os.path.join(*paths))


USER_PACKAGE_PATH = mkpath(sublime.packages_path(), "User", PACKAGE_NAME)
SETTINGS_PATH = mkpath(sublime.packages_path(), PACKAGE_NAME, f"{PACKAGE_NAME}.sublime-settings")
SESSIONS_PATH = mkpath(USER_PACKAGE_PATH, "sessions.json")
MENU_PATH = mkpath(USER_PACKAGE_PATH, "Main.sublime-menu")


def sublimeAssert(expression, error_message=None):
    '''Replacement for Python's "assert" keyword'''
    if expression is False:
        sublime.error_message(MSG["assertion_failed"] if error_message is None else error_message)

    return expression


def sublimePrint(string, debug=True):
    if debug:
        print(string)
    sublime.status_message(string)


# =============================================================================================================

def getSettings():
    '''Checks whether the format of the settings is correct. Returns settings object or None'''

    settings = sublime.load_settings(f"{PACKAGE_NAME}.sublime-settings")

    # Check if all settings exist
    if not sublimeAssert(
        all(settings.has(setting) for setting in ("PuTTY_exec", "pure_PuTTY_enabled")),
        MSG["setting_not_found"]
    ):
        return None

    # Renewing handler
    settings.clear_on_change("update_settings")
    settings.add_on_change("update_settings", reloadSettings)

    # Checking "PuTTY_exec" setting
    if not sublimeAssert(isinstance(settings.get("PuTTY_exec"), (str, list)), MSG["invalid_PuTTY_exec"]):
        return None

    if isinstance(settings.get("PuTTY_exec"), list):
        if not sublimeAssert(
            all(isinstance(item, str) for item in settings.get("PuTTY_exec")),
            MSG["invalid_PuTTY_exec"]
        ):
            return None

    # Checking "pure_PuTTY_enabled" setting
    if not sublimeAssert(isinstance(settings.get("pure_PuTTY_enabled"), bool), MSG["invalid_pure_PuTTY_enabled"]):
        return None

    # print("{}: Settings checked".format(PACKAGE_NAME))
    return settings


def reloadSettings():
    # getSettings()  # Currently not needed because there is the same check in reloadSessions
    reloadSessions()


def checkSessions(sessions):
    '''Checks whether the format of the sessions is correct. Recursive. Returns True/False'''

    if not sublimeAssert(isinstance(sessions, list), MSG["invalid_sessions"]):
        return False

    for item in sessions:
        if not sublimeAssert(
            isinstance(item, dict) and
            "name" in item and isinstance(item["name"], str),

            MSG["invalid_sessions"]
        ):
            return False

        if "children" in item:
            if not sublimeAssert(checkSessions(item["children"]), MSG["invalid_sessions"]):
                return False
        else:
            if not sublimeAssert(
                "host" in item and isinstance(item["host"], str) and re_match(IPV4_REGEX, item["host"]) is not None and
                "port" in item and isinstance(item["port"], int) and item["port"] >= 0 and
                ("login" not in item or isinstance(item["login"], str)) and
                ("password" not in item or isinstance(item["password"], str)),

                MSG["invalid_sessions"]
            ):
                return False

    return True


def updateSesions(sessions):
    '''Stores sessions to "sessions.json" and creates a .sublime-menu file'''

    def build(item):
        result = {
            "caption": item["name"],
            "mnemonic": item["name"][0] if item["name"] else None
        }

        if "children" in item:
            # Folder
            result["children"] = [build(subitem) for subitem in item["children"]]

        else:
            # Session
            result["command"] = "quickputty_open"
            result["args"] = {
                "host": item["host"],
                "port": item["port"]
            }

            if "login" in item and item["login"]:
                result["args"]["login"] = item["login"]

            if "password" in item and item["password"]:
                result["args"]["password"] = item["password"]

        return result

    # Storing sessions to "sessions.json"
    with open(SESSIONS_PATH, 'w', encoding="utf-8") as file:
        json_dump(sessions, file, ensure_ascii=False, indent=4, sort_keys=False)

    # Creating a .sublime-menu file
    data = deepcopy(TEMPLATE_MENU)

    # Structure: "Open PuTTY" command | "New", "Manage", "Remove", etc. options | Root folder
    data[0]["children"] = (data[0]["pure_PuTTY_enabled"] if getSettings().get("pure_PuTTY_enabled") else []) + data[0]["children"] + [build(item) for item in sessions]

    # Removing temporary storage
    del data[0]["pure_PuTTY_enabled"]

    with open(MENU_PATH, 'w', encoding="utf-8") as file:
        json_dump(data, file, ensure_ascii=False, indent=4, sort_keys=False)

    sublimePrint(MSG["sessions_reloaded"])


def reloadSessions():
    # Renewing file for storing sessions
    sessions = None
    if os.path.isfile(SESSIONS_PATH):
        with open(SESSIONS_PATH, encoding="utf-8") as file:
            try:
                sessions = sublime.decode_value(file.read())  # Note: the result can also be None
            except Exception:
                sublime.error_message(MSG["invalid_sessions_json"])
                return

    if sessions is None:
        sessions = []

    # Checking and updating sessios
    if not checkSessions(sessions):
        return

    updateSesions(sessions)


class QuickputtyOpen(sublime_plugin.WindowCommand):
    '''Responsible for opening PuTTY'''

    def run(self, host=None, port=22, login="", password=""):
        run_command = getSettings().get("PuTTY_exec")

        if host is not None:
            if isinstance(run_command, str):
                run_command = list(run_command.split())

            run_command += ("-ssh", host, "-P", str(port))

            if login:
                run_command += ("-l", login)
            if password:
                run_command += ("-pw", password)

        Popen(run_command)


class QuickputtyNew(sublime_plugin.WindowCommand):
    '''Responsible for creating new sessions and folders'''

    def run(self):
        with open(SESSIONS_PATH, encoding="utf-8") as file:
            try:
                self.sessions = sublime.decode_value(file.read())  # Note: the result can also be None
            except Exception:
                sublime.error_message(MSG["invalid_sessions_json"])
                return

        if self.sessions is None:
            self.sessions = []

        if not checkSessions(self.sessions):
            sublimePrint(MSG["canel"])
            return

        self.new_session = {}  # Creating storage for new session

        self.window.show_quick_panel(("Session", "Folder"), self.chooseType)

    def chooseType(self, index):
        if index == -1:  # Nothing is selected
            sublimePrint(MSG["cancel"])
            return

        self.chooseLocation(self.window.show_input_panel, (
            "Folder name" if index else "Session name",
            "",
            self.saveFolder if index else self.chooseHost,
            0,
            lambda: sublimePrint(MSG["cancel"])
        ))

    def saveFolder(self, folder_name):
        if not folder_name.strip():
            sublimePrint(MSG["cancel"])
            return

        sublimePrint(MSG["folder_created"].format(
            name=folder_name.strip(),
            location=(' in "' + "/".join(self.cur_location_path)) + '"' if self.cur_location_path else "")
        )

        self.cur_options.append({
            "name": folder_name.strip(),
            "children": []
        })

        updateSesions(self.sessions)

    def chooseLocation(self, callback, args):
        self.cur_options = self.sessions
        self.cur_location_path = []

        self.cur_folder_indexes = [index for index, obj in enumerate(self.cur_options) if "children" in obj]

        def choose(index):
            if index == -1:  # Nothing is selected
                sublimePrint(MSG["cancel"])
                return

            if index == 1:   # Click on "<HERE>"
                callback(*args)
                return

            if index != 0:   # Click NOT on the title (index = 0)
                self.cur_location_path.append(self.cur_options[self.cur_folder_indexes[index - 2]]["name"])
                self.cur_options = self.cur_options[self.cur_folder_indexes[index - 2]]["children"]

            self.cur_folder_indexes = [index for index, obj in enumerate(self.cur_options) if "children" in obj]

            self.window.show_quick_panel(
                [
                    "### Choose location{} ###".format((": " + "/".join(self.cur_location_path)) if self.cur_location_path else ""),
                    "<HERE>"
                ] +
                [self.cur_options[index]["name"] for index in self.cur_folder_indexes],
                choose
            )

        choose(0)

    def chooseHost(self, session_name):
        if not session_name.strip():
            sublimePrint(MSG["cancel"])
            return

        if session_name in (item["name"] for item in self.cur_options):
            sublime.error_message(MSG["session_already_exists"])
            return

        self.new_session["name"] = session_name
        self.window.show_input_panel("Server host", "127.0.0.1", self.choosePort, 0, lambda: sublimePrint(MSG["cancel"]))

    def choosePort(self, session_host):
        if not session_host.strip():
            sublimePrint(MSG["cancel"])
            return

        # IPv4 is recognized:
        ipv4_match = re_match(IPV4_REGEX, session_host)
        if ipv4_match is not None:
            session_host = ".".join(ipv4_match.groups())

        self.new_session["host"] = session_host
        self.window.show_input_panel("Connection port", "22", self.chooseLogin, 0, lambda: sublimePrint(MSG["cancel"]))

    def chooseLogin(self, session_port):
        try:
            session_port = int(session_port)
            port_valid = (session_port >= 0)

        except Exception:
            port_valid = False

        if not sublimeAssert(port_valid, MSG["wrong_port"]):
            sublimePrint(MSG["cancel"])
            return

        self.new_session["port"] = session_port
        self.window.show_input_panel("Username (optional)", "", self.choosePassword, 0, lambda: sublimePrint(MSG["cancel"]))

    def choosePassword(self, session_login):
        if session_login.strip():
            self.new_session["login"] = session_login.strip()

        self.window.show_input_panel("Password (optional)", "", self.saveSession, 0, lambda: sublimePrint(MSG["cancel"]))

    def saveSession(self, session_password):
        if session_password.strip():
            self.new_session["password"] = session_password.strip()

        self.cur_options.append(self.new_session)

        sublimePrint(MSG["session_created"].format(
            name=self.new_session["name"],
            host=self.new_session["host"],
            location=(' in "' + "/".join(self.cur_location_path)) + '"' if self.cur_location_path else "")
        )

        updateSesions(self.sessions)


class QuickputtyRemove(sublime_plugin.WindowCommand):
    '''Responsible for removing sessions and folders'''

    def run(self):
        with open(SESSIONS_PATH, encoding="utf-8") as file:
            try:
                self.sessions = sublime.decode_value(file.read())  # Note: the result can also be None
            except Exception:
                sublime.error_message(MSG["invalid_sessions_json"])
                return

        if self.sessions is None:
            self.sessions = []

        if not checkSessions(self.sessions):
            sublimePrint(MSG["canel"])
            return

        if not self.sessions:
            sublime.message_dialog(MSG["nothing_to_remove"])
            return

        self.last_location = None         # DEV: last_location = previous list[items{}] = list[items{one of which is item{"children"=`self.cur_options`}}]
        self.last_index = -1

        self.cur_options = self.sessions  # DEV: cur_options   = list[items{}]
        self.cur_location_path = []

        def choose(index):
            if index == -1:
                sublimePrint(MSG["cancel"])
                return

            if index >= 0:
                if self.cur_options == self.sessions:
                    index += 1

                if index == 0:  # Click on "*** THIS FOLDER ***"
                    item = self.last_location[self.last_index - 1]

                    if sublime.yes_no_cancel_dialog(
                        "Folder \"{}\" ({} subitems) will be deleted. Are you sure?".format(item["name"], len(item["children"]))
                    ) == sublime.DIALOG_YES:

                        del self.last_location[self.last_index - 1]

                        sublimePrint(MSG["folder_removed"].format(name=item["name"], subitems_count=len(item["children"])))
                        updateSesions(self.sessions)

                    else:
                        sublimePrint(MSG["cancel"])

                    return

                selected = self.cur_options[index - 1]  # DEV: selected = item{}

                if "children" not in selected:  # If a session is selected
                    if sublime.yes_no_cancel_dialog(
                        "Session \"{}\" ({}) will be deleted. Are you sure?".format(selected["name"], selected["host"])
                    ) == sublime.DIALOG_YES:

                        del self.cur_options[index - 1]

                        sublimePrint(MSG["session_removed"].format(name=selected["name"], host=selected["host"]))
                        updateSesions(self.sessions)

                    else:
                        sublimePrint(MSG["cancel"])

                    return

                # Else: a folder is selected

                self.last_location = self.cur_options
                self.last_index = index

                self.cur_location_path.append(selected["name"])
                self.cur_options = selected["children"]

            self.window.show_quick_panel(
                (["*** THIS FOLDER ***"] if self.cur_options != self.sessions else []) +
                [("[{}]".format(item["name"]) if "children" in item else item["name"]) for item in self.cur_options],
                choose
            )

        choose(index=-2)


class Files(sublime_plugin.EventListener):
    '''Controls the behavior of settings file and sessions file and updates the .sublime-menu file'''

    # Does not work in sublime-package file. Help wanted. TODO
    def on_load_async(self, view):
        '''Preventing the user from changing the default settings'''

        if not EDIT_DEFAULT_SETTINGS and mkpath(view.file_name()) == SETTINGS_PATH:
            view.set_read_only(True)

    def on_post_save_async(self, view):
        if mkpath(view.file_name()) == SESSIONS_PATH:
            reloadSessions()


class QuickputtyReadme(sublime_plugin.WindowCommand):
    '''Responsible for showing the README file when installing the package'''

    def run(self):
        view = sublime.active_window().new_file()
        view.set_read_only(True)
        view.set_scratch(True)
        view.set_name(PACKAGE_NAME)
        view.add_phantom(
            "QuickPuTTY README",
            sublime.Region(0, 0),
            INSTALL_HTML,
            sublime.LAYOUT_INLINE,
            lambda url: sublime.run_command("open_url", args={"url": url})
        )


def onLoad():
    '''This function should run asynchronously on plugin startup'''

    global MSG
    global TEMPLATE_MENU
    global INSTALL_HTML

    while True:
        try:
            sublime.load_resource(f"Packages/{PACKAGE_NAME}/communication.json")
            break
        except FileNotFoundError:
            sleep(0.1)

    MSG = sublime.decode_value(sublime.load_resource(f"Packages/{PACKAGE_NAME}/communication.json"))
    TEMPLATE_MENU = sublime.decode_value(sublime.load_resource(f"Packages/{PACKAGE_NAME}/template_menu.json"))
    INSTALL_HTML = sublime.load_resource(f"Packages/{PACKAGE_NAME}/installation.html")

    for key, value in MSG.items():
        MSG[key] = re_sub(r"{([\w\d_]+)}", r"{{\1}}", value).replace(r"{{package_name}}", r"{package_name}").format(package_name=PACKAGE_NAME)

    # Show README
    try:
        sublime.load_resource(f"Packages/User/{PACKAGE_NAME}/sessions.json")
    except FileNotFoundError:
        QuickputtyReadme(sublime.active_window()).run()

    # QuickputtyReadme(sublime.active_window()).run()  # For debug

    # Check settings
    if getSettings() is None:
        return

    # Creating folder in "Packages/User"
    os.makedirs(mkpath(USER_PACKAGE_PATH), exist_ok=True)

    reloadSessions()


def plugin_loaded():
    sublime.set_timeout_async(onLoad)


def plugin_unloaded():
    # Disable settings check after saving
    getSettings().clear_on_change("update_settings")

    # Removing menu file
    if os.path.exists(MENU_PATH):
        os.remove(MENU_PATH)
