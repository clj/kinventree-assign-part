import sys

import wx
from assign_dialog import AssignDialog


def main(filename):
    class InventreeAssignPartsApp(wx.App):
        def OnInit(self):
            frame = AssignDialog(filename=filename)
            frame.SetSize(700, 500)
            if frame.ShowModal() == wx.ID_OK:
                pass
            frame.Destroy()
            return True

    app = InventreeAssignPartsApp()
    app.MainLoop()

    print("Done")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit("Expected one argument (a .kicad_sch file)")
    main(sys.argv[1])
