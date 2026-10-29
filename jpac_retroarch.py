#!/usr/bin/env python3
"""Apply Ultimarc J-PAC default (MAME) keycodes to a RetroArch config.

Maps the keys a factory-default J-PAC sends to RetroArch players 1 and 2,
moves RetroArch hotkeys off any key the J-PAC sends, and optionally reports
or clears leftover conflicts. Standard library only; Python 3.6+.
"""

import argparse
import os
import re
import shutil
import sys

# Keys sent by a default J-PAC, per physical input.
# https://www.ultimarc.com/control-interfaces/j-pac-en/j-pac-jamma-interface/
JPAC = {
    1: {
        "up": "up", "down": "down", "left": "left", "right": "right",
        "start": "num1", "coin": "num5",
        "buttons": ["ctrl", "alt", "space", "shift", "z", "x", "c", "v"],
    },
    2: {
        "up": "r", "down": "f", "left": "d", "right": "g",
        "start": "num2", "coin": "num6",
        "buttons": ["a", "s", "q", "w", "i", "k", "j", "l"],
    },
}
JPAC_SYSTEM = {"service": "f1", "test": "f2", "tilt": "f3"}
# Sent while Start 1 is held: right, left, up, down, button 1, start 2.
JPAC_SHIFTED = ["tab", "enter", "tilde", "p", "num5", "escape"]

# RetroPad button for each J-PAC button 1..8.
LAYOUTS = {
    # Button N is "button N" in FBNeo / MAME 2003-Plus (classic mapping).
    "mame": ["b", "a", "y", "x", "l", "r", "l2", "r2"],
    # SNES pad shape on a 2x3 panel: top row Y X L, bottom row B A R.
    "snes": ["y", "x", "l", "b", "a", "r", "l2", "r2"],
}

# RetroArch hotkeys, set so that the J-PAC shift combos do something
# sensible and nothing else collides with a J-PAC key.
HOTKEYS = {
    "input_menu_toggle": "tab",             # Start1 + Right
    "input_pause_toggle": "p",              # Start1 + Down
    "input_exit_emulator": "escape",        # Start1 + Start2
    "input_netplay_player_chat": "nul",     # was tilde (Start1 + Up)
    "input_toggle_fast_forward": "pageup",  # default space (P1 B3)
    "input_hold_fast_forward": "pagedown",  # default l (P2 B8)
    "input_rewind": "backspace",            # default r (P2 up)
    "input_frame_advance": "end",           # default k (P2 B6)
    "input_toggle_fullscreen": "f12",       # default f (P2 down)
    "input_netplay_game_watch": "home",     # default i (P2 B5)
    "input_save_state": "f10",              # default f2 (Test)
    "input_fps_toggle": "insert",           # default f3 (Tilt)
}

BIND_RE = re.compile(r'^(\s*)([A-Za-z0-9_]+)(\s*=\s*)"([^"]*)"(\s*)$')


def build_settings(layout, service_test, quit_twice):
    settings = {}
    for player, keys in JPAC.items():
        prefix = "input_player%d_" % player
        for d in ("up", "down", "left", "right", "start"):
            settings[prefix + d] = keys[d]
        settings[prefix + "select"] = keys["coin"]
        for button, key in zip(LAYOUTS[layout], keys["buttons"]):
            settings[prefix + button] = key
    if service_test:
        settings["input_player1_l3"] = JPAC_SYSTEM["service"]
        settings["input_player1_r3"] = JPAC_SYSTEM["test"]
    settings.update(HOTKEYS)
    if quit_twice is not None:
        settings["quit_press_twice"] = "true" if quit_twice else "false"
    return settings


def split_eol(line):
    stripped = line.rstrip("\r\n")
    return stripped, line[len(stripped):]


def apply(lines, settings):
    """Return (new_lines, changes). Missing settings are appended."""
    out, changes, seen = [], [], set()
    for line in lines:
        body, eol = split_eol(line)
        m = BIND_RE.match(body)
        if m and m.group(2) in settings:
            name, old = m.group(2), m.group(4)
            new = settings[name]
            seen.add(name)
            if old != new:
                changes.append((name, old, new))
                body = '%s%s%s"%s"%s' % (m.group(1), name, m.group(3), new, m.group(5))
        out.append(body + eol)
    eol = split_eol(lines[0])[1] if lines else "\n"
    eol = eol or "\n"
    if out and not out[-1].endswith(("\n", "\r")):
        out[-1] += eol
    for name in sorted(set(settings) - seen):
        out.append('%s = "%s"%s' % (name, settings[name], eol))
        changes.append((name, None, settings[name]))
    return out, changes


