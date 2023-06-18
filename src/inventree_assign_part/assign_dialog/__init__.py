from collections import UserDict
import copy
import wx
from kifield.sch import Schematic_V6
from natsort import natsorted
from .assign_parts import AssignParts
from .config import Config
import os
from inventree.api import InvenTreeAPI
from inventree.part import Part
from inventree.company import Company
from inventree.company import SupplierPart
from inventree.company import ManufacturerPart
import sexpdata


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
    def __init__(self, filename):
        super().__init__(None)

        self.filename = filename

        self.config = Config(os.path.dirname(filename))
        self.config.load_from_ini()

        self.api = InvenTreeAPI(
            self.config.inventree_server,
            username=self.config.inventree_username,
            password=self.config.inventree_password,
        )

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

        # self.schematic = Schematic_V6(filename)
        self.schematic = Schematic(filename)

        self._parts = {}
        self._parts_idx = {}
        self._components = {}

        rows = []
        for component in self.schematic.components:
            # print(component.uuid, component.properties)
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

    def onAutoAssignButton(self, event):
        inventree_parts = {}

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

    def onCloseButton(self, event):
        self.Close()

    def onSaveButton(self, event):
        self.schematic.save(self.filename)
