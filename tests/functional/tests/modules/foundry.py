import concurrent.futures
import logging
import unittest

import zaza.model


class TestBase(unittest.TestCase):
    """ Base class for functional charm tests. """

    @classmethod
    def setUpClass(cls):
        """ Run setup for tests. """
        cls.model_name = zaza.model.get_juju_model()
        cls.application_name = "foundry-vtt"


class ResourceTests(TestBase):
    """Test resource uploads."""

    def test01_wrong_resource(self):
        """Test uploading an invalid install resource."""
        zaza.model.attach_resource(
            self.application_name, "foundryvtt", "./tests/resources/foundryvtt-zero.zip"
        )
        try:
            zaza.model.block_until_wl_status_info_starts_with(
                self.application_name,
                status="Bad zip file, upload a new resource",
                timeout=60,
            )
        except concurrent.futures._base.TimeoutError:
            self.fail("Timed out waiting for invalid snap upload test.")

    def test02_right_resource(self):
        """Test uploading a valid install resource."""
        zaza.model.attach_resource(
            self.application_name, "foundryvtt", "./tests/resources/foundryvtt.zip"
        )
        try:
            zaza.model.block_until_wl_status_info_starts_with(
                self.application_name, status="Unit is ready", timeout=60
            )
        except concurrent.futures._base.TimeoutError:
            self.fail("Timed out waiting for Unit to become ready.")


class ConfigTests(TestBase):
    """Test config parameters."""

    def test01_change_data_path(self):
        """Test moving the data_path."""
        try:
            zaza.model.block_until_file_has_contents(
                self.application_name,
                "/opt/foundry/userdata/Config/options.json",
                '"port": 30000',
                timeout=30,
            )
            logging.info("default path verified")
        except concurrent.futures._base.TimeoutError:
            self.fail("Timed out waiting test.")

        zaza.model.run_on_unit("foundry-vtt/0", "mkdir /tmp/data")
        zaza.model.set_application_config(
            self.application_name, {"custom_data_path": "/tmp/data"}
        )
        try:
            zaza.model.block_until_file_missing(
                self.application_name,
                "/opt/foundry/userdata/Config/options.json",
                timeout=30,
            )
            logging.info("default path removed")
        except concurrent.futures._base.TimeoutError:
            self.fail("Timed out waiting for test.")

        try:
            zaza.model.block_until_file_has_contents(
                self.application_name,
                "/tmp/data/Config/options.json",
                '"port": 30000',
                timeout=30,
            )
            logging.info("custom path verified")
        except concurrent.futures._base.TimeoutError:
            self.fail("Timed out waiting for test.")

    def test02_path_not_empty(self):
        """Test moving to a non-empty directory."""
        zaza.model.set_application_config(
            self.application_name, {"custom_data_path": "/opt/foundry/vtt"}
        )
        try:
            zaza.model.block_until_unit_wl_status(
                "foundry-vtt/0", "blocked", timeout=30,
            )
            unit = zaza.model.get_unit_from_name(
                "foundry-vtt/0", model_name=self.model_name
            )
            assert "Destination directory is not empty" in unit.workload_status_message
            logging.info("Verified data path blocks on non-empty directory")
        except concurrent.futures._base.TimeoutError:
            self.fail("Timed out waiting for test!")
        zaza.model.set_application_config("foundry-vtt", {"custom_data_path": ""})
        try:
            zaza.model.block_until_file_has_contents(
                "foundry-vtt",
                "/opt/foundry/userdata/Config/options.json",
                '"port": 30000',
                timeout=30,
            )
            logging.info("default path verified")
        except concurrent.futures._base.TimeoutError:
            self.fail("Timed out waiting for test.")

    def test03_path_not_empty(self):
        """Test moving to path that doesn't exist."""
        zaza.model.set_application_config(
            self.application_name, {"custom_data_path": "/tmp/does-not-exist"}
        )
        try:
            zaza.model.block_until_unit_wl_status(
                "foundry-vtt/0", "blocked", timeout=30,
            )
            unit = zaza.model.get_unit_from_name(
                "foundry-vtt/0", model_name=self.model_name
            )
            assert (
                "Destination directory does not exist" in unit.workload_status_message
            )
            logging.info("Verified data path blocks on missing directory")
        except concurrent.futures._base.TimeoutError:
            self.fail("Timed out waiting for test!")
        zaza.model.set_application_config(
            self.application_name, {"custom_data_path": ""}
        )
        try:
            zaza.model.block_until_file_has_contents(
                "foundry-vtt",
                "/opt/foundry/userdata/Config/options.json",
                '"port": 30000',
                timeout=30,
            )
            logging.info("default path verified")
        except concurrent.futures._base.TimeoutError:
            self.fail("Timed out waiting for test.")
