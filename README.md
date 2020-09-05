<h1 align="center">QuickPuTTY</h1>

<div class="badges" align="center">
	<a href="https://packagecontrol.io/packages/QuickPuTTY"><img src="https://img.shields.io/badge/WIN-LINUX-f08989?labelColor=99c1f0&style=flat-square&cacheSeconds=260000" alt="WIN|LINUX"></a>
	<a href="https://packagecontrol.io/packages/QuickPuTTY" target="_blank" title="Package Control: QuickPuTTY"><img src="https://img.shields.io/packagecontrol/dt/QuickPuTTY?color=success&style=flat-square&cacheSeconds=1000"></a>
	<a href="http://npanuhin.me/license.html" target="_blank" title="license: MIT"><img alt="license: MIT" src="https://img.shields.io/badge/license-MIT-blue.svg?color=informational&style=flat-square&cacheSeconds=260000"></a>
	<br>
</div>

*QuickPuTTY* is a plugin for Sublime Text 3 that allows you to save SSH sessions for quick access to them.

Plugin will be useful to those who often use SSH.
Works with a free and open-source terminal emulator [PuTTY](https://putty.org "Visit putty.org").

**New!** Folders supported.

See how fast you can start an SSH session **without entering username and password**:

![](./messages/usage.gif)

<h2>Installation</h2>

The plugin is available on [Package Control](https://packagecontrol.io/packages/QuickPuTTY "Visit QuickPuTTY page on packagecontrol.io") and can be installed in this way:

1.  Press <kbd>Ctrl + Shift + P</kbd>, then enter `Package Control: Install Package` (or just `ins`)
2.  Choose `QuickPuTTY` in the list of available packages

After installation, you can change encryption keys in plugin settings (looking through all settings may be useful):

Go to `Preferences > Package Settings > QuickPuTTY > Settings` in the nav-bar.

![](./messages/installation.gif)

## Usage

**Warning!** Usernames and passwords are stored using symmetric-key encryption (can be easily decoded). Make sure no one can access them.

#### Create folder

1.  Go to `PuTTY > New session/folder` in the nav-bar and select `folder` option
2.  [Choose location](#choosing-location) to place new folder
3.  Enter folder name

#### Create session

1.  Go to `PuTTY > New session/folder` in the nav-bar and select `session` option
2.  [Choose location](#choosing-location) to place new session
3.  Enter server host/ip, port, username and password (last two are optional)

#### Edit sessions and folders

1.  Go to `PuTTY > Manage sessions` in the nav-bar
2.  Edit data (if you are editing password, do not forget to specify “encrypt”)
3.  Do not forget to save file

#### Remove session/folder

1.  Go to `PuTTY > Remove session/folder` in the nav-bar
2.  Select session or folder you want to remove

#### Choosing location

At each stage, you'll see a list of options:

|           item          |                            meaning                                  |
|:-----------------------:|:-------------------------------------------------------------------:|
| ### Choose location ### |                          Just a title                               |
|         \<HERE\>        | Choose this if you want to place session/folder in current location |
|        {folder_1}       |            Select a folder name to navigate into it                 |
|          . . .          |                             . . .                                   |


-------------------------------------------

The plugin was tested on `Windows 10 (1809) x64` and `Ubuntu 18.04.03`.
If you have found a bug or mistake, you are very welcome to contact me on [npanuhin.me](https://npanuhin.me "Visit npanuhin.me") or open a [new GitHub issue](https://github.com/Nikita-Panyuhin/QuickPuTTY/issues/new "Open QuickPuTTY GitHub Issues").

You can find the latest version of PuTTY on [putty.org](https://putty.org "Visit putty.org")

-------------------------------------------

Copyright &copy; 2020 Nikita Paniukhin

License: [MIT](http://npanuhin.me/license.html "Visit npanuhin.me/license")