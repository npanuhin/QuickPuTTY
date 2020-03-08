import sublime
import sublime_plugin
from subprocess import Popen, PIPE
import os
from re import match as re_match
from copy import deepcopy

from .QuickPuTTY_encryption import QuickPuTTYEncryption

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
    "no_sessions": "You have not saved any sessions :(\nGo to \"PuTTY > New session\" to add one!",
    "encrypt_changed_password": "// If you change the password, specify (\"encrypt\": {something, e.g. true}) as one of the session parameters\n",
    "bad_json": "Sublime Text cannot decode JSON. Please check the file for errors.",
    "bad_keys": "The keys specified in the settings are incorrect. Change them and restart Quick PuTTY (or Sublime Text)."
}

IPV4_REGEX = r"(?:https?:?[\/\\]{,2})?(\d+)[\.:,](\d+)[\.:,](\d+)[\.:,](\d+)(?::\d+)?"

# JSON is saved this way only because Package Control does not allow
# files to be opened when the plugin is packed in .sublime-package archive

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
    '''Combines paths and normalizes the result'''
    return os.path.normpath(os.path.join(*paths))


def runCommand(command, result=False):
    '''Runs a system command'''
    if type(command) is str:
        command = list(command.split())
    if result:
        return Popen(command, stdout=PIPE, stderr=PIPE).communicate()
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
    '''Checks if the session format is correct'''
    if not isinstance(sessions, dict):
        sublime.error_message("bad_json")

    for name in sessions:
        if not isinstance(sessions[name], dict) or "host" not in sessions[name] or "port" not in sessions[name]:
            sublime.error_message("bad_json")
            break

        if "encrypt" in sessions[name]:
            del sessions[name]["encrypt"]
            sessions[name]["password"] = encryption.encrypt(sessions[name]["password"])
    else:
        return sessions


class QuickputtyOpen(sublime_plugin.WindowCommand):
    '''Responsible for opening PuTTY.  Handles "quickputty_open" command.'''

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
                password=" -pw " + encryption.decrypt(password) if password else "",
            ))


class QuickputtyNew(sublime_plugin.WindowCommand):
    '''Responsible for creating new sessions. Handles "quickputty_new" command.'''

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
    '''Responsible for removing sessions. Handles "quickputty_remove" command.'''

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
            view.set_read_only(False)

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


def handleReadmeClick(string):
    sublime.run_command("open_url", args={"url": string})


def showReadme():
    # with open(mkpath(sublime.packages_path(), "QuickPuTTY", "messages", "install.html"), 'r', encoding="utf-8") as file:
    #     html = file.read().strip()

    html = """<body id="quickputty-readme">
    <style>code{padding:0 .3em}html.dark code{background-color:#444}html.light code{background-color:#eee}h1{margin-top:0;font-size:2.3rem}h3{font-size:1.4rem}.hr{width:999rem;height:.2rem}html.dark .hr{background-color:#444}html.light .hr{background-color:#ddd}</style>
    <h1>QuickPuTTY</h1><p><em>QuickPuTTY</em> is a plugin for Sublime Text 3 that allows you to save SSH sessions for quick access to them.</p><p><strong>Warning!</strong> Usernames and passwords are stored using symmetric-key encryption (can be easily decoded). Make sure no one can access them.</p><h3>Installation</h3><p style="margin-bottom:0">If you see this message in Sublime Text, you are already completed this step :)</p><p style="margin-top:0">Otherwise, visit <a href="https://github.com/Nikita-Panyuhin/QuickPuTTY">QuickPuTTY github page</a> to find all information.</p><p style="margin-bottom:0">You can change encryption keys in plugin settings:</p><p style="margin-top:0.1rem">Go to <code>Preferences &gt; Package Settings &gt; QuickPuTTY Settings</code></p><h3>Usage</h3><h4>Create session:</h4><ol><li>Go to <code>PuTTY &gt; New session</code></li><li>Enter server host/ip, port, username and password (last two are optional)</li></ol><h4>Edit sessions:</h4><ol><li>Go to <code>PuTTY &gt; Manage sessions</code></li><li>Edit session data (if you are editing password, do not forget to specify “encrypt”)</li><li>Do not forget to save file</li></ol><h4>Remove session:</h4><ol><li>Go to <code>PuTTY &gt; Remove session</code></li><li>Choose a session that you want to remove</li></ol><div class="hr"></div><p>The plugin was tested on <code>Windows 10 (1809) x64</code> and <code>Ubuntu 18.04.03</code>. If you have found a bug or mistake, you are very welcome to contact me on <a href="https://n-panuhin.info" title="Visit n-panuhin.info">n-panuhin.info</a></p><p>You can find the latest version of PuTTY on <a href="https://putty.org" title="Visit putty.org">putty.org</a></p><div class="hr"></div><p style="margin-bottom:0.3rem">Copyright © 2020 Nikita Paniukhin</p><a href="http://n-panuhin.info/license.html">
    <img style="width:7rem;height:1.45rem" src="data:image/png;base64,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"></a>
    </body>"""

    view = sublime.active_window().new_file()
    view.set_read_only(True)
    view.set_name("QuickPuTTY")
    view.add_phantom("test", sublime.Region(0, 0), html, sublime.LAYOUT_BELOW, handleReadmeClick)


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

    settings = sublime.load_settings(PACKAGE_NAME + ".sublime-settings")

    # Show README
    if events.install(PACKAGE_NAME):
        showReadme()

    key_one = settings.get("encryption_key_one")
    key_two = settings.get("encryption_key_two")
    if not (isinstance(key_one, int) and isinstance(key_two, str)):
        sublime.error_message(MSG["bad_keys"])
        return

    encryption = QuickPuTTYEncryption(key_one, key_two)

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

    with open(SESSIONS_PATH, "w", encoding="utf-8") as file:
        file.write(MSG["encrypt_changed_password"] + sublime.encode_value(sessions, True))

    with open(SESSIONS_PATH, "r", encoding="utf-8") as file:
        makeSessionMenuFile(sessions)


def plugin_unloaded():
    if os.path.exists(MENU_PATH):
        os.remove(MENU_PATH)

    if sublime.load_settings(PACKAGE_NAME + ".sublime-settings").get("clear_on_remove", False):
        os.remove(SESSIONS_PATH)
        try:
            os.rmdir(USER_PACKAGE_PATH)
        except Exception:
            sublime.error_message("Can not remove QuickPuTTY user directory.")
