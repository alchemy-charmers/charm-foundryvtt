#! /usr/bin/env python3
# -*- coding: utf-8 -*-
# vim:fenc=utf-8
# Copyright © 2020 Chris Sanders sanders.chris@gmail.com
# Distributed under terms of the GPL license.
"""Foundry Charm support library."""

# import base64
import logging
import zipfile
from pathlib import Path

from charmhelpers.core import host
from charmhelpers.fetch import add_source, apt_install, apt_update

from charmhelpers.core import templating


class FoundryHelper:
    """Helper module"""

    def __init__(self, config, state):
        """Initialize the module with charm config and state."""
        self.charm_config = config
        self.state = state
        self.install_path = Path("/opt/foundry/vtt")
        self.data_path = Path("/opt/foundry/userdata")
        self.service_file = Path("/etc/systemd/system/foundryvtt.service")
        self.service_name = "foundryvtt.service"
        self.node_version = "12.x"
        self.dependencies = [
            "nodejs",
            "libssl-dev",
        ]
        # self.service_name = "snap.cloudstats.cloudstats.service"

    def install_zip(self, zip_path):
        """Install the zip file."""
        # TODO: Create a system user so this doesn't run as root?
        self.install_path.mkdir(parents=True, exist_ok=True)
        self.data_path.mkdir(parents=True, exist_ok=True)
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

    def install_systemd_service(self):
        """Install systemd service file."""
        context = {}
        context["install_path"] = self.install_path
        context["data_path"] = self.data_path
        templating.render(self.service_name, self.service_file, context, perms=0o440)
