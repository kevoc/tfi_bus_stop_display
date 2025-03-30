
"""
`mqtt_controller`
====================================================

MQTT controller allows you to specify an adhoc command-response
protocol over MQTT, where a published command triggers an
action or returns some information.

* Author: Kevin O'Connell

"""

# NOTE: when using MQTT over TLS, there are 2 ways to authenticate
#       1) With a CA cert to validate the server, and a username &
#          password to authenticate.
#       2) With a CA cert to validate the server, and a client certificate
#          private key signed by the same CA to authenticate.
#
#       If you provide a username and password to MQTTController.over_ssl(),
#       it is assumed you're using method 1. In that case, the `auth_cert`
#       should be just the path to the CA certificate with no modifications.
#       If you're authenticating with method 2, the CA cert, client cert and
#       private key should be packaged into 1 file. You must use the
#       `tools/create_cert_bundle.sh` script to make your bundle. It will
#       validate all 3 certificates, and will convert them to DER format as
#       needed. MicroPython only works with DER certs/private keys.
#


import re
import ssl
import machine

from . import MQTTClient, MQTTException


_REQUIRED_CERTS = ['ca', 'client_cert', 'client_key']


def _client_id():
    """Generate a unique client ID that won't change between reboots"""
    return 'uPy-' + '-'.join([f'{b:02X}' for b in machine.unique_id()])


def unbundle_certificates(bundle: bytes):
    """Take a cert bundle file and return a dictionary with the names
    of each certificate and its cert data as values."""

    # cert comment format is: ##### cert_name bytes #####
    cert_comment_regex = re.compile(b"##### ([-a-zA-Z0-9_]+) ([0-9]+) #####")

    # iterate over the full bundle, finding results
    certs = {}
    current_offset = 0
    while True:
        match = cert_comment_regex.search(bundle[current_offset:])
        if match is None:
            break
        name, byte_count = match.group(1).decode('utf-8'), int(match.group(2))
        start_of_cert = current_offset + match.end() + 1
        end_of_cert = start_of_cert + byte_count
        cert_data = bundle[start_of_cert:end_of_cert]

        certs[name] = cert_data
        current_offset = end_of_cert

    if not certs:
        # see the header of this file for explanation of bundling
        raise ValueError('not a bundled certificate file')

    return certs


def unbundle_certificate_file(path):
    """Read in and unbundle the certificates from the given file."""

    with open(path, 'rb') as f:
        return unbundle_certificates(f.read())


def validate_bundle(cert_bundle):
    """Ensure the required certificates are in the bundle"""

    for cert in _REQUIRED_CERTS:
        if cert not in cert_bundle:
            raise ValueError(f'required cert {cert} not in bundle')


class MQTTController(MQTTClient):
    """A controller to run various commands. """

    def __init__(self, mqtt_server: str, user: str, password: str, port: int = 1883,
                 client_id: str = None, keepalive: int = 30, ssl_context: ssl.SSLContext = None):

        self._root_topic = None

        MQTTClient.__init__(self, client_id or _client_id(),
                            mqtt_server, port=port,
                            user=user, password=password,
                            keepalive=keepalive,
                            ssl=ssl_context)
        self.connect()

    def set_root_topic(self, topic):
        """Set the root topic to publish and subscribe to."""
        self._root_topic = topic.format(id=_client_id())

    @classmethod
    def over_ssl(cls, mqtt_server: str, auth_cert_file: str, user: str = None,
                 password: str = None, port: int = 8883, client_id: str = None,
                 keepalive: int = 30):
        """Create an MQTT Client instance secured with SSL."""

        if user or password:
            # assuming auth method 1
            ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
            ssl_context.load_verify_locations(cafile=auth_cert_file)
        else:
            # assuming auth method 2
            certs = unbundle_certificate_file(auth_cert_file)
            validate_bundle(certs)

            ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
            ssl_context.load_verify_locations(cadata=certs['ca'])
            ssl_context.load_cert_chain(certs['client_cert'], certs['client_key'])

        ssl_context.verify_mode = ssl.CERT_REQUIRED

        return cls(mqtt_server, user, password, port=port, client_id=client_id,
                   keepalive=keepalive, ssl_context=ssl_context)

    def publish(self, topic, msg, retain=False, qos=0):
        super().publish(self._root_topic + topic,
                        msg, retain=retain, qos=qos)
