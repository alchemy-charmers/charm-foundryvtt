# FoundryVtt Charm

Overview
--------

Foundry VTT is a standalone application built for experiencing multi player tabletop RPGs
using a feature-rich and modern self-hosted application where your players connect directly
through the browser. See https://foundryvtt.com/ for details.

Quickstart
----------

Deploy the charm and attach the foundry.zip file for Linux.
```bash
juju deploy cs:~pirate-charmers/foundryvtt
juju attach-resource foundryvtt foundryvtt=./foundry.zip
```
At this time the foundry.zip file is downloaded from your account on
[https://foundryvtt.com](https://foundryvtt.com). FoundryVTT is currently in a pre-release
stage and the requirement to attach the zip file may be mitigated in the future as the
software gains other distribution methods.

After the install settles FoundryVTT will be available at the units IP address on port 30000.
Other than testing, Foundry should always be run behind a proxy and this charm supports
HAProxy. You can deploy and relate HAProxy with.
```bash
juju deploy cs:~pirate-charmers/haproxy
juju add-relation foundryvtt haproxy
```
This will make FounryVTT available at the subdomain `foundry` on HAProxy on port 443. You can
connect at `https://foundry.<haproxyip>`. Serving Foundry via TLS on port 443 will requires a
certificate which the HAProxy charm can register for you via letsencrypt. See the [HAProxy charm](https://jaas.ai/u/pirate-charmers/haproxy) for details.

There are config settings on this charm to allow some customization of the proxy
configuration.
* proxy_subdomain: Can be used to customize the subdomain if you run multiple servers.
* proxy_port: Can be set to 80 if you do not want to use TLS but is **highly discouraged** as
  your user credentials will not be encrypted if you do this.
* proxy_via_fqdn: Setting to false will register the IP instead of the fqdn with HAProxy.
  This is useful if you are installing in an environment that lacks DNS but has static IP
  assignments.

Contact
-------
 - Author: Chris Sanders <sanders.chris@gmail.com>
 - Bug Tracker: [here](https://github.com/alchemy-charmers/charm-foundryvtt/issues)
