# -*- coding: utf-8 -*-

###########################################################################
## Python code generated with wxFormBuilder (version 3.10.1-0-g8feb16b)
## http://www.wxformbuilder.org/
##
## PLEASE DO *NOT* EDIT THIS FILE!
###########################################################################

import wx
import wx.xrc
import wx.dataview
import wx.propgrid as pg

###########################################################################
## Class AssignParts
###########################################################################

class AssignParts ( wx.Dialog ):

    def __init__( self, parent ):
        wx.Dialog.__init__ ( self, parent, id = wx.ID_ANY, title = wx.EmptyString, pos = wx.DefaultPosition, size = wx.Size( 626,577 ), style = wx.DEFAULT_DIALOG_STYLE|wx.RESIZE_BORDER )

        self.SetSizeHints( wx.DefaultSize, wx.DefaultSize )

        bSizer4 = wx.BoxSizer( wx.VERTICAL )

        self.m_splitter1 = wx.SplitterWindow( self, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.SP_3D )
        self.m_splitter1.Bind( wx.EVT_IDLE, self.m_splitter1OnIdle )

        self.m_panel2 = wx.Panel( self.m_splitter1, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.TAB_TRAVERSAL )
        sbSizer1 = wx.StaticBoxSizer( wx.StaticBox( self.m_panel2, wx.ID_ANY, u"Parts" ), wx.VERTICAL )

        self.parts = wx.dataview.DataViewListCtrl( sbSizer1.GetStaticBox(), wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, 0 )
        sbSizer1.Add( self.parts, 1, wx.ALL|wx.EXPAND, 5 )


        self.m_panel2.SetSizer( sbSizer1 )
        self.m_panel2.Layout()
        sbSizer1.Fit( self.m_panel2 )
        self.m_panel3 = wx.Panel( self.m_splitter1, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.TAB_TRAVERSAL )
        sbSizer3 = wx.StaticBoxSizer( wx.StaticBox( self.m_panel3, wx.ID_ANY, u"Manufacturer Parts" ), wx.VERTICAL )

        self.supplier_parts_table = wx.dataview.DataViewListCtrl( sbSizer3.GetStaticBox(), wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, 0 )
        sbSizer3.Add( self.supplier_parts_table, 2, wx.ALL|wx.EXPAND, 5 )


        self.m_panel3.SetSizer( sbSizer3 )
        self.m_panel3.Layout()
        sbSizer3.Fit( self.m_panel3 )
        self.m_splitter1.SplitHorizontally( self.m_panel2, self.m_panel3, 0 )
        bSizer4.Add( self.m_splitter1, 2, wx.EXPAND, 5 )

        self.m_panel31 = wx.Panel( self, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.TAB_TRAVERSAL )
        sbSizer31 = wx.StaticBoxSizer( wx.StaticBox( self.m_panel31, wx.ID_ANY, u"Manufacturer Part Details" ), wx.VERTICAL )

        self.part_properties = pg.PropertyGrid(sbSizer31.GetStaticBox(), wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.propgrid.PG_DEFAULT_STYLE)
        sbSizer31.Add( self.part_properties, 1, wx.ALL|wx.EXPAND, 5 )


        self.m_panel31.SetSizer( sbSizer31 )
        self.m_panel31.Layout()
        sbSizer31.Fit( self.m_panel31 )
        bSizer4.Add( self.m_panel31, 1, wx.ALL|wx.EXPAND, 5 )

        bSizer5 = wx.BoxSizer( wx.HORIZONTAL )

        self.assign_button = wx.Button( self, wx.ID_ANY, u"Assign", wx.DefaultPosition, wx.DefaultSize, 0 )
        self.assign_button.Enable( False )

        bSizer5.Add( self.assign_button, 0, wx.ALL, 5 )

        self.assign_all_button = wx.Button( self, wx.ID_ANY, u"Assign All", wx.DefaultPosition, wx.DefaultSize, 0 )
        self.assign_all_button.Enable( False )

        bSizer5.Add( self.assign_all_button, 0, wx.ALL, 5 )

        self.m_button12 = wx.Button( self, wx.ID_ANY, u"Auto Assign", wx.DefaultPosition, wx.DefaultSize, 0 )
        bSizer5.Add( self.m_button12, 0, wx.ALL, 5 )


        bSizer5.Add( ( 0, 0), 1, wx.EXPAND, 5 )

        self.m_button10 = wx.Button( self, wx.ID_ANY, u"Save", wx.DefaultPosition, wx.DefaultSize, 0 )
        bSizer5.Add( self.m_button10, 0, wx.ALL, 5 )

        self.m_button11 = wx.Button( self, wx.ID_ANY, u"Close", wx.DefaultPosition, wx.DefaultSize, 0 )
        bSizer5.Add( self.m_button11, 0, wx.ALL, 5 )


        bSizer4.Add( bSizer5, 0, wx.EXPAND, 5 )


        self.SetSizer( bSizer4 )
        self.Layout()

        self.Centre( wx.BOTH )

        # Connect Events
        self.parts.Bind( wx.dataview.EVT_DATAVIEW_SELECTION_CHANGED, self.parts_onDataViewListCtrolSelectionChanged, id = wx.ID_ANY )
        self.supplier_parts_table.Bind( wx.dataview.EVT_DATAVIEW_SELECTION_CHANGED, self.supplier_parts_table_onDataViewListCtrlSelectionChanged, id = wx.ID_ANY )
        self.assign_button.Bind( wx.EVT_BUTTON, self.assign_button_on_click )
        self.assign_all_button.Bind( wx.EVT_BUTTON, self.assign_all_button_on_click )
        self.m_button12.Bind( wx.EVT_BUTTON, self.onAutoAssignButton )
        self.m_button10.Bind( wx.EVT_BUTTON, self.onSaveButton )
        self.m_button11.Bind( wx.EVT_BUTTON, self.onCloseButton )

    def __del__( self ):
        pass


    # Virtual event handlers, override them in your derived class
    def parts_onDataViewListCtrolSelectionChanged( self, event ):
        event.Skip()

    def supplier_parts_table_onDataViewListCtrlSelectionChanged( self, event ):
        event.Skip()

    def assign_button_on_click( self, event ):
        event.Skip()

    def assign_all_button_on_click( self, event ):
        event.Skip()

    def onAutoAssignButton( self, event ):
        event.Skip()

    def onSaveButton( self, event ):
        event.Skip()

    def onCloseButton( self, event ):
        event.Skip()

    def m_splitter1OnIdle( self, event ):
        self.m_splitter1.SetSashPosition( 0 )
        self.m_splitter1.Unbind( wx.EVT_IDLE )


