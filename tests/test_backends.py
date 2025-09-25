import unittest
import pytest
import socket
from botocore.exceptions import ClientError

class TestBackends(unittest.TestCase):

    #
    # I'm not convinced this test 100% proves we have access to all the backends. it does
    # seem to check google, parimiko and boto. azure is less clear. but it's something.
    #
    def test_smart_open_backends(self):
        import smart_open
        errors = []

        schemes = {
            's3': 's3://bucket/key',
            'sftp': 'sftp://user@host/path',
            'azure': 'azure://container/blob',
            'gs': 'gs://bucket/blob'
        }

        for scheme, uri in schemes.items():
            with pytest.raises( (OSError, ValueError, TypeError, ClientError, socket.gaierror) ):
                with smart_open.open(uri, 'rb'):
                    ...

