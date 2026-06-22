"""UI automation driver for the Infineon STDF Analyzer.

The STDF Analyzer (eSquare ``_STDFAnalyser.exe``) is a GUI-only .NET application with no
command-line conversion interface, so conversion is driven through Windows UI Automation
via :mod:`pywinauto`.

High-level flow for one conversion:

1. Snapshot the ``.eff`` files already present in the watched folders.
2. Start or attach to the analyzer.
3. ``File -> Open`` the ST4 file.
4. ``Convert -> To EFF``.
5. If a Save/Save As dialog appears, type the destination path; otherwise detect the
   newly produced ``.eff`` by diffing the folder snapshot.
6. Move/rename the produced ``.eff`` to ``wafernum<N>_<base>.eff`` next to the ST4 file.

All window titles, menu paths, and timeouts are configurable in :mod:`config` so the
automation can be re-calibrated for a different analyzer build without code changes.
"""
from __future__ import annotations

import logging
import shutil
import time
from pathlib import Path

from . import config

log = logging.getLogger(__name__)

# Only ever attach to the real WinForms application window, never a look-alike
# (e.g. a terminal tab whose title happens to contain "STDF Analy...").
_WINFORMS_CLASS_RE = r"WindowsForms.*"

# Title of the child dialog opened by ``Convert -> To EFF``.
_CONVERT_DIALOG_TITLE = "Convert To EFF"


class AnalyzerError(RuntimeError):
    """Raised when the STDF Analyser cannot be driven to produce an EFF file."""


def _import_pywinauto():
    try:
        from pywinauto import Application, timings  # noqa: WPS433
        from pywinauto import findwindows  # noqa: WPS433
    except ImportError as exc:  # pragma: no cover
        raise AnalyzerError(
            "pywinauto is not installed. Run: pip install pywinauto"
        ) from exc
    return Application, timings, findwindows


def _watch_dirs(st4_folder: Path) -> list[Path]:
    dirs = [st4_folder]
    if config.EFF_WATCH_DIR is not None and config.EFF_WATCH_DIR != st4_folder:
        dirs.append(config.EFF_WATCH_DIR)
    return dirs


def _snapshot_eff(dirs: list[Path]) -> set[Path]:
    found: set[Path] = set()
    for directory in dirs:
        if directory.is_dir():
            found.update(directory.glob("*.eff"))
    return found


def _parse_menu_path(menu_path: str) -> tuple[str, str]:
    parts = [p.strip() for p in menu_path.split("->") if p.strip()]
    if len(parts) != 2:
        raise AnalyzerError(f"Menu path must be 'Top->Leaf', got {menu_path!r}.")
    return parts[0], parts[1]


def _find_app_window(findwindows):
    """Return the UIA element of the real analyser window, or ``None`` if not running."""
    try:
        elems = findwindows.find_elements(
            title_re=config.WINDOW_TITLE_RE,
            class_name_re=_WINFORMS_CLASS_RE,
            backend=config.UI_BACKEND,
        )
    except Exception as exc:  # noqa: BLE001
        log.debug("find_elements failed: %s", exc)
        return None
    return elems[0] if elems else None


def _connect_or_start(Application, timings, findwindows):
    """Return ``(app, main_window)`` for a running analyser, starting it if needed."""
    elem = _find_app_window(findwindows)
    if elem is not None:
        app = Application(backend=config.UI_BACKEND).connect(process=elem.process_id)
        log.info("Attached to running STDF Analyser (pid %s).", elem.process_id)
        return app, _main_window(app)

    if not config.ANALYZER_PATH.is_file():
        raise AnalyzerError(f"STDF Analyser executable not found: {config.ANALYZER_PATH}")

    log.info("Starting STDF Analyser: %s", config.ANALYZER_PATH)
    app = Application(backend=config.UI_BACKEND).start(
        f'"{config.ANALYZER_PATH}"',
        work_dir=str(config.ANALYZER_PATH.parent),
        wait_for_idle=False,  # .NET app: WaitForInputIdle is unsupported.
    )

    deadline = time.monotonic() + config.APP_START_TIMEOUT
    while time.monotonic() < deadline:
        if _find_app_window(findwindows) is not None:
            break
        time.sleep(0.5)
    else:
        raise AnalyzerError(
            f"STDF Analyser window did not appear within {config.APP_START_TIMEOUT:.0f}s."
        )
    return app, _main_window(app)


def _main_window(app):
    win = app.window(title_re=config.WINDOW_TITLE_RE, class_name_re=_WINFORMS_CLASS_RE)
    win.wait("exists ready", timeout=config.DIALOG_TIMEOUT)
    return win


