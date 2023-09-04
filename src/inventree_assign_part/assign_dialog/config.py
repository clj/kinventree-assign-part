import os.path

from wx import FileConfig


class Config:
    inventree_server = ""
    inventree_username = ""
    inventree_password = ""
    inventree_apikey = ""

    def __init__(self, local_dir):
        # This is how ibom determines config locations
        self.local_assign_part_config_file = os.path.join(
            local_dir, "inventree-assign-part.config.ini"
        )
        self.local_inventree_config_file = os.path.join(
            local_dir, "inventree.config.ini"
        )
        self.global_config_file = os.path.join(
            os.path.dirname(__file__), "..", "config.ini"
        )

    def load_from_ini(self):
        """Init from config file if it exists."""
        if os.path.isfile(self.local_assign_part_config_file):
            file = self.local_assign_part_config_file
        if os.path.isfile(self.local_inventree_config_file):
            file = self.local_inventree_config_file
        elif os.path.isfile(self.global_config_file):
            file = self.global_config_file
        else:
            return

        f = FileConfig(localFilename=file)

        f.SetPath("/inventree")
        self.inventree_server = f.Read("server", self.inventree_server)
        self.inventree_username = f.Read("username", self.inventree_username)
        self.inventree_password = f.Read("password", self.inventree_password)
        self.inventree_apikey = f.Read("apikey", self.inventree_apikey)
