import sys
from logging import getLogger, Formatter, StreamHandler, DEBUG, WARNING
import argparse

class RQIFHeader:
    def init_variables(self):
        self.binary = None
        self.id = None
        self.filesize = None
        self.version = None
        self.dir = None
        self.generate_time = None
        self.offset = None
        self.blockfactor = None
        self.chunk_count = None

    def __init__(self):
        self.init_variables()

    def parse(self, binary):
        self.binary = binary
        self.read_RQIF_header()

    def read_RQIF_header(self):
        self.id = self.binary[0:4]
        if id == b'RQIF':
            raise RuntimeError("This file is not RQIF file.")
        self.filesize = int.from_bytes(self.binary[4:8], 'big')
        self.version = int.from_bytes(self.binary[8:10], 'big')
        self.dir = int.from_bytes(self.binary[10:12], 'big')
        self.file = int.from_bytes(self.binary[12:16], 'big')
        self.generate_time = int.from_bytes(self.binary[16:20], 'big')
        self.offset = int.from_bytes(self.binary[20:24], 'big')
        self.blockfactor = int.from_bytes(self.binary[24:26], 'big')
        self.chunk_count = int.from_bytes(self.binary[26:28], 'big')
    
    def apply(self):
        self.binary = bytearray()
        self.binary.extend(self.id)
        self.binary.extend(self.filesize.to_bytes(4, 'big'))
        self.binary.extend(self.version.to_bytes(2, 'big'))
        self.binary.extend(self.dir.to_bytes(2, 'big'))
        self.binary.extend(self.file.to_bytes(4, 'big'))
        self.binary.extend(self.generate_time.to_bytes(4, 'big'))
        self.binary.extend(self.offset.to_bytes(4, 'big'))
        self.binary.extend(self.blockfactor.to_bytes(2, 'big'))
        self.binary.extend(self.chunk_count.to_bytes(2, 'big'))
        self.binary.extend(b'\0\0\0\0')

class RQIFChunkHeader:
    def init_variables(self):
        self.binary = None
        self.id = None
        self.offset = None
        self.size = None

    def __init__(self):
        self.init_variables()
    
    def parse(self, binary):
        self.binary = binary
        self.read_chunk_header()
    
    def read_chunk_header(self):
        self.id = self.binary[0:4]
        self.offset = int.from_bytes(self.binary[4:8], 'big')
        self.size = int.from_bytes(self.binary[8:12], 'big')

    def apply(self):
        self.binary = bytearray()
        self.binary.extend(self.id)
        self.binary.extend(self.offset.to_bytes(4, 'big'))
        self.binary.extend(self.size.to_bytes(4, 'big'))

class RQIFChunk:
    def init_variables(self):
        self.binary = None
        self.id = None
        self.size = None
        self.data = None
    
    def __init__(self):
        self.init_variables()
    
    def parse(self, binary):
        self.binary = binary
        self.read_RQIF_chunk()

    def read_RQIF_chunk(self):
        self.id = self.binary[0:4]
        self.size = int.from_bytes(self.binary[4:8], 'big')
        self.data = self.binary[8:]

    def apply(self):
        self.binary = bytearray()
        self.binary.extend(self.id)
        self.binary.extend(self.size.to_bytes(4, 'big'))
        self.binary.extend(self.data)