def find_conflicts(lines, settings):
    """Keyboard binds not set by this script that use a key the J-PAC sends."""
    values = {}
    for line in lines:
        m = BIND_RE.match(split_eol(line)[0])
        if m:
            values[m.group(2)] = m.group(4)
    jpac_keys = set(JPAC_SHIFTED) | set(JPAC_SYSTEM.values())
    for keys in JPAC.values():
        jpac_keys.update([keys["up"], keys["down"], keys["left"], keys["right"],
                          keys["start"], keys["coin"]] + keys["buttons"])
    conflicts = []
    for name, value in values.items():
        # A keyboard bind always has a matching <name>_btn joypad entry;
        # this skips settings like input_driver = "x".
        if (name + "_btn") not in values or name in settings:
            continue
        # Light gun binds are left alone on purpose.
        if "_gun_" in name:
            continue
        if value in jpac_keys:
            conflicts.append((name, value))
    return sorted(conflicts)


def main(argv=None):
    p = argparse.ArgumentParser(
        description="Apply Ultimarc J-PAC default (MAME) keycodes to a RetroArch config.")
    p.add_argument("config", help="path to retroarch.cfg")
    p.add_argument("-l", "--layout", choices=sorted(LAYOUTS), default="mame",
                   help="how J-PAC buttons 1-8 map to RetroPad buttons (default: mame)")
    p.add_argument("-o", "--output",
                   help="write to this file instead of editing the config in place")
    p.add_argument("-n", "--dry-run", action="store_true",
                   help="show what would change without writing anything")
    p.add_argument("--no-backup", action="store_true",
                   help="do not create <config>.bak when editing in place")
    p.add_argument("--no-service-test", action="store_true",
                   help="do not bind Service/Test (F1/F2) to player 1 L3/R3")
    p.add_argument("--quit-press-twice", choices=["true", "false", "keep"], default="true",
                   help="require pressing Esc (Start1+Start2) twice to quit (default: true)")
    p.add_argument("--clear-conflicts", action="store_true",
                   help="set other binds that use a J-PAC key to nul instead of only warning")
    args = p.parse_args(argv)

    try:
        with open(args.config, encoding="utf-8", newline="") as f:
            lines = f.readlines()
    except OSError as e:
        p.error("cannot read %s: %s" % (args.config, e))

    quit_twice = {"true": True, "false": False, "keep": None}[args.quit_press_twice]
    settings = build_settings(args.layout, not args.no_service_test, quit_twice)

    conflicts = find_conflicts(lines, settings)
    if args.clear_conflicts:
        for name, _ in conflicts:
            settings[name] = "nul"

    new_lines, changes = apply(lines, settings)

    print("Layout: %s (J-PAC buttons 1-8 -> %s)" % (
        args.layout, ", ".join(b.upper() for b in LAYOUTS[args.layout])))
    if changes:
        for name, old, new in changes:
            print("  %-34s %s -> %s" % (name, "(missing)" if old is None else old, new))
    else:
        print("  already up to date")
    if conflicts:
        verb = "cleared" if args.clear_conflicts else "WARNING, still bound to a J-PAC key"
        print("Other binds using J-PAC keys (%s):" % verb)
        for name, value in conflicts:
            print("  %-34s %s" % (name, value))
        if not args.clear_conflicts:
            print("Re-run with --clear-conflicts to set these to nul.")

    if args.dry_run:
        print("Dry run: nothing written.")
        return 0

    target = args.output or args.config
    if not args.output and not args.no_backup and changes:
        backup = args.config + ".bak"
        shutil.copy2(args.config, backup)
        print("Backup: %s" % backup)
    tmp = target + ".tmp"
    with open(tmp, "w", encoding="utf-8", newline="") as f:
        f.writelines(new_lines)
    os.replace(tmp, target)
    print("Wrote: %s" % target)
    return 0


if __name__ == "__main__":
    sys.exit(main())
