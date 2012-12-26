# -*- coding: utf-8 -*-

import os, json, base64, zlib
from hashlib import sha1
from subprocess import Popen, PIPE

class NewKey(object):

    def __init__(self, length=2048):
        devnull = open('/dev/null', 'w')
        proc = Popen(['openssl', 'genrsa', str(length)], stdout=PIPE, stderr=devnull)
        proc.wait()
        self.private = proc.stdout.read()

    @property
    def public(self):
        return self.generate_public_key(self.private)

    @classmethod
    def generate_public_key(cls, private_key):
        devnull = open('/dev/null', 'w')
        proc = Popen(['openssl', 'rsa', '-pubout'], stdout=PIPE, stdin=PIPE, stderr=devnull)
        proc.stdin.write(private_key)
        proc.stdin.close()
        proc.wait()
        return proc.stdout.read()

class Sender(object):

    def __init__(self, keyfile, msg):
        self.msg = msg
        self.keyfile = keyfile
        assert os.path.exists(keyfile)

    @property
    def signed(self):
        """
        Returns a RSA signed message
        """
        cmd = 'openssl rsautl -sign -inkey'.split() + [self.keyfile]
        proc = Popen(cmd, stdout=PIPE, stdin=PIPE)
        proc.stdin.write(self.msg)
        proc.stdin.close()
        proc.wait()
        return proc.stdout.read()

    def pack(self):
        return base64.b64encode(self.signed)
        
class Receiver(object):

    class BrokenMessage(Exception):
        pass

    class InvalidMessage(Exception):
        pass

    class UnauthorizedMessage(Exception):
        pass

    def __init__(self, peerkey, pack):
        self.peerkey = peerkey
        self.pack = pack

    def verify_signature(self, signed):
        """
        Returns a base64 encoded RSA signature of the checksum of the message
        """
        cmd = 'openssl rsautl -verify -pubin -inkey'.split() + [self.peerkey]
        proc = Popen(cmd, stdout=PIPE, stdin=PIPE, stderr=PIPE)
        proc.stdin.write(signed)
        proc.stdin.close()
        proc.wait()
        out = proc.stdout.read()
        err = proc.stderr.read()
        if 'operation error' in err:
            raise self.UnauthorizedMessage
        return out

    def unpack(self):
        try:
            msg = base64.b64decode(self.pack)
        except:
            raise self.InvalidMessage

        return self.verify_signature(msg)
