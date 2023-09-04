from collections import UserDict
import copy
from urllib.parse import urljoin

from inventree.api import InvenTreeAPI
from inventree.company import Company
from inventree.company import ManufacturerPart
from inventree.part import Part
from natsort import natsorted
import sexpdata
import wx

from .assign_parts import AssignParts


# Monkeypatch spexdata.Symbol to work with matching
sexpdata.Symbol.__match_args__ = ("__match_self_prop__",)


@property
def __match_self_prop__(self):
    return str(self)


sexpdata.Symbol.__match_self_prop__ = __match_self_prop__


class InvalidDataError(Exception):
    pass


class Property:
    def __init__(self, data):
        self.data = data
        self.parse(data)

    def parse(self, data):
        match data:
            case [sexpdata.Symbol("property"), str(name), str(value), *_]:
                self._name = name
                self._value = value
            case _:
                raise InvalidDataError("not a property")

    @property
    def name(self):
        return self._name

    @name.setter
    def name(self, value):
        self._name = value
        self.data[1] = value

    @property
    def value(self):
        return self._value

    @value.setter
    def value(self, value):
        self._value = value
        self.data[2] = value


class SExpDict(UserDict):
    def __init__(self, initial_data, sexp_data, insertion_pos):
        self.data = initial_data
        self.sexp_data = sexp_data
        self.insertion_pos = insertion_pos

    def __setitem__(self, key, value):
        insert_as_sexp = key not in self.data
        super().__setitem__(key, value)
        if insert_as_sexp:
            self.sexp_data.insert(self.insertion_pos, value.data)
            self.insertion_pos += 1


class Symbol:
    def __init__(self, data, *, project_uuid=None):
        self.data = data
        self.properties = {}
        self.project_uuid = project_uuid
        self.refs = {}
        self.parse(data)
        last_prop = self.properties[list(self.properties.keys())[-1]]
        last_prop_idx = self.data.index(last_prop.data) + 1
        self.properties = SExpDict(self.properties, self.data, last_prop_idx)

    def get_ref(self, *, project_uuid=None):
        return self.refs[str(project_uuid or self.project_uuid)]

    def parse(self, data):
        match data:
            case [
                sexpdata.Symbol("symbol"),
                [sexpdata.Symbol("lib_id"), str(lib_id)],
                *rest,
            ]:
                self.lib_id = lib_id
                for thing in rest:
                    match thing:
                        case [sexpdata.Symbol("uuid"), str(uuid)]:
                            self.uuid = uuid
                        case [sexpdata.Symbol("property"), str(name), *_]:
                            self.properties[name] = Property(thing)
                        case [sexpdata.Symbol("instances"), *projects]:
                            for project in projects:
                                match project:
                                    case [sexpdata.Symbol("project"), str(), *paths]:
                                        for path in paths:
                                            match path:
                                                case [
                                                    sexpdata.Symbol("path"),
                                                    str(path_str),
                                                    *props,
                                                ]:
                                                    for prop in props:
                                                        match prop:
                                                            case [
                                                                sexpdata.Symbol(
                                                                    "reference"
                                                                ),
                                                                str(ref),
                                                            ]:
                                                                self.refs[
                                                                    path_str[1:]
                                                                ] = ref
            case _:
                raise InvalidDataError("Not a symbol")


class Schematic:
    def __init__(self, file):
        if not hasattr("read", file):
            file = open(file, "r")

        self.data = sexpdata.load(file)
        self.components = []
        self.parse()

    def parse(self):
        for thing in self.data:
            match thing:
                case [sexpdata.Symbol("uuid"), str(uuid)]:
                    self.uuid = uuid
                case [
                    sexpdata.Symbol("symbol"),
                    [sexpdata.Symbol("lib_id"), str()],
                    *_,
                ]:
                    self.components.append(Symbol(thing, project_uuid=self.uuid))

    def save(self, file=None):
        if not hasattr("write", file):
            file = open(file, "w")
        sexpdata.dump(self.data, file, pretty_print=True)


