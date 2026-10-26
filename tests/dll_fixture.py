"""Synthetic PE data for static parsing only; contains no executable routine."""
import struct


def pe_dll(machine=0x8664, export=b'GenerateKeyEx'):
    data=bytearray(0x600)
    data[:2]=b'MZ';struct.pack_into('<I',data,0x3C,0x80)
    data[0x80:0x84]=b'PE\0\0'
    bits=32 if machine==0x14C else 64
    optional_size=0xE0 if bits==32 else 0xF0
    struct.pack_into('<HHIIIHH',data,0x84,machine,1,0,0,0,optional_size,0x2002)
    opt=0x98
    struct.pack_into('<H',data,opt,0x10B if bits==32 else 0x20B)
    struct.pack_into('<II',data,opt+32,0x1000,0x200)
    struct.pack_into('<II',data,opt+56,0x2000,0x200)
    directory=opt+(96 if bits==32 else 112)
    struct.pack_into('<I',data,directory-4,16)
    struct.pack_into('<II',data,directory,0x1000,0x100)
    section=opt+optional_size
    data[section:section+8]=b'.edata\0\0'
    struct.pack_into('<IIII',data,section+8,0x400,0x1000,0x400,0x200)
    struct.pack_into('<I',data,section+36,0x40000040)
    struct.pack_into('<IIHHIIIIIII',data,0x200,0,0,0,0,0x1050,1,1,1,0x1060,0x1064,0x1068)
    data[0x250:0x259]=b'fake.dll\0'
    struct.pack_into('<IIH',data,0x260,0x1100,0x1080,0)
    data[0x280:0x281+len(export)]=export+b'\0'
    return bytes(data)
