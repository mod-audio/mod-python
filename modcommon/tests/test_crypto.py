# -*- coding: utf-8

import unittest, os
from modcommon.communication.crypto import NewKey, Sender, Receiver

class Communication(unittest.TestCase):

    def setUp(self):
        self.sendr_prv = '/tmp/sendr_test.pem'
        self.sendr_pub = '/tmp/sendr_test.pub'
        self.recvr_prv = '/tmp/recvr_test.pem'
        self.recvr_pub = '/tmp/recvr_test.pub'
        self.wrong_prv = '/tmp/wrong_test.pem'
        self.wrong_pub = '/tmp/wrong_test.pub'
        sendr_key = NewKey(256)
        recvr_key = NewKey(256)
        wrong_key = NewKey(256)

        open(self.sendr_prv, 'w').write(sendr_key.private)
        open(self.sendr_pub, 'w').write(sendr_key.public)
        open(self.recvr_prv, 'w').write(recvr_key.private)
        open(self.recvr_pub, 'w').write(recvr_key.public)
        open(self.wrong_prv, 'w').write(wrong_key.private)
        open(self.wrong_pub, 'w').write(wrong_key.public)

    def tearDown(self):
        for key in (self.sendr_prv, self.sendr_pub,
                    self.recvr_prv, self.recvr_pub,
                    self.wrong_prv, self.wrong_pub):
            os.remove(key)

    def test_communication_packed_by_sender_is_received_by_receiver(self):
        sender = Sender(self.sendr_prv, "Hello World")
        receiver = Receiver(self.sendr_pub, sender.pack())

        self.assertEquals(receiver.unpack(), "Hello World")

    def test_message_with_wrong_key_is_rejected(self):
        sender = Sender(self.sendr_prv, "Hello World")
        receiver = Receiver(self.wrong_pub, sender.pack())
        try:
            receiver.unpack()
        except Receiver.UnauthorizedMessage:
            pass
        else:
            self.fail()
        
    def test_packed_communication_is_json_serializable(self):
        sender = Sender(self.sendr_prv, "Hello World")
        import json
        json.dumps(sender.pack())



if __name__ == '__main__':
    unittest.main()
        
