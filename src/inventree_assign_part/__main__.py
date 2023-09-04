import os
from pathlib import Path
import sys

import wx
from assign_dialog import AssignDialog

from assign_dialog.config import Config


def main(filename):
    class InventreeAssignPartsApp(wx.App):
        def OnInit(self):
            nonlocal filename

            if not filename:
                with wx.FileDialog(
                    None,
                    "Open KiCad Schematic file",
                    wildcard="KiCad Schematic files (*.kicad_sch)|*.kicad_sch",
                    style=wx.FD_OPEN | wx.FD_FILE_MUST_EXIST,
                ) as fileDialog:
                    if fileDialog.ShowModal() == wx.ID_CANCEL:
                        return True
                    filename = fileDialog.GetPath()

            lockfile = Path(filename)
            lockfile = lockfile.with_name(f"~{lockfile.name}.lck")

            if lockfile.exists():
                wx.LogError(
                    """The schematic is already open in KiCad,
                    please close the schematic editor before continuing"""
                )
                return True

            config = Config(os.path.dirname(filename))
            config.load_from_ini()

            if not all(
                (
                    config.inventree_server,
                    config.inventree_username,
                    config.inventree_password,
                )
            ):
                wx.LogError(
                    """No configuration present or configuration incomplete.
                    Please specify: server, username, and password in inventree.config.ini
                    next to the schematic file."""
                )
                return True

            # XXX: Create lockfile?
            frame = AssignDialog(config=config, filename=filename)
            if frame.api is None:
                wx.LogError(
                    """Could not connect to InvenTree, please check the settings in
                    inventree.config.ini, and your network is working properly."""
                )
                frame.Destroy()
                return True
            frame.SetSize(700, 500)
            if frame.ShowModal() == wx.ID_OK:
                pass
            frame.Destroy()
            return True

    app = InventreeAssignPartsApp()
    app.MainLoop()


if __name__ == "__main__":
    if len(sys.argv) > 2:
        sys.exit("Expected one argument (a .kicad_sch file)")
    elif len(sys.argv) < 2:
        filename = None
    else:
        filename = sys.argv[1]
    main(filename)