class RQIFHandler:
    def init_variables(self):
        self.offset = 0
        self.chunk_headers = []
        self.chunks = []
        self.RQIF_HEADER_SIZE = 0x20
        self.RQIF_CHUNK_HEADER_SIZE = 0xC

    def __init__(self):
        self.init_variables()
        self.header = RQIFHeader()

    def parse(self, binary):
        self.binary = binary
        self.read_RQIF()

    def read_RQIF(self):
        self.check_SPRC_exist()
        seek = self.offset
        # ヘッダの読み込み
        self.header = RQIFHeader()
        self.header.parse(self.binary[0+seek:self.RQIF_HEADER_SIZE+seek])
        seek += self.RQIF_HEADER_SIZE
        # チャンクヘッダの読み込み
        for i in range(0, self.header.chunk_count):
            chunk_header = RQIFChunkHeader()
            chunk_header.parse(self.binary[seek:self.RQIF_CHUNK_HEADER_SIZE+seek])
            self.chunk_headers.append(chunk_header)
            seek += self.RQIF_CHUNK_HEADER_SIZE
        # チャンクの読み込み
        for i in range(0, self.header.chunk_count):
            chunk = RQIFChunk()
            chunk.parse(self.binary[seek:self.chunk_headers[i].size+seek])
            self.chunks.append(chunk)
            seek += self.chunk_headers[i].size

    def check_SPRC_exist(self):
        if self.binary[0:4] == b'SPRC':
            self.offset = 0x10
    
    def BGEV_append(self):
        for chunk_header in self.chunk_headers:
            if b'BGEV' == chunk_header.id:
                raise RuntimeError("This song already has BGEV.")
        # チャンクヘッダの作成
        BGEV_chunk_header = RQIFChunkHeader()
        BGEV_chunk_header.id = b'BGEV'
        BGEV_chunk_header.size = 0x4a
        self.chunk_headers.append(BGEV_chunk_header)
        # BGEVチャンクの作成
        BGEV_chunk = RQIFChunk()
        BGEV_chunk.id = b'BGEV'
        BGEV_chunk.size = 0x4a
        # BGEV.SBGVチャンクの作成
        SBGV_chunk = RQIFChunk()
        SBGV_chunk.id = b'SBGV'
        SBGV_chunk.size = 0x42
        # BGEV.SBGVデータの作成
        SBGV_chunk.data = bytearray()
        SBGV_chunk.data.extend(self.header.file.to_bytes(4, 'big'))
        SBGV_chunk.data.extend(bytearray.fromhex('00 00 00 00 00 01 00 07 00 00 00 00 00 22 00 01 00 00 00 00 00 00 00 00'))
        SBGV_chunk.data.extend((1020).to_bytes(2, 'big'))
        SBGV_chunk.data.extend(self.header.file.to_bytes(4, 'big'))
        SBGV_chunk.data.extend(bytearray.fromhex('00 00 00 00 FF FF FF FF 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00'))
        SBGV_chunk.apply()
        # BGEVにBGEV.SBGVを書き込み
        BGEV_chunk.data = SBGV_chunk.binary
        # チャンクを追加
        self.chunks.append(BGEV_chunk)
        self.header.chunk_count = self.header.chunk_count + 1
        self.apply()
    
    def apply(self):
        seek = 0
        seek += self.RQIF_HEADER_SIZE
        seek += self.RQIF_CHUNK_HEADER_SIZE * len(self.chunks)
        self.header.offset = seek
        for i in range(0, self.header.chunk_count):
            self.chunk_headers[i].offset = seek
            seek += self.chunk_headers[i].size
        self.header.filesize = seek
        # binaryに書き込み
        self.binary = bytearray()
        self.header.apply()
        self.binary.extend(self.header.binary)
        for chunk_header in self.chunk_headers:
            chunk_header.apply()
            self.binary.extend(chunk_header.binary)
        for chunk in self.chunks:
            chunk.apply()
            self.binary.extend(chunk.binary)

def main():
    parser = argparse.ArgumentParser(description="Adds BGEV to RQIF file without BGEV.")
    parser.add_argument("input", help="Path to input file.")
    parser.add_argument("output", help="Path to output file.")
    args = parser.parse_args()
    # 元ファイルを読み込み
    fr = open(args.input, 'rb')
    before = fr.read()
    # ハンドラー
    handler = RQIFHandler()
    handler.parse(before)
    handler.BGEV_append()
    fw = open(args.output, 'wb')
    fw.write(handler.binary)

if __name__ == '__main__':
    main()