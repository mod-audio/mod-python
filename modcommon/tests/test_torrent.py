# -*- coding: utf-8

import unittest, os, random, json
from modcommon.communication.torrent import TorrentGenerator, TorrentReceiver

class Communication(unittest.TestCase):

    def generate_file(self, basedir, name, size):
        fp = open(os.path.join(basedir, name), 'w')
        fp.write(''.join([ chr(random.randint(0,255)) for i in range(size) ]))
        fp.close()

    def generate_dir(self):
        uniqid = ''.join([ random.choice('abcdefghijklmnopiqrstuwxyz') for i in range(8) ])
        basedir = os.path.join('/tmp', uniqid)
        os.mkdir(basedir)
        self.dirs.append(basedir)
        return basedir

    def setUp(self):
        self.dirs = []

    def tearDown(self):
        for basedir in self.dirs:
            for f in os.listdir(basedir):
                os.remove(os.path.join(basedir, f))
            os.rmdir(basedir)

    def test_generated_file_is_received(self):
        name = 'this_is_a_test_file'
        origin = self.generate_dir()
        self.generate_file(origin, name, 2**8)

        gen = TorrentGenerator(os.path.join(origin, name), piece_length=2**6)

        torrent_data = gen.torrent_data()
        torrent = json.loads(torrent_data)
        tmpdir = self.generate_dir()
        destination = self.generate_dir()
        receiver = TorrentReceiver(download_tmp_dir=tmpdir, destination_dir=destination)
        receiver.load(torrent_data)

        # There must be an id now
        assert receiver.torrent_id

        self.assertTrue(not receiver.complete)
        self.assertEquals(receiver.percent, 0)

        for i in range(len(torrent['pieces'])):
            chunk = gen.get_chunk(i)
            receiver.receive(i, chunk)

        self.assertTrue(receiver.complete)
        self.assertEquals(receiver.percent, 100)

        receiver.finish()

        self.assertTrue(os.path.exists(os.path.join(destination, name)))
        self.assertEquals(open(os.path.join(destination, name)).read(),
                          open(os.path.join(origin, name)).read())

    def test_generated_file_is_received_when_last_piece_is_not_full(self):
        # Same test as before, but now we generate a file with size 2**8-5 instead of 2**8
        name = 'this_is_a_test_file'
        origin = self.generate_dir()
        self.generate_file(origin, name, 2**8-5)

        gen = TorrentGenerator(os.path.join(origin, name), piece_length=2**6)

        torrent_data = gen.torrent_data()
        torrent = json.loads(torrent_data)
        tmpdir = self.generate_dir()
        destination = self.generate_dir()
        receiver = TorrentReceiver(download_tmp_dir=tmpdir, destination_dir=destination)
        receiver.load(torrent_data)

        self.assertTrue(not receiver.complete)
        self.assertEquals(receiver.percent, 0)

        for i in range(len(torrent['pieces'])):
            chunk = gen.get_chunk(i)
            receiver.receive(i, chunk)

        self.assertTrue(receiver.complete)
        self.assertEquals(receiver.percent, 100)

        receiver.finish()

        self.assertTrue(os.path.exists(os.path.join(destination, name)))
        self.assertEquals(open(os.path.join(destination, name)).read(),
                          open(os.path.join(origin, name)).read())

    def test_receiving_leaves_nothing_behind(self):
        name = 'this_is_a_test_file'
        origin = self.generate_dir()
        self.generate_file(origin, name, 2**8)

        gen = TorrentGenerator(os.path.join(origin, name), piece_length=2**6)

        torrent_data = gen.torrent_data()
        torrent = json.loads(torrent_data)
        tmpdir = self.generate_dir()
        destination = self.generate_dir()
        receiver = TorrentReceiver(download_tmp_dir=tmpdir, destination_dir=destination)
        receiver.load(torrent_data)

        for i in range(len(torrent['pieces'])):
            chunk = gen.get_chunk(i)
            receiver.receive(i, chunk)

        receiver.finish()

        self.assertEquals(len(os.listdir(tmpdir)), 0)

    def test_file_can_be_received_out_of_order(self):
        name = 'this_is_a_test_file'
        origin = self.generate_dir()
        self.generate_file(origin, name, 2**8-5)

        gen = TorrentGenerator(os.path.join(origin, name), piece_length=2**6)

        torrent_data = gen.torrent_data()
        torrent = json.loads(torrent_data)
        tmpdir = self.generate_dir()
        destination = self.generate_dir()
        receiver = TorrentReceiver(download_tmp_dir=tmpdir, destination_dir=destination)
        receiver.load(torrent_data)

        self.assertTrue(not receiver.complete)
        self.assertEquals(receiver.percent, 0)

        for i in range(len(torrent['pieces'])):
            if i % 2 == 0:
                continue
            chunk = gen.get_chunk(i)
            receiver.receive(i, chunk)
        for i in range(len(torrent['pieces'])):
            if i % 2 == 1:
                continue
            chunk = gen.get_chunk(i)
            receiver.receive(i, chunk)

        self.assertTrue(receiver.complete)
        self.assertEquals(receiver.percent, 100)

        receiver.finish()

        self.assertTrue(os.path.exists(os.path.join(destination, name)))
        self.assertEquals(open(os.path.join(destination, name)).read(),
                          open(os.path.join(origin, name)).read())

    def test_torrent_can_be_signed(self):
        from modcommon.communication.crypto import NewKey
        keydir = self.generate_dir()

        key = NewKey(512)
        privkey = os.path.join(keydir, 'key.pem')
        pubkey = os.path.join(keydir, 'key.pub')
        open(privkey, 'w').write(key.private)
        open(pubkey, 'w').write(key.public)

        wrong = os.path.join(keydir, 'wrong.pub')
        open(wrong, 'w').write(NewKey(512).public)

        name = 'this_is_a_test_file'
        origin = self.generate_dir()
        destination = self.generate_dir()
        self.generate_file(origin, name, 2**8)

        gen = TorrentGenerator(os.path.join(origin, name), piece_length=2**6)

        torrent_data = gen.torrent_data(privkey)
        torrent = json.loads(torrent_data)
        tmpdir = self.generate_dir()

        # Let's try to load file without key, must fail
        try:
            receiver = TorrentReceiver(download_tmp_dir=tmpdir, destination_dir=destination)
            receiver.load(torrent_data)
        except:
            pass
        else:
            self.fail()

        # Now with wrong key, must fail
        try:
            receiver = TorrentReceiver(download_tmp_dir=tmpdir, destination_dir=destination, 
                                       remote_public_key=wrong)
            receiver.load(torrent_data)
        except:
            pass
        else:
            self.fail()

        # Now with right key it must go ok
        receiver = TorrentReceiver(download_tmp_dir=tmpdir, destination_dir=destination, 
                                   remote_public_key=pubkey)
        receiver.load(torrent_data)

        for i in range(len(torrent['pieces'])):
            chunk = gen.get_chunk(i)
            receiver.receive(i, chunk)

        self.assertTrue(receiver.complete)
        self.assertEquals(receiver.percent, 100)

        receiver.finish()

        self.assertTrue(os.path.exists(os.path.join(destination, name)))
        self.assertEquals(open(os.path.join(destination, name)).read(),
                          open(os.path.join(origin, name)).read())

    def test_unsigned_torrent_cant_be_opened_with_key(self):
        from modcommon.communication.crypto import NewKey
        keydir = self.generate_dir()
        pubkey = os.path.join(keydir, 'key.pub')
        open(pubkey, 'w').write(NewKey(512).public)

        name = 'this_is_a_test_file'
        origin = self.generate_dir()
        self.generate_file(origin, name, 2**8)

        gen = TorrentGenerator(os.path.join(origin, name), piece_length=2**14)

        torrent_data = gen.torrent_data()
        torrent = json.loads(torrent_data)
        tmpdir = self.generate_dir()

        try:
            receiver = TorrentReceiver(download_tmp_dir=tmpdir,
                                       remote_public_key=pubkey)
            receiver.load(torrent_data)
        except:
            pass
        else:
            self.fail()

    def test_key_wont_be_necessary_to_receive_pieces_after_transference_has_started(self):
        from modcommon.communication.crypto import NewKey
        keydir = self.generate_dir()

        key = NewKey(512)
        privkey = os.path.join(keydir, 'key.pem')
        pubkey = os.path.join(keydir, 'key.pub')
        open(privkey, 'w').write(key.private)
        open(pubkey, 'w').write(key.public)

        name = 'this_is_a_test_file'
        origin = self.generate_dir()
        destination = self.generate_dir()
        self.generate_file(origin, name, 2**8)

        gen = TorrentGenerator(os.path.join(origin, name), piece_length=2**6)

        torrent_data = gen.torrent_data(privkey)
        torrent = json.loads(torrent_data)
        tmpdir = self.generate_dir()

        receiver = TorrentReceiver(download_tmp_dir=tmpdir, destination_dir=destination, 
                                   remote_public_key=pubkey)
        receiver.load(torrent_data)

        # Torrent has been created, so we can recreate it using the generated id
        # and no key
        receiver = TorrentReceiver(receiver.torrent_id, 
                                   download_tmp_dir=tmpdir, destination_dir=destination)

        for i in range(len(torrent['pieces'])):
            chunk = gen.get_chunk(i)
            receiver.receive(i, chunk)

        self.assertTrue(receiver.complete)
        self.assertEquals(receiver.percent, 100)

        receiver.finish()

        self.assertTrue(os.path.exists(os.path.join(destination, name)))
        self.assertEquals(open(os.path.join(destination, name)).read(),
                          open(os.path.join(origin, name)).read())
        

    def test_file_smaller_than_chunk_will_be_delivered_in_torrent(self):
        name = 'this_is_a_test_file'
        origin = self.generate_dir()
        self.generate_file(origin, name, 2**8)

        gen = TorrentGenerator(os.path.join(origin, name), piece_length=2**8)

        torrent_data = gen.torrent_data()
        torrent = json.loads(torrent_data)
        tmpdir = self.generate_dir()
        destination = self.generate_dir()
        receiver = TorrentReceiver(download_tmp_dir=tmpdir, destination_dir=destination)
        receiver.load(torrent_data)

        self.assertTrue(receiver.complete)
        self.assertEquals(receiver.percent, 100)

        # Lets do the same for bigger chunk
        gen = TorrentGenerator(os.path.join(origin, name), piece_length=2**9)

        torrent_data = gen.torrent_data()
        torrent = json.loads(torrent_data)
        tmpdir = self.generate_dir()
        destination = self.generate_dir()
        receiver = TorrentReceiver(download_tmp_dir=tmpdir, destination_dir=destination)
        receiver.load(torrent_data)

        self.assertTrue(receiver.complete)
        self.assertEquals(receiver.percent, 100)

        # Now let's finish and check file

        receiver.finish()

        self.assertTrue(os.path.exists(os.path.join(destination, name)))
        self.assertEquals(open(os.path.join(destination, name)).read(),
                          open(os.path.join(origin, name)).read())

    def test_partial_file_can_be_continued_even_same_torrent_data_is_used(self):
        name = 'this_is_a_test_file'
        origin = self.generate_dir()
        self.generate_file(origin, name, 2**8)

        gen = TorrentGenerator(os.path.join(origin, name), piece_length=2**6)

        torrent_data = gen.torrent_data()
        torrent = json.loads(torrent_data)
        tmpdir = self.generate_dir()
        destination = self.generate_dir()
        receiver = TorrentReceiver(download_tmp_dir=tmpdir, destination_dir=destination)
        receiver.load(torrent_data)

        size = len(torrent['pieces'])

        for i in range(size/2):
            chunk = gen.get_chunk(i)
            receiver.receive(i, chunk)
            
        receiver = TorrentReceiver(download_tmp_dir=tmpdir, destination_dir=destination)
        receiver.load(torrent_data)

        self.assertEquals(receiver.percent, 50)

        for i in range(size/2, size):
            chunk = gen.get_chunk(i)
            receiver.receive(i, chunk)
            
        self.assertEquals(receiver.percent, 100)
        self.assertTrue(receiver.complete)

        receiver.finish()

        self.assertTrue(os.path.exists(os.path.join(destination, name)))
        self.assertEquals(open(os.path.join(destination, name)).read(),
                          open(os.path.join(origin, name)).read())
        
    def test_completed_file_wont_be_downloaded_again(self):
        name = 'this_is_a_test_file'
        origin = self.generate_dir()
        self.generate_file(origin, name, 2**8)

        gen = TorrentGenerator(os.path.join(origin, name), piece_length=2**6)

        torrent_data = gen.torrent_data()
        torrent = json.loads(torrent_data)
        tmpdir = self.generate_dir()
        destination = self.generate_dir()
        receiver = TorrentReceiver(download_tmp_dir=tmpdir, destination_dir=destination)
        receiver.load(torrent_data)

        size = len(torrent['pieces'])

        for i in range(size):
            chunk = gen.get_chunk(i)
            receiver.receive(i, chunk)
            
        receiver.finish()

        receiver = TorrentReceiver(download_tmp_dir=tmpdir, destination_dir=destination)
        receiver.load(torrent_data)

        self.assertEquals(receiver.percent, 100)
        self.assertTrue(receiver.complete)

        receiver.finish()

        self.assertTrue(os.path.exists(os.path.join(destination, name)))
        self.assertEquals(open(os.path.join(destination, name)).read(),
                          open(os.path.join(origin, name)).read())
        
