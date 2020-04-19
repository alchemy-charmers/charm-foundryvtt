#! /usr/bin/env python3
# -*- coding: utf-8 -*-
# vim:fenc=utf-8
# Copyright © 2020 Chris Sanders sanders.chris@gmail.com
# Distributed under terms of the GPL license.
"""Operator Charm main library."""
# Load modules from lib directory
import logging
import socket
from zipfile import BadZipFile

import setuppath  # noqa:F401
from charmhelpers.core import host
from interface_reverseproxy.operator_requires import (
    ProxyConfig,  # ProxyConfigError,
    ReverseProxyRequires,
)
from lib_foundry import FoundryHelper
from ops.charm import CharmBase
from ops.framework import StoredState
from ops.main import main
from ops.model import ActiveStatus, BlockedStatus, MaintenanceStatus, ModelError


class FoundryvttCharm(CharmBase):
    """Class reprisenting this Operator charm."""

    state = StoredState()

    def __init__(self, *args):
        """Initialize charm and configure states and events to observe."""
        super().__init__(*args)
        # -- standard hook observation
        self.framework.observe(self.on.install, self.on_install)
        self.framework.observe(self.on.start, self.on_start)
        self.framework.observe(self.on.config_changed, self.on_config_changed)
        # -- initialize states --
        self.state.set_default(installed=False)
        self.state.set_default(configured=False)
        self.state.set_default(started=False)
        # -- relations --
        self.proxy = ReverseProxyRequires(self, "reverseproxy")
        self.framework.observe(self.proxy.on.proxy_connected, self.on_proxy_connected)
        # Setup helper
        self.helper = FoundryHelper(self.model.config, self.state)

    def on_install(self, event):
        """Handle install state."""
        self.unit.status = MaintenanceStatus("Installing charm software")
        # Perform install tasks
        zip_path = None
        try:
            zip_path = self.model.resources.fetch("foundryvtt")
        except ModelError:
            self.unit.status = BlockedStatus("Upload foundryvtt resource to proceed")
            logging.warning(
                "No install resource available, install blocked, deferring event: {}".format(
                    event.handle
                )
            )
            self._defer_once(event)

            return
        # Install the resource
        try:
            self.helper.install_zip(zip_path)
        except BadZipFile:
            self.unit.status = BlockedStatus("Bad zip file, upload a new resource")
            logging.error(
                "Could not install resource, deferring event: {}".format(event.handle)
            )
            self._defer_once(event)

            return
        self.unit.status = MaintenanceStatus("Installing dependencies")
        logging.info("Installing dependencies")
        self.helper.add_sources()
        self.helper.install_dependencies()
        self.helper.install_systemd_service()
        self.unit.status = MaintenanceStatus("Install complete")
        logging.info("Install of software complete")
        self.state.installed = True

    def on_config_changed(self, event):
        """Handle config changed."""

        if not self.state.installed:
            logging.warning(
                "Config changed called before install complete, deferring event: {}.".format(
                    event.handle
                )
            )
            self._defer_once(event)

            return

        if self.state.started:
            # Stop if necessary for reconfig
            logging.info(
                "Stopping for configuration, event handle: {}".format(event.handle)
            )
        # Configure the software
        logging.info("Configuring")
        self.state.configured = True

    def on_start(self, event):
        """Handle start state."""

        if not self.state.configured:
            logging.warning(
                "Start called before configuration complete, deferring event: {}".format(
                    event.handle
                )
            )
            self._defer_once(event)

            return
        self.unit.status = MaintenanceStatus("Starting charm software")
        # Start software
        host.service_start(self.helper.service_name)
        self.unit.status = ActiveStatus("Unit is ready")
        self.state.started = True
        logging.info("Started")

    # - mode: (Optional) set 'tcp' or 'http' routing, defaults to 'http'
    # - urlbase: (Optional if subdomain is provided) the base url to redirect to his charm, including leading /
    # - acl-local: (Optional) restrict access to local ip address ranges for this backend
    # - rewrite-path: (Optional) remove the urlbase from the path
    # - subdomain: (Optional if urlbase is provided) a subdomain to redirect to this charm
    # - external_port: the external port to listen on
    # - internal_host: the internal host to redirect to
    # - internal_port: the internal port to redirect to
    # - group_id: (Optional) all relations with a matching group id will share the same server pool. urlbase, subdomain, and external_port should match on all members of the group
    # - proxypass: (Optional) set Forward-For and Forward-Proto headers
    # - ssl: (Optional) Connect to the backend via ssl regardless of the port
    # - ssl-verify: (Optional) Boolean, set to True to check SSL certs. False will not check
    # - check: (Optional) perform port availability check, defaults to True set False to not check
    def on_proxy_connected(self, event):
        """Handle proxy connected event."""
        config = {
            "mode": "http",
            "subdomain": "foundry",
            "external_port": 80,
            "internal_host": socket.getfqdn(),
            "internal_port": 30000,
        }
        logging.info("Proxy is connected, configuring: {}".format(config))
        proxy_config = ProxyConfig(config)
        logging.debug("Proxy config: {}".format(proxy_config))
        self.proxy.set_proxy_config(proxy_config)
        logging.debug("Proxy set_proxy_config conplete")

    def _defer_once(self, event):
        """Defer the given event, but only once."""
        notice_count = 0
        handle = str(event.handle)

        for event_path, _, _ in self.framework._storage.notices(None):
            if event_path.startswith(handle.split("[")[0]):
                notice_count += 1
                logging.debug("Found event: {} x {}".format(event_path, notice_count))

        if notice_count > 1:
            logging.debug(
                "Not deferring {} notice count of {}".format(handle, notice_count)
            )
        else:
            logging.debug(
                "Deferring {} notice count of {}".format(handle, notice_count)
            )
            event.defer()


if __name__ == "__main__":
    main(FoundryvttCharm)
