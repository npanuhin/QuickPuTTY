<h1 align="center">QuickPuTTY</h1>

<div class="badges" align="center">
	<a href="https://packagecontrol.io/packages/QuickPuTTY"><img src="https://img.shields.io/badge/WIN-LINUX-f08989?labelColor=99c1f0&style=flat-square&cacheSeconds=260000" alt="WIN|LINUX"></a>
	<a href="https://packagecontrol.io/packages/QuickPuTTY" target="_blank" title="Package Control: QuickPuTTY"><img src="https://img.shields.io/packagecontrol/dt/QuickPuTTY?color=success&style=flat-square&cacheSeconds=1000"></a>
	<a href="http://n-panuhin.info/license.html" target="_blank" title="license: MIT"><img alt="license: MIT" src="https://img.shields.io/badge/license-MIT-blue.svg?color=informational&style=flat-square&cacheSeconds=260000"></a>
	<br>
</div>

*QuickPuTTY* is a plugin for Sublime Text 3 that allows you to save SSH sessions for quick access to them.

Plugin will be useful to those who often use SSH.
Works with a free and open-source terminal emulator [PuTTY](https://putty.org "Visit putty.org").

![](./messages/usage.gif)

<h2>Installation</h2>

The plugin is available on [Package Control](https://packagecontrol.io/packages/QuickPuTTY "QuickPuTTY page on packagecontrol.io") and can be installed in this way:

1.  Press `Ctrl + Shift + P`, then enter `Package Control: Install Package` (or just `ins`)
2.  Choose `QuickPuTTY` in the list of available packages

After installation, you can change encryption keys in plugin settings (looking through all settings may be useful):

Go to `Preferences > Package Settings > QuickPuTTY > Settings` in the nav-bar.

![](./messages/installation.gif)

## Usage

#### Create session

1.  Go to `PuTTY > New session` in the nav-bar
2.  Enter server host/ip, port, username and password (last two are optional)

#### Edit sessions

1.  Go to `PuTTY > Manage sessions` in the nav-bar
2.  Edit session data (if you are editing password, do not forget to specify “encrypt”)
3.  Do not forget to save file

#### Remove session

1.  Go to `PuTTY > Remove session` in the nav-bar
2.  Choose a session that you want to remove

**Warning!** Usernames and passwords are stored using symmetric-key encryption (can be easily decoded). Make sure no one can access them.

-------------------------------------------

The plugin was tested on `Windows 10 (1809) x64` and `Ubuntu 18.04.03`.
If you have found a bug or mistake, you are very welcome to contact me on [n-panuhin.info](https://n-panuhin.info "Visit n-panuhin.info") or open a [new GitHub issue](https://github.com/Nikita-Panyuhin/QuickPuTTY/issues/new "Open QuickPuTTY GitHub Issues").

You can find the latest version of PuTTY on [putty.org](https://putty.org "Visit putty.org")

-------------------------------------------

Copyright &copy; 2020 Nikita Paniukhin

License: [MIT](http://n-panuhin.info/license.html "Visit n-panuhin.info/license")