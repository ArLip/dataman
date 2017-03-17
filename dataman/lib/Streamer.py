#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Created on Sep 24, 2015 15:32
@author: <'Ronny Eichler'> ronny.eichler@gmail.com

Stream data to buffer
"""

import logging
import os
import signal
import time
import multiprocessing as mp
import logging

from .Buffer import Buffer
from dataman.lib.open_ephys import read_header, read_record
from dataman.lib.tools import fmt_time

logger = logging.getLogger('Streamer')

class Streamer(mp.Process):
    def __init__(self, queue, raw, update_interval=0.02):
        super(Streamer, self).__init__()

        ##### WARNING #####
        # On Windows, a logging.logger can't be added to the class
        # as loggers can't be pickled. There probably is a way around
        # using configuration dicts, but I'll stay away from that...
        # self.logger = logging.getLogger(__name__)
        # self.logger = mp.log_to_stderr()
        logger.info('{} process initializing'.format(self.name))

        # # Queue Interface
        self.commands = {'stop': self.stop,
                         'offset': self.reposition}
        self.queue = queue
        self.alive = True
        self.update_interval = update_interval

        # Shared Buffer
        self.raw = raw
        self.buffer = Buffer()

        # # Data specifics
        self.offset = None

    def run(self):
        """Main streaming loop."""
        # ignore CTRL+C, runs daemonic, will stop with parent
        signal.signal(signal.SIGINT, signal.SIG_IGN)
        logger.info('Running...')

        self.buffer.initialize_from_raw(self.raw)

        while self.alive:
            # Grab all messages currently in the queue
            # FIXME: Only move to last position update
            instructions = self.__get_instructions()
            commands = [instr[0] for instr in instructions]
            for instr in instructions:
                self.__execute_instruction(instr)
                if instr[0] == 'stop':
                    break
            logger.debug('Instructions: {}'.format(instructions))
            time.sleep(self.update_interval)

    def stop(self, _):
        logger.info('Received Stop Signal')
        self.alive = False

    def reposition(self, offset):
        pass

    def __get_instructions(self):
        cmdlets = []
        for msg in range(0, self.queue.qsize()):
            try:
                cmdlets.append(self.queue.get(False))
            except Exception as e:
                logger.error(e)
                break
        return cmdlets

    def __execute_instruction(self, instruction):
        if len(instruction)==2 and instruction[0] in self.commands:
            try:
                self.commands[instruction[0]](instruction[1])
            except BaseException as e:
                logger.warning('Unable to execute {} because: {}'.format(instruction, e))
        else:
            logger.warning('Ignoring {}'.format(instruction))

    def __add_command(self, command, func):
        self.commands[command] = func


#         channel_list = range(self.__buf.nChannels)
#         self.files = [(channel, os.path.join(self.target, '{}_CH{}.continuous'.format(proc_node, channel + 1)))
#                       for channel in channel_list]
#         self.target_header = read_header(self.files[0][1])

#     def run(self):
#         """Main streaming loop."""
#         cmd = self.__get_cmd()
#         self.logger.info("Started streaming")
#
#         # ignore CTRL+C, runs daemonic, will stop with parent
#         signal.signal(signal.SIGINT, signal.SIG_IGN)
#
#         while cmd != 'stop':
#             # Grab all messages currently in the queue
#             messages = self.__get_cmd()
#             pos_changes = [msg[1] for msg in messages if msg[0] == 'position' and msg[1] is not None]
#             last_pos = pos_changes[-1] if len(pos_changes) else self.position
#             cmd = 'stop' if 'stop' in [msg[0] for msg in messages if msg[0] != 'position'] else None
#
#             if last_pos is not None and self.position != last_pos:
#                 self.position = last_pos
#
#                 # READ IN DATA
#                 # TODO: Here be worker pool of threads/processes grabbing data into the shared buffer
#                 # TODO: Avoid extra copy of data by having Buffer return view on array and write in place
#                 t = time.time()
#                 for sf in self.files:
#                     data = read_record(sf[1], offset=self.position)[:self.__buf.nSamples]
#                     self.__buf.put_data(data, channel=sf[0])
#                 self.logger.debug('Read {} channel data at position {} in {:.0f} ms'.
#                                   format(self.__buf.nChannels,
#                                          fmt_time(self.position * 1024 / self.target_header['sampleRate']),
#                                          (time.time() - t) * 1000))

#

if __name__ == "__main__":
    pass