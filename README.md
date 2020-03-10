<h1 align="center">QuickPuTTY</h1>

<div class="badges" align="center">
	<a href="https://packagecontrol.io/packages/QuickPuTTY" target="_blank" title="Package Control: QuickPuTTY"><img src="https://img.shields.io/packagecontrol/dt/QuickPuTTY?color=success"></a>
	<a href="http://n-panuhin.info/license.html" target="_blank" title="license: MIT"><img alt="license: MIT" src="https://img.shields.io/badge/license-MIT-blue.svg?color=informational"></a>
</div>


*QuickPuTTY* is a plugin for Sublime Text 3 that allows you to save SSH sessions for quick access to them.

**Warning!** Usernames and passwords are stored using symmetric-key encryption (can be easily decoded). Make sure no one can access them.

## Installation

The plugin can be installed via [Package Control](https://packagecontrol.io "Visit packagecontrol.io"):

1. Press `Ctrl + Shift + P`, then enter `Package Control: Install Package` (or just `ins`)
2. Choose `QuickPuTTY` in the list of available packages

You can change encryption keys in plugin settings:

Go to `Preferences > Package Settings > QuickPuTTY Settings`

## Usage

#### Create session

1. Go to `PuTTY > New session`
2. Enter server host/ip, port, username and password (last two are optional)

#### Edit sessions

1. Go to `PuTTY > Manage sessions`
2. Edit session data (if you are editing password, do not forget to specify “encrypt”)
3. Do not forget to save file

#### Remove session

1. Go to `PuTTY > Remove session`
2. Choose a session that you want to remove

-------------------------------------------

The plugin was tested on `Windows 10 (1809) x64` and `Ubuntu 18.04.03`.
If you have found a bug or mistake, you are very welcome to contact me on [n-panuhin.info](https://n-panuhin.info "Visit n-panuhin.info")

You can find the latest version of PuTTY on [putty.org](https://putty.org "Visit putty.org")

-------------------------------------------

Copyright &copy; 2020 Nikita Paniukhin

License: [MIT](http://n-panuhin.info/license.html "Visit n-panuhin.info/license")