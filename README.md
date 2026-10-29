# jpac_retroarch

Make a factory-default [Ultimarc J-PAC](https://www.ultimarc.com/control-interfaces/j-pac-en/j-pac-jamma-interface/) work in RetroArch without reprogramming it.

A J-PAC ships with MAME's default keycodes, so it works in MAME as soon as you plug it in. RetroArch's default keyboard layout is different, and several RetroArch hotkeys (fast-forward, rewind, fullscreen, save state…) use the same keys as the J-PAC. Pressing a fire button can toggle fast-forward, and moving player 2's joystick can rewind.

`jpac_retroarch.py` edits your `retroarch.cfg` so that:

- the J-PAC controls players 1 and 2,
- every RetroArch hotkey that collides with a J-PAC key moves to a key the J-PAC never sends,
- the J-PAC's "shift" combos (hold Start 1) open the menu, pause and quit,
- Service and Test reach arcade cores through player 1's L3 and R3,
- Esc has to be pressed twice to quit.

You don't need to change anything in MAME or on the J-PAC.

## Requirements

- Python 3.6 or newer. Only the standard library is used; there is nothing to `pip install`.
- RetroArch has to be **closed** while you run the script. RetroArch saves its config when it exits (`config_save_on_exit`), so a running copy would overwrite your changes.

## Usage

```sh
python3 jpac_retroarch.py ~/.config/retroarch/retroarch.cfg
```

The script edits the file in place and saves the original as `retroarch.cfg.bak`. It then prints every setting it changed.

| Option | Effect |
|---|---|
| `-l mame` / `-l snes` | Button layout (see below). Default: `mame`. |
| `-n`, `--dry-run` | Show what would change without writing anything. |
| `-o FILE` | Write the result to `FILE` and leave the input untouched. |
| `--no-backup` | Don't create `retroarch.cfg.bak`. |
| `--no-service-test` | Don't bind Service/Test (F1/F2) to player 1 L3/R3. |
| `--quit-press-twice true\|false\|keep` | Whether quitting with Esc needs two presses. Default: `true`. |
| `--clear-conflicts` | Set any *other* bind that uses a J-PAC key to `nul`. Without it, the script only lists them. |

You can run the script again at any time, for example to switch layouts. It only changes what it needs to.

### Where is retroarch.cfg?

| Install | Path |
|---|---|
| Linux (distro package) | `~/.config/retroarch/retroarch.cfg` |
| Linux (Flatpak) | `~/.var/app/org.libretro.RetroArch/config/retroarch/retroarch.cfg` |
| Linux (Steam) | `~/.local/share/Steam/steamapps/common/RetroArch/retroarch.cfg` |
| Windows (installer) | `%APPDATA%\RetroArch\retroarch.cfg`, or `retroarch.cfg` in the RetroArch folder |
| Windows (Steam) | `C:\Program Files (x86)\Steam\steamapps\common\RetroArch\retroarch.cfg` |

If you aren't sure, open RetroArch and check **Settings → Configuration**, or look at which file RetroArch prints on startup.

### Windows

1. Install Python 3 from [python.org](https://www.python.org/downloads/windows/), or run `winget install Python.Python.3.12`. The python.org installer also installs the `py` launcher.
2. Close RetroArch.
3. Open PowerShell or Command Prompt in the folder that holds `jpac_retroarch.py` and run:

   ```powershell
   py jpac_retroarch.py "$env:APPDATA\RetroArch\retroarch.cfg"
   ```

   In Command Prompt, use `"%APPDATA%\RetroArch\retroarch.cfg"` instead. If `py` isn't found, try `python`.

Windows line endings (CRLF) in the config are preserved.

## Button layouts

A J-PAC has 8 buttons per player. Most control panels arrange them like this:

```
 [1] [2] [3] [7]
 [4] [5] [6] [8]
```

RetroArch sees a "RetroPad" (an SNES-style pad plus L2/R2). The `--layout` option decides which RetroPad button each J-PAC button becomes.

| J-PAC button | P1 key | P2 key | `mame` (default) | `snes` |
|---|---|---|---|---|
| 1 | Left Ctrl | A | B | Y |
| 2 | Left Alt | S | A | X |
| 3 | Space | Q | Y | L |
| 4 | Left Shift | W | X | B |
| 5 | Z | I | L | A |
| 6 | X | K | R | R |
| 7 | C | J | L2 | L2 |
| 8 | V | L | R2 | R2 |

- **`mame`**: arcade cores (FBNeo, MAME 2003-Plus) map RetroPad B, A, Y, X, L, R to their buttons 1 to 6 in their default "classic" mapping. So J-PAC button 1 is button 1, just as in standalone MAME. Choose this if you mostly play arcade games.
- **`snes`**: the top row is Y X L and the bottom row is B A R, the same shape as an SNES pad. Choose this if you mostly play console games. Arcade cores will then see J-PAC button 1 as their button 3, unless you remap inside the core.

Both layouts set the rest the same way:

| Input | Player 1 | Player 2 | RetroPad |
|---|---|---|---|
| Joystick | arrow keys | R / F / D / G (up / down / left / right) | D-pad |
| Start | 1 | 2 | Start |
| Coin | 5 | 6 | Select |

Players 3 to 16 are not changed.

## J-PAC shift functions (hold Start 1)

| Combo | Key sent | RetroArch action |
|---|---|---|
| Start 1 + Right | Tab | Open / close the menu |
| Start 1 + Down | P | Pause |
| Start 1 + Start 2 | Esc | Quit (press twice) |
| Start 1 + Button 1 | 5 | Insert coin (player 1) |
| Start 1 + Up | ~ | Nothing. This was netplay chat, which the script turns off. |
| Start 1 + Left | Enter | Nothing |

## Service, Test and Tilt

| J-PAC input | Key | RetroArch |
|---|---|---|
| Service | F1 | Player 1 L3 |
| Test | F2 | Player 1 R3 |
| Tilt | F3 | Unbound |

Real arcade games use **Test** to open the operator menu (DIP switches, sound test, high-score reset) and **Service** to add a credit without counting a coin. RetroPad has no buttons for these, so the script sends them through L3 and R3, which the J-PAC doesn't otherwise use.

You need to do one thing per arcade core: start a game, open **Quick Menu → Controls → Port 1**, and check which game function L3 and R3 control. If they aren't Service and Test, change them, then choose **Save Core Remap File** so the change applies to every game on that core.

Tilt is left unbound because it is often a physical tilt switch. Binding it to anything disruptive would let a bump of the cabinet trigger that action.

## Relocated RetroArch hotkeys

These RetroArch default hotkeys use keys the J-PAC sends, so the script moves them:

| Hotkey | RetroArch default | Collides with | New key |
|---|---|---|---|
| Fast-forward (toggle) | Space | P1 button 3 | Page Up |
| Fast-forward (hold) | L | P2 button 8 | Page Down |
| Rewind | R | P2 up | Backspace |
| Frame advance | K | P2 button 6 | End |
| Fullscreen | F | P2 down | F12 |
| Netplay spectate | I | P2 button 5 | Home |
| Save state | F2 | Test | F10 |
| FPS display | F3 | Tilt | Insert |
| Netplay chat | ~ | Start 1 + Up | unbound |

You can still use them from a regular keyboard. Everything else, such as load state (F4), state slots (F6/F7), screenshot (F8) and mute (F9), keeps its key.

The script also checks for **any other bind** in your config that uses a J-PAC key, for example something you bound yourself. It lists those, and `--clear-conflicts` sets them to `nul`. Light gun binds are left alone.

## Notes

- RetroArch reads only one keyboard key per action, so a hotkey can't be on both its old key and a new one.
- The script changes only the keyboard settings listed above (`input_player1_a = "..."` and so on). It leaves joypad (`_btn`), axis and mouse binds alone, so a gamepad configured alongside the J-PAC keeps working.
- If a setting is missing from your config, the script adds it. Otherwise RetroArch would fall back to its built-in default, which may be a J-PAC key.
- To undo the changes, copy `retroarch.cfg.bak` back over `retroarch.cfg`.
