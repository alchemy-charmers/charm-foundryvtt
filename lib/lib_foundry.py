#! /usr/bin/env python3
# -*- coding: utf-8 -*-
# vim:fenc=utf-8
# Copyright © 2020 Chris Sanders sanders.chris@gmail.com
# Distributed under terms of the GPL license.
"""Foundry Charm support library."""

import logging
import shutil
import zipfile
from pathlib import Path

from charmhelpers.core import host, templating
from charmhelpers.fetch import add_source, apt_install, apt_update


class PathError(Exception):
    """Raise if there is an issue with a path."""

    pass


class FoundryHelper:
    """Helper module"""

    def __init__(self, config, state):
        """Initialize the module with charm config and state."""
        self.charm_config = config
        self.state = state
        self.install_path = Path("/opt/foundry/vtt")
        self.default_data_path = Path("/opt/foundry/userdata")
        self.service_file = Path("/etc/systemd/system/foundryvtt.service")
        self.service_name = "foundryvtt.service"
        self.node_version = "12.x"
        self.dependencies = [
            "nodejs",
            "libssl-dev",
        ]

    def install_zip(self, zip_path):
        """Install the zip file."""
        self.install_path.mkdir(parents=True, exist_ok=True)
        self.default_data_path.mkdir(parents=True, exist_ok=True)

        if not self.state.current_data_path:
            self.state.current_data_path = str(self.default_data_path)
        with zipfile.ZipFile(zip_path, "r") as zip_ref:
            zip_ref.extractall(self.install_path)

    def add_sources(self):
        """Ensure apt repositories are configured and updated for use."""
        distro = host.get_distrib_codename()
        apt_repo = self.charm_config.get("node_repo")
        apt_key = self.charm_config.get("node_repo_key")
        version = "node_{}".format(self.node_version)
        apt_line = "deb {}/{} {} main".format(apt_repo, version, distro)
        logging.info(
            "Installing and updating apt source {} key {})".format(apt_line, apt_key)
        )
        add_source(apt_line, apt_key)
        apt_update()

    def install_dependencies(self):
        """Install dependencies."""
        apt_install(self.dependencies, fatal=True)

    def render_systemd_service(self):
        """Install systemd service file."""
        context = {}
        context["install_path"] = self.install_path
        context["data_path"] = self.state.current_data_path
        templating.render(self.service_name, self.service_file, context, perms=0o440)

    def migrate_data(self):
        """Migrate data to a new path."""

        if not self.needs_data_migration:
            logging.error("Cowardly refusing to migrate data unnecessarily")

            return
        data_path = Path(self.state.current_data_path)

        if not self.charm_config.get("custom_data_path"):
            # Migrate current -> default
            target_path = self.default_data_path
            self.default_data_path.mkdir(parents=True, exist_ok=True)
        else:
            # Migrate current -> custom
            target_path = Path(self.charm_config["custom_data_path"])

        if not target_path.is_dir():
            raise PathError("Destination directory does not exist")
        if any(target_path.iterdir()):
            raise PathError("Destination directory is not empty")
        for item in data_path.iterdir():
            shutil.move(str(item.resolve()), str(target_path))
        self.state.current_data_path = str(target_path)

    @property
    def needs_data_migration(self):
        """Returns true if the datapath config has changed and needs to be migrated."""
        custom_path = self.charm_config.get("custom_data_path")

        if custom_path:
            if custom_path != self.state.current_data_path:
                return True
        elif self.state.current_data_path != str(self.default_data_path):
            return True

        return False