def _menu_bar(win):
    """Return the WinForms main menu bar wrapper.

    The window exposes more than one ``MenuBar`` (e.g. the system menu strip), so the
    named ``menuStrip1`` bar is preferred, falling back to the first menu bar that
    actually contains the configured top-level menu.
    """
    bar = win.child_window(title="menuStrip1", control_type="MenuBar")
    if bar.exists(timeout=2):
        return bar

    top_text, _ = _parse_menu_path(config.MENU_OPEN)
    bars = win.children(control_type="MenuBar")
    for candidate in bars:
        try:
            if candidate.child_window(title=top_text, control_type="MenuItem").exists(timeout=1):
                return candidate
        except Exception:  # noqa: BLE001
            continue
    if bars:
        return bars[0]
    raise AnalyzerError("Could not locate the analyser menu bar.")


def _menu_click(win, menu_path: str) -> None:
    """Open ``Top`` menu and click ``Leaf`` using non-blocking mouse interaction.

    ``invoke()`` is deliberately avoided: on this app it blocks (the modal dialog never
    lets the Invoke call return) and can crash the process.
    """
    top_text, leaf_text = _parse_menu_path(menu_path)
    win.set_focus()
    bar = _menu_bar(win)

    top = bar.child_window(title=top_text, control_type="MenuItem")
    top.wait("exists ready", timeout=config.DIALOG_TIMEOUT)
    try:
        top.expand()
    except Exception:  # noqa: BLE001 - ExpandCollapse may be unsupported; click instead
        top.click_input()
    time.sleep(0.4)

    leaf = top.child_window(title=leaf_text, control_type="MenuItem")
    leaf.wait("exists ready", timeout=config.DIALOG_TIMEOUT)
    leaf.click_input()
    time.sleep(0.4)


def _set_dialog_filename(dlg, value: str) -> None:
    """Type ``value`` into a file dialog's file-name field, trying several locators."""
    locators = (
        dict(auto_id="1148", control_type="Edit"),
        dict(title="File name:", control_type="Edit"),
        dict(title="File name:", control_type="ComboBox"),
        dict(class_name="Edit"),
    )
    for kw in locators:
        try:
            ctrl = dlg.child_window(**kw)
            if not ctrl.exists(timeout=1):
                continue
            ctrl.set_focus()
            try:
                ctrl.set_edit_text(value)
            except Exception:  # noqa: BLE001 - combobox/edit without ValuePattern
                ctrl.type_keys("^a{BACKSPACE}", set_foreground=True)
                ctrl.type_keys(value, with_spaces=True, set_foreground=True)
            return
        except Exception:  # noqa: BLE001
            continue
    dlg.type_keys(value, with_spaces=True, set_foreground=True)


def _wait_child_dialog(win, title_re: str, timeout: float):
    """Return the ``#32770`` common dialog that appears as a child of the main window.

    The analyser parents its Open/Save common dialogs to the main window, so they are
    located via ``child_window`` rather than as separate top-level windows.
    """
    dlg = win.child_window(title_re=title_re, class_name="#32770", control_type="Window")
    dlg.wait("exists ready", timeout=timeout)
    return dlg


def _submit_dialog(dlg) -> None:
    """Accept a file dialog via its default action (Enter).

    The Open button is a split button that matches ambiguously, so Enter is used to
    invoke the dialog's default command.
    """
    try:
        dlg.set_focus()
    except Exception:  # noqa: BLE001
        pass
    dlg.type_keys("{ENTER}", set_foreground=True)


def _open_st4(app, win, st4_file_path: Path) -> None:
    _menu_click(win, config.MENU_OPEN)
    dlg = _wait_child_dialog(win, title_re="Open.*", timeout=config.DIALOG_TIMEOUT)

    _set_dialog_filename(dlg, str(st4_file_path))
    time.sleep(0.3)
    _submit_dialog(dlg)

    # Wait for the Open dialog to close (dataset loading may take a while).
    deadline = time.monotonic() + config.DIALOG_TIMEOUT
    while time.monotonic() < deadline:
        try:
            if not dlg.exists(timeout=1):
                break
        except Exception:  # noqa: BLE001
            break
        time.sleep(0.5)
    time.sleep(1.5)


