import concurrent.futures
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
                self.application_name, status="Bad zip file, upload a new resource", timeout=60
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
