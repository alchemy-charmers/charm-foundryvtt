import tempfile
import unittest
from pathlib import Path

import setuppath  # noqa:F401
import mock
from operator_fixtures import OperatorTestCase


class TestCharm(OperatorTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Mock zip install
        zip_patcher = mock.patch("lib_foundry.zipfile.ZipFile")
        cls.patchers["lib_foundry.zipfile"] = zip_patcher.start()

        # Mock charmhelpers subprocess calls
        subprocess_patcher = mock.patch("charmhelpers.fetch.ubuntu.subprocess")
        cls.patchers["charmhelpers_fetch_subprocess"] = subprocess_patcher.start()
        subprocess_patcher = mock.patch("charmhelpers.core.host.subprocess")
        cls.patchers["charmhelpers_host_subprocess"] = subprocess_patcher.start()

        # Mock import_key
        import_key_patcher = mock.patch("charmhelpers.fetch.ubuntu.import_key")
        cls.patchers["fetch_import_key"] = import_key_patcher.start()

    def setUp(self):
        """Setup per-test fixtures."""
        super().setUp()

        # Setup a tmpfile for the install path
        tmp_install = tempfile.NamedTemporaryFile(
            prefix="install_", dir=self.tmpdir.name
        ).name
        self.charm.helper.install_path = Path(tmp_install)

        # Setup a tmpfile for the data path
        tmp_data = tempfile.NamedTemporaryFile(
            prefix="data_", dir=self.tmpdir.name
        ).name
        self.charm.helper.default_data_path = Path(tmp_data)

        # Setup a tmpfile for service path
        tmp_service = tempfile.NamedTemporaryFile(
            prefix="service_", dir=self.tmpdir.name
        ).name
        self.charm.helper.service_file = Path(tmp_service)

    def test_create_charm(self):
        """Verify fixtures and create a charm."""
        self.assertEqual(self.charm.state.installed, False)

    def test_install(self):
        """Test emitting an install hook."""
        self.emit("install")
        self.assertEqual(self.charm.state.installed, True)
        with open(self.charm.helper.service_file, "r") as service_file:
            content = service_file.read()
        self.assertIn("ExecStart=/usr/bin/node", content)

    def test_start(self):
        """Test emitting a start hook."""
        self.charm.state.installed = True
        self.charm.state.configured = True
        self.emit("start")
        self.assertEqual(self.charm.state.started, True)

    def test_proxy(self):
        """Test emitting reversepoxy join."""
        self.charm.state.started = True
        relation = mock.MagicMock()
        relation.id = "mock_relation_id"
        relation.name = "mock_relation_name"
        self.charm.proxy._relation = relation
        self.emit("reverseproxy_relation_joined")
        # Setting relation does a get followed by a set of the data
        get_item = relation.data.__getitem__.mock_calls[1]
        # The key to set should be config
        self.assertEqual(get_item.args[0], "config")
        # The value should include expected JSON strings
        self.assertIn('"mode": "http"', get_item.args[1])
        self.assertIn('"subdomain": "foundry"', get_item.args[1])
        self.assertIn('"external_port": 443', get_item.args[1])
        self.assertIn('"internal_port": 30000', get_item.args[1])
        self.assertIn('"check": true', get_item.args[1])
        self.assertIn('"urlbase": null', get_item.args[1])

    def test_upgrade_charm(self):
        """Test emitting upgrade charm."""
        # Not enabled
        self.assertEqual(self.charm.state.enabled, False)
        # Do not enable if charm hasn't been started yet
        self.emit("upgrade_charm")
        self.assertEqual(self.charm.state.enabled, False)
        # Enable if charm is started but was not enabled
        self.charm.state.started = True
        self.emit("upgrade_charm")
        self.assertEqual(self.charm.state.enabled, True)


if __name__ == "__main__":
    unittest.main()
