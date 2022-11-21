'''
TCP方式(同期通信)用可変長データ送受信プロトコル

同期通信で使用する通信処理。最初に固定長のデータ長パケット送信後に
可変長のペイロードパケットを送信する方式。

author  : Taiyou Komazawa
date    : 2022/11/21
'''

import struct
import pickle

payload_size = struct.calcsize('>L')


def send(conn, packets):
    serial_packets = pickle.dumps(packets, 0)
    data = struct.pack('>L', len(serial_packets)) + serial_packets
    result = conn.send(data)
    return result

def receive(conn, max_buffer_sz=1024):
    r_dict = {}

    packed_msg_sz = conn.recv(payload_size)

    if len(packed_msg_sz) >= 4:
        msg_sz = struct.unpack('>L', packed_msg_sz)[0]

        data = b''
        if msg_sz <= max_buffer_sz:
            data = conn.recv(msg_sz)
        else:
            buff_sz = msg_sz
            while buff_sz > max_buffer_sz:
                data += conn.recv(max_buffer_sz)
                buff_sz -= max_buffer_sz
            data += conn.recv(buff_sz)

        r_dict = pickle.loads(data[:msg_sz], fix_imports=True, encoding='bytes')

    return r_dict
