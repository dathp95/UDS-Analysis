import tempfile
import time
import unittest
from dataclasses import replace
from pathlib import Path
from threading import Event

import can
from core.can_interface_view import CanFrameView


def raw(sequence=1,channel=0,**changes):
    return replace(CanFrameView(.001*sequence,'RX',0x760,2,b'\x01\x02',
        1_700_000_000+.001*sequence,10+.001*sequence,channel,False,'',False,False,
        'session',sequence,channel,1_700_000_000+.001*sequence,'driver'),**changes)


class BlfRecordingTests(unittest.TestCase):
    def setUp(self):
        self.directory=tempfile.TemporaryDirectory(dir=Path.cwd())
        self.addCleanup(self.directory.cleanup)
        self.path=Path(self.directory.name)/'capture.blf'

    def recorder(self,**kwargs):
        from services.can.blf_recording_service import BlfRecordingService
        service=BlfRecordingService(**kwargs)
        self.addCleanup(lambda:(service.stop(),service.wait(5)))
        return service

    def ready(self,service):
        deadline=time.monotonic()+3
        while service.snapshot.state=='STARTING' and time.monotonic()<deadline: time.sleep(.001)
        self.assertEqual(service.snapshot.state,'RECORDING',service.snapshot)

    def finish(self,service):
        service.stop();self.assertTrue(service.wait(3))
        return service.snapshot

    def test_round_trip_channels_direction_duplicates_echo_and_flags(self):
        for channel in (0,1):
            path=self.path.with_name(f'{channel}.blf')
            service=self.recorder();service.start(path,'session');self.ready(service)
            events=[raw(1,channel),raw(2,channel),raw(3,channel,direction='TX',can_id=0x681,tx_origin='driver_accepted'),
                    raw(4,channel,direction='TX',can_id=0x681,tx_origin='observed_echo',echo_of_sequence=3),
                    raw(5,channel,can_id=0x123456,is_extended_id=True)]
            for event in events: service.offer(event)
            result=self.finish(service)
            self.assertTrue(result.complete,result)
            self.assertEqual((result.captured,result.written,result.dropped,result.echoes),(4,4,0,1))
            with can.BLFReader(path) as reader: messages=list(reader)
            self.assertEqual(len(messages),4)
            self.assertEqual([m.channel for m in messages],[channel]*4)
            self.assertEqual([m.is_rx for m in messages],[True,True,False,True])
            self.assertTrue(messages[-1].is_extended_id)
            self.assertAlmostEqual(messages[1].timestamp-messages[0].timestamp,.001,places=5)
            self.assertEqual([bytes(m.data) for m in messages],[e.data for e in events if e.echo_of_sequence is None])
            from core.blf_reader import load_blf,get_blf_channels
            self.assertEqual(get_blf_channels(path),[channel+1])
            self.assertEqual(len(load_blf(path,channel=channel+1)),4)

    def test_empty_repeat_sessions_and_refused_overwrite(self):
        service=self.recorder();service.start(self.path,'session');self.ready(service)
        self.assertTrue(self.finish(service).complete)
        with can.BLFReader(self.path) as reader: self.assertEqual(list(reader),[])
        original=self.path.read_bytes()
        service.start(self.path,'session');self.assertTrue(service.wait(3))
        self.assertFalse(service.snapshot.complete)
        self.assertEqual(self.path.read_bytes(),original)
        service.start(self.path.with_name('second.blf'),'session');self.ready(service)
        service.offer(raw());self.assertTrue(self.finish(service).complete)

    def test_rtr_and_rx_error_round_trip(self):
        service=self.recorder();service.start(self.path,'session');self.ready(service)
        service.offer(raw(1,is_remote_frame=True,data=b'',dlc=8))
        service.offer(raw(2,is_error_frame=True))
        self.assertTrue(self.finish(service).complete)
        with can.BLFReader(self.path) as reader: messages=list(reader)
        self.assertTrue(messages[0].is_remote_frame)
        self.assertEqual((messages[0].dlc,bytes(messages[0].data)),(8,b''))
        self.assertTrue(messages[1].is_error_frame)
        self.assertEqual(bytes(messages[1].data),b'\x01\x02')

    def test_echo_from_before_recording_is_retained(self):
        service=self.recorder();service.start(self.path,'session');self.ready(service)
        service.offer(raw(2,direction='TX',tx_origin='observed_echo',echo_of_sequence=1))
        result=self.finish(service)
        self.assertTrue(result.complete)
        self.assertEqual((result.written,result.echoes),(1,0))

    def test_frames_during_async_open_are_queued_not_lost(self):
        entered=Event();release=Event()
        def factory(*args,**kwargs):
            entered.set();release.wait(3)
            return can.BLFWriter(*args,**kwargs)
        service=self.recorder(writer_factory=factory)
        self.addCleanup(release.set)
        service.start(self.path,'session');self.assertTrue(entered.wait(2))
        service.offer(raw(1));service.offer(raw(2))
        self.assertEqual(service.snapshot.captured,2)
        release.set();self.ready(service)
        self.assertTrue(self.finish(service).complete)
        with can.BLFReader(self.path) as reader: self.assertEqual(len(list(reader)),2)

    def test_queue_overflow_is_incomplete_and_start_is_exclusive(self):
        entered=Event();release=Event()
        class SlowWriter:
            def __init__(self,*a,**k): self.stops=0
            def on_message_received(self,msg): entered.set();release.wait(3)
            def stop(self): self.stops+=1
        writer=SlowWriter()
        service=self.recorder(capacity=1,writer_factory=lambda *a,**k:writer)
        service.start(self.path,'session');self.ready(service)
        with self.assertRaises(RuntimeError): service.start(self.path,'session')
        service.offer(raw(1));self.assertTrue(entered.wait(2))
        service.offer(raw(2));service.offer(raw(3));release.set()
        self.assertTrue(service.wait(3));result=service.snapshot
        self.assertFalse(result.complete)
        self.assertEqual((result.captured,result.written,result.dropped),(3,2,1))
        self.assertEqual(writer.stops,1)

    def test_write_stop_invalid_timestamp_and_session_failures(self):
        for failure in ('write','stop','timestamp','session'):
            class Writer:
                stops=0
                def on_message_received(self,msg):
                    if failure=='write': raise OSError(28,'No space left on device')
                def stop(self):
                    self.stops+=1
                    if failure=='stop': raise OSError('Finalization failed')
            writer=Writer();service=self.recorder(writer_factory=lambda *a,**k:writer)
            path=self.path.with_name(f'{failure}.blf');service.start(path,'session');self.ready(service)
            event=raw()
            if failure=='timestamp': event=replace(event,wall_timestamp_s=None)
            if failure=='session': event=replace(event,session_id='other')
            service.offer(event);result=self.finish(service)
            self.assertFalse(result.complete,failure)
            self.assertTrue(result.error,failure)
            self.assertEqual(writer.stops,1)