class AssignDialog(AssignParts):
    def __init__(self, config, filename):
        super().__init__(None)

        self.config = config
        self.filename = filename

        try:
            self.api = InvenTreeAPI(
                self.config.inventree_server,
                username=self.config.inventree_username,
                password=self.config.inventree_password,
            )
        except ConnectionError:
            self.api = None
            return

        self.parts.ClearColumns()
        col = self.parts.AppendTextColumn("IPN")
        col.SetWidth(wx.COL_WIDTH_AUTOSIZE)
        col = self.parts.AppendTextColumn("References")
        col = col.SetWidth(wx.COL_WIDTH_AUTOSIZE)
        col = self.parts.AppendTextColumn("Supplier")
        col.SetWidth(wx.COL_WIDTH_AUTOSIZE)
        col = self.parts.AppendTextColumn("Supplier Part")
        col.SetWidth(wx.COL_WIDTH_AUTOSIZE)
        col = self.parts.AppendTextColumn("Manufacturer")
        col.SetWidth(wx.COL_WIDTH_AUTOSIZE)
        col = self.parts.AppendTextColumn("MPN")
        col.SetWidth(wx.COL_WIDTH_AUTOSIZE)

        self.schematic = Schematic(filename)

        self._parts = {}
        self._parts_idx = {}
        self._components = {}
        self._parts_rows = []
        self._parts_ipn = {}

        rows = []
        for component in self.schematic.components:
            if "IPN" not in component.properties:
                continue

            def get_properties_value(name):
                proprerty = component.properties.get(name)
                if not proprerty:
                    return None
                return proprerty.value

            ipn = component.properties["IPN"].value
            ref = component.get_ref()
            row = [
                ipn,
                ref,
                get_properties_value("Supplier"),
                get_properties_value("Supplier Part"),
                get_properties_value("Manufacturer"),
                get_properties_value("MPN"),
            ]
            rows += [row]
            self._parts[ref] = row
            self._components[ref] = component

        rows = natsorted(rows)

        for idx, row in enumerate(rows):
            self.parts.AppendItem(row)
            self._parts_idx.setdefault(row[1], []).append(idx)
            self._parts_rows.append(row)
            self._parts_ipn.setdefault(row[0], []).append(row)

    def assign_part(self, ref, supplier, spart, manufacturer, mpart):
        self._parts[ref] = self._parts[ref][:2] + [
            supplier["name"],
            spart.SKU,
            manufacturer.name,
            mpart.MPN,
        ]

        for idx in self._parts_idx[ref]:
            for col, value in enumerate(self._parts[ref][2:], start=2):
                self.parts.SetValue(value, idx, col)

        component = self._components[ref]

        def set_property(name, value):
            if not value:
                return
            if name not in component.properties:
                property = copy.deepcopy(component.properties["IPN"])
                property.name = name
                component.properties[name] = property
            component.properties[name].value = value

        set_property("Supplier", self._parts[ref][2])
        set_property("Supplier Part", self._parts[ref][3])
        set_property("Manufacturer", self._parts[ref][4])
        set_property("MPN", self._parts[ref][5])

    def onAutoAssignButton(self, event):
        inventree_parts = {}  # xxx: Fix caching

        for ref in self._parts:
            ipn = self._parts[ref][0]
            if not (part := inventree_parts.get(ipn)):
                part = Part.list(self.api, IPN=ipn)
                if not part:
                    continue
                sparts = part[0].getSupplierParts()
                if len(sparts) != 1:
                    continue

                spart = sparts[0]
                mpart = ManufacturerPart(self.api, spart.manufacturer_part)
                manufacturer = Company(self.api, mpart.manufacturer)

                supplier = spart.supplier_detail

            if not part:
                continue

            self.assign_part(ref, supplier, spart, manufacturer, mpart)

    def onCloseButton(self, event):
        self.Close()

    def onSaveButton(self, event):
        self.schematic.save(self.filename)

    def update_manufacturer_parts(self, ipn):
        self.assign_button.Enable(False)
        self.assign_all_button.Enable(False)

        self.supplier_parts_table.ClearColumns()
        col = self.supplier_parts_table.AppendTextColumn("Supplier")
        col.SetWidth(wx.COL_WIDTH_AUTOSIZE)
        col = self.supplier_parts_table.AppendTextColumn("Supplier Part")
        col.SetWidth(wx.COL_WIDTH_AUTOSIZE)
        col = self.supplier_parts_table.AppendTextColumn("Manufacturer")
        col.SetWidth(wx.COL_WIDTH_AUTOSIZE)
        col = self.supplier_parts_table.AppendTextColumn("MPN")
        col.SetWidth(wx.COL_WIDTH_AUTOSIZE)
        self.supplier_parts_table.DeleteAllItems()

        part = Part.list(self.api, IPN=ipn)
        if not part:
            return
        supplier_parts = part[0].getSupplierParts()

        self.supplier_parts = []
        for spart in supplier_parts:
            mpart = ManufacturerPart(self.api, spart.manufacturer_part)
            manufacturer = Company(self.api, mpart.manufacturer)

            self.supplier_parts.append([part[0], spart, mpart, manufacturer])
            supplier = spart.supplier_detail

            row = [
                supplier["name"],
                spart.SKU,
                manufacturer.name,
                mpart.MPN,
            ]
            self.supplier_parts_table.AppendItem(row)

    def parts_onDataViewListCtrolSelectionChanged(self, event):
        self.part_properties.Clear()
        row_idx = event.EventObject.SelectedRow
        row = self._parts_rows[row_idx]
        self.update_manufacturer_parts(row[0])

    def supplier_parts_table_onDataViewListCtrlSelectionChanged(self, event):
        row_idx = event.EventObject.SelectedRow
        row = self.supplier_parts[row_idx]
        ipn = row[0].IPN

        self.assign_button.Enable(True)
        if len(self._parts_ipn[ipn]) > 1:
            self.assign_all_button.Enable(True)

        def prop(label, name, value, /, can_edit=False, prop_type=wx.propgrid.StringProperty):
            p = prop_type(label, name, value or '')
            if not can_edit:
                p.ChangeFlag(wx.propgrid.PG_PROP_READONLY, True)
            return p

        self.part_properties.Clear()
        self.part_properties.Append(prop("Description", 'description', f"{row[2].description}"))
        self.part_properties.Append(prop("Active", 'active', f"{row[2].part_detail['active']}"))
        self.part_properties.Append(prop("Stock", 'stock', f"{int(row[1].in_stock)}"))
        self.part_properties.Append(prop("InvenTree", 'inventree', urljoin(self.api.base_url, f'/manufacturer-part/{row[1].pk}/')))
        if row[2].link:
            self.part_properties.Append(prop("Datasheet", 'datasheet', row[2].link))
        self.part_properties.Append(prop("Updated", 'updated', row[1].updated))
        self.part_properties.Grid.FitColumns()

    def assign_all_button_on_click(self, event):
        part_row_idx = self.parts.SelectedRow
        part_row = self._parts_rows[part_row_idx]

        supplier_row_idx = self.supplier_parts_table.SelectedRow
        supplier_row = self.supplier_parts[supplier_row_idx]

        rows = self._parts_ipn[part_row[0]]

        for row in rows:
            self.assign_part(
                row[1],
                supplier_row[1].supplier_detail,
                supplier_row[1],
                supplier_row[3],
                supplier_row[2],
            )

    def assign_button_on_click(self, event):
        part_row_idx = self.parts.SelectedRow
        part_row = self._parts_rows[part_row_idx]

        supplier_row_idx = self.supplier_parts_table.SelectedRow
        supplier_row = self.supplier_parts[supplier_row_idx]

        self.assign_part(
            part_row[1],
            supplier_row[1].supplier_detail,
            supplier_row[1],
            supplier_row[3],
            supplier_row[2],
        )
