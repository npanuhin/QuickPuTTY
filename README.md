<h1 align="center">QuickPuTTY</h1>

<!-- <div class="badges" align="center">
	<a href="https://packagecontrol.io/packages/QuickPuTTY" target="_blank" title="Package Control: QuickPuTTY"><img src="https://img.shields.io/badge/WIN-LINUX-f08989?labelColor=99c1f0&style=flat-square&cacheSeconds=260000" alt="WIN|LINUX"></a>
	<a href="https://packagecontrol.io/packages/QuickPuTTY" target="_blank" title="Package Control: QuickPuTTY"><img src="https://img.shields.io/packagecontrol/dt/QuickPuTTY?color=success&style=flat-square&cacheSeconds=300"></a>
	<a href="https://npanuhin.me/license" target="_blank" title="license: MIT"><img alt="license: MIT" src="https://img.shields.io/badge/license-MIT-blue.svg?color=informational&style=flat-square&cacheSeconds=260000"></a>
	<br>
</div> -->

<!-- Archived badges: -->
<div class="badges" align="center">
	<img src="https://img.shields.io/badge/WIN-LINUX-f08989?labelColor=99c1f0&style=flat-square&cacheSeconds=260000" alt="WIN|LINUX">
	<img src="https://img.shields.io/badge/downloads-616-f08989?color=success&style=flat-square&cacheSeconds=26000" alt="downloads|616">
	<a href="https://npanuhin.me/license" target="_blank" title="license: MIT"><img alt="license: MIT" src="https://img.shields.io/badge/license-MIT-blue.svg?color=informational&style=flat-square&cacheSeconds=260000"></a>
	<br>
</div>

<br>

> <h3 align="center">🚧 Unfortunately, this plugin has reached the end of its life 😔</h3>
>
> The current version in the `master` branch requires a lot of fixing and refactoring (and is simply broken), so I can't just post it, although I really wanted to update the version before archiving the project


***QuickPuTTY*** is a plugin for [Sublime Text](https://sublimetext.com "Visit sublimetext.com") that allows you to save SSH sessions for quick access to them. It will be useful for those who often use SSH.

Supports folders with a unique navigation system, making it easy to add or remove sessions on the go (manual JSON editing is also possible).

Works with the free open source terminal emulator [PuTTY](https://putty.org "Visit putty.org").

Check out how quickly you can start an SSH session **without entering username and password**:

![](./media/usage.gif)

## Installation

Plugin is available on [Package Control](https://packagecontrol.io/packages/QuickPuTTY "Visit QuickPuTTY page on packagecontrol.io") and can be installed as follows:

1. Press <kbd>Ctrl + Shift + P</kbd>, then enter `Package Control: Install Package`
2. Choose `QuickPuTTY` in the list of available packages

After installation, you can find settings and README by going to `Preferences > Package Settings > QuickPuTTY` in nav-bar.

![](./media/installation.gif)

## Usage

#### Create folder

1. Go to `PuTTY > New session/folder` in the nav-bar and select `Folder` option
2. [Choose location](#choosing-location) to place new folder
3. Enter folder name

#### Create session

1. Go to `PuTTY > New session/folder` in the nav-bar and select `Session` option
2. [Choose location](#choosing-location) to place new session
3. Enter *server host/ip*, *port*, *username* and *password* (last two are optional)

#### Edit sessions and folders

1. Go to `PuTTY > Manage sessions` in the nav-bar
2. Change the data presented in plain json format
3. Do not forget to save the file

#### Remove session/folder

1. Go to `PuTTY > Remove session/folder` in the nav-bar
2. Select a session or folder you want to remove using the [*Choose location*](#choosing-location) system

### Choosing location

At each stage, you'll see a list of options:

|           item          |                            meaning                                  |
|:-----------------------:|:-------------------------------------------------------------------:|
| ### Choose location ### |                          Just a title                               |
|         \<HERE\>        | Select this if you want to place session/folder in current location |
|        {folder_№}       |            Select a folder name to navigate into it                 |

------------------------------------------------------------------------------------------------------------------------

This plugin was tested in `Sublime Text 4143` on `Windows 10 (22H2)` and `Ubuntu 20.04.5` (iOS support coming soon).
If you find a bug, mistake, or typo, you are very welcome to open a [new GitHub issue](https://github.com/npanuhin/QuickPuTTY/issues/new "Create a new GitHub Issue in the QuickPuTTY repository") or contact me directly (e.g., on [npanuhin.me](https://npanuhin.me "Visit npanuhin.me")).

You can find the latest version of PuTTY on [putty.org](https://putty.org "Visit putty.org")

------------------------------------------------------------------------------------------------------------------------

## Development

#### Code linting
```bash
pip install -U -r ".github/flake8.requirements.txt"
flake8 --show-source --statistics

# To install pre-commit hook:
pip install -U pre-commit
pre-commit install --config ".github/.pre-commit-config.yaml"
```

#### TODO
- "Do not forget to save the file" — add autosave
- JSON -> TOML (or other language with less "control characters")
- Test on iOS

------------------------------------------------------------------------------------------------------------------------

Copyright © 2023 Nikita Panuhin ([MIT](https://npanuhin.me/license "Visit https://npanuhin.me/license"))