def _convert_to_eff(app, win, eff_target: Path) -> None:
    """Drive ``Convert -> To EFF``: set the output name and press Start.

    ``Convert -> To EFF`` opens a child *Convert To EFF* dialog whose ``tbFileName`` edit
    holds the output path. Setting it to ``eff_target`` makes the analyser write the EFF
    directly with the wafer-prefixed name into the ST4 folder; the ``Start`` button
    (auto-id ``btSave``) runs the conversion.
    """
    _menu_click(win, config.MENU_CONVERT_EFF)

    dlg = win.child_window(title=_CONVERT_DIALOG_TITLE, control_type="Window")
    dlg.wait("exists ready", timeout=config.DIALOG_TIMEOUT)

    # Set the output file name/path (wafer-prefixed) before starting the conversion.
    try:
        fn = dlg.child_window(auto_id="tbFileName", control_type="Edit")
        if fn.exists(timeout=config.DIALOG_TIMEOUT):
            fn.set_focus()
            try:
                fn.set_edit_text(str(eff_target))
            except Exception:  # noqa: BLE001 - no ValuePattern; type instead
                fn.type_keys("^a{BACKSPACE}", set_foreground=True)
                fn.type_keys(str(eff_target), with_spaces=True, set_foreground=True)
            time.sleep(0.3)
    except Exception as exc:  # noqa: BLE001 - fall back to the analyser default name
        log.warning("Could not set EFF output name (%s); using analyser default.", exc)

    start = dlg.child_window(auto_id="btSave", control_type="Button")
    start.wait("exists ready", timeout=config.DIALOG_TIMEOUT)
    start.click_input()

    # Confirm any "overwrite?" prompt that may appear after Start.
    try:
        confirm = win.child_window(class_name="#32770", control_type="Window")
        if confirm.exists(timeout=2):
            _click_dialog_button(confirm, ("Yes", "&Yes", "OK"))
    except Exception:  # noqa: BLE001
        pass


def _dismiss_convert_dialog(win) -> None:
    """Best-effort close of the *Convert To EFF* dialog after a conversion."""
    try:
        dlg = win.child_window(title=_CONVERT_DIALOG_TITLE, control_type="Window")
        if not dlg.exists(timeout=1):
            return
        try:
            btn = dlg.child_window(title="Close", control_type="Button", found_index=0)
            if btn.exists(timeout=1):
                btn.click_input()
                return
        except Exception:  # noqa: BLE001
            pass
        dlg.close()
    except Exception:  # noqa: BLE001
        pass


def _click_dialog_button(dlg, titles: tuple[str, ...]) -> bool:
    for title in titles:
        try:
            btn = dlg.child_window(title=title, control_type="Button")
            if btn.exists(timeout=1):
                btn.click_input()
                return True
        except Exception:  # noqa: BLE001
            continue
    try:
        dlg.type_keys("{ENTER}", set_foreground=True)
        return True
    except Exception:  # noqa: BLE001
        return False


def _wait_for_new_eff(before: set[Path], dirs: list[Path], timeout: float) -> Path:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        new = _snapshot_eff(dirs) - before
        # Ignore partially written files by requiring a stable size.
        ready = [p for p in new if _is_stable(p)]
        if ready:
            return max(ready, key=lambda p: p.stat().st_mtime)
        time.sleep(1.0)
    raise AnalyzerError(
        "Conversion did not produce a new .eff file within "
        f"{timeout:.0f}s (watched: {', '.join(str(d) for d in dirs)})."
    )


def _is_stable(path: Path) -> bool:
    try:
        first = path.stat().st_size
        time.sleep(0.5)
        return path.is_file() and path.stat().st_size == first and first > 0
    except OSError:
        return False


def _finalize(produced: Path, eff_target: Path) -> Path:
    if produced.resolve() == eff_target.resolve():
        return eff_target
    if eff_target.exists():
        # eff_output_path already timestamps on collision; guard anyway.
        raise AnalyzerError(f"Destination already exists: {eff_target}")
    shutil.move(str(produced), str(eff_target))
    return eff_target


def convert(st4_file_path: Path, eff_target: Path) -> Path:
    """Convert one ST4 file to EFF and place it at ``eff_target``.

    Returns the path of the written ``.eff`` file. Raises :class:`AnalyzerError` on failure.
    """
    if not st4_file_path.is_file():
        raise AnalyzerError(f"ST4 file not found: {st4_file_path}")

    Application, timings, findwindows = _import_pywinauto()
    dirs = _watch_dirs(st4_file_path.parent)
    before = _snapshot_eff(dirs)

    app, win = _connect_or_start(Application, timings, findwindows)

    try:
        _open_st4(app, win, st4_file_path)
        _convert_to_eff(app, win, eff_target)
        produced = _wait_for_new_eff(before, dirs, config.CONVERT_TIMEOUT)
        result = _finalize(produced, eff_target)
        _dismiss_convert_dialog(win)
        log.info("Converted %s -> %s", st4_file_path.name, result.name)
        return result
    finally:
        if not config.KEEP_APP_OPEN:
            try:
                app.kill()
            except Exception:  # noqa: BLE001
                pass
