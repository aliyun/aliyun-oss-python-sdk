import platform
import struct
import requests

from .compat import to_bytes
from .exceptions import RequestError
from .exceptions import SelectOperationFailed


"""
The adapter class for Select object's response.
The response consists of frames. Each frame has the following format:

Type  |   Payload Length |  Header Checksum | Payload | Payload Checksum

|<4-->|  <--4 bytes------><---4 bytes-------><-n/a-----><--4 bytes--------->
And we have three kind of frames.
Data Frame:
Type:8388609
Payload:   Offset    |    Data
           <-8 bytes>

Continuous Frame
Type:8388612
Payload: Offset  (8-bytes)

End Frame
Type:8388613
Payload: Offset | total scanned bytes | http status code | error message
    <-- 8bytes--><-----8 bytes--------><---4 bytes-------><---variabe--->

"""
class SelectResponseAdapter(object):

    _CHUNK_SIZE = 8 * 1024
    _CONTINIOUS_FRAME_TYPE=8388612
    _DATA_FRAME_TYPE = 8388609
    _END_FRAME_TYPE = 8388613
    _FRAMES_FOR_PROGRESS_UPDATE = 10

    def __init__(self, response, progress_callback = None, content_length = None):
       self.response = response
       self.frame_off_set = 0
       self.frame_length = 0
       self.frame_data = b''
       self.check_sum_flag = 0
       self.file_offset = 0
       self.finished = 0
       self.raw_buffer = b''
       self.raw_buffer_offset = 0
       self.resp_content_iter = response.__iter__()
       self.callback = progress_callback
       self.frames_since_last_progress_report = 0
       self.content_length = content_length

    def __iter__(self):
        return self

    def __next__(self):
        return self.next()
    
    def next(self):
        while self.finished == 0:
            if self.frame_off_set < self.frame_length:
                frame_data = self.read_raw(self.frame_length - self.frame_off_set)
                #print("Reading FrameData:" + str(len(frame_data)) + " buffer size" + str(self.frame_length - self.frame_off_set))
                self.frame_length = self.frame_off_set = 0
                return frame_data
            else:
                self.read_next_frame()
                self.frames_since_last_progress_report += 1
                if (self.frames_since_last_progress_report >= SelectResponseAdapter._FRAMES_FOR_PROGRESS_UPDATE and self.callback is not None):
                    self.callback(self.file_offset, self.content_length)
                    self.frames_since_last_progress_report = 0
        
        raise StopIteration

    def read_raw(self, amt):
        ret = b''
        read_count = 0
        while amt > 0 and self.finished == 0:
            size = len(self.raw_buffer)
            if size == 0:
                self.raw_buffer = next(self.resp_content_iter)
                self.raw_buffer_offset = 0
                size = len(self.raw_buffer)
                if size == 0:
                    break

            if size - self.raw_buffer_offset >= amt:
                data = self.raw_buffer[self.raw_buffer_offset:self.raw_buffer_offset + amt]
                data_size = len(data)
                self.raw_buffer_offset += data_size
                ret += data
                read_count += data_size
                amt -= data_size
            else:
                data = self.raw_buffer[self.raw_buffer_offset:]
                data_len = len(data)
                ret += data
                read_count += data_len
                amt -= data_len 
                self.raw_buffer = b''
        
        return ret

    def read_next_frame(self):
        if (self.check_sum_flag == 1):
            self.read_raw(4)

        frame_type = bytearray(self.read_raw(4))
        payload_length = bytearray(self.read_raw(4))
        header_checksum = bytearray(self.read_raw(4))
        frame_type[0] = 0 #mask the version bit
        frame_type.reverse() # convert to little endian
        frame_type_val = struct.unpack("I", bytearray(frame_type))[0]
        file_offset_bytes = bytearray(self.read_raw(8))
        file_offset_bytes.reverse()
        self.file_offset = struct.unpack("Q", bytearray(file_offset_bytes))[0]
        if frame_type_val == SelectResponseAdapter._DATA_FRAME_TYPE:
            payload_length.reverse() # convert to little endian
            payload_length_val = struct.unpack("I", bytearray(payload_length))[0]
            self.frame_length = payload_length_val - 8
            self.frame_off_set = 0
            self.check_sum_flag=1
            #print("Get Data Frame:" + str(self.frame_length))
        elif frame_type_val == SelectResponseAdapter._CONTINIOUS_FRAME_TYPE:
            self.frame_length = self.frame_off_set = 0
            self.check_sum_flag=1
            #print("GetContiniousFrame:" + str(self.frame_length))
        elif frame_type_val == SelectResponseAdapter._END_FRAME_TYPE:
            self.frame_off_set = 0
            payload_length.reverse()
            payload_length_val = struct.unpack("I", bytearray(payload_length))[0]
            scanned_size_bytes = bytearray(self.read_raw(8))
            status_bytes = bytearray(self.read_raw(4))
            status_bytes.reverse()
            status = struct.unpack("I", bytearray(status_bytes))[0]
            error_msg_size = payload_length_val - 20
            error_msg=b'';
            if error_msg_size > 0:
                error_msg = self.read_raw(error_msg_size)
            self.read_raw(4) # read the payload checksum
            if status >= 400:
                raise SelectOperationFailed(status, error_msg)
            self.frame_length = 0
            if self.callback is not None:
                self.callback(self.file_offset, self.content_length)
        else:
            raise SelectOperationFailed(400, "Unexpected frame type:" + str(frame_type_val))
