"""Bounded, static PE inspection. Never loads a library or resolves a callable ABI."""
from dataclasses import dataclass,field
from enum import Enum
from pathlib import Path,PureWindowsPath
import os
import platform
import struct

from config.paths import PROJECT_ROOT

MAX_DLL_BYTES=16*1024*1024
MAX_EXPORTS=512
MAX_EXPORT_NAME=512


class DllResourceStatus(Enum):
    NOT_CONFIGURED='not_configured'
    MISSING='missing'
    INVALID_PATH='invalid_path'
    INVALID_FILE='invalid_file'
    MALFORMED='malformed'
    ARCH_UNSUPPORTED='architecture_unsupported'
    METADATA_AVAILABLE='metadata_available'
    CONFIGURATION_ERROR='configuration_error'
    INSPECTION_UNAVAILABLE='inspection_unavailable'


@dataclass(frozen=True)
class DllResourceMetadata:
    status: DllResourceStatus
    message: str
    path: str=field(default='',repr=False)
    machine: str=''
    bits: int|None=None
    exports: tuple[str,...]=()

    @property
    def configurable(self):
        return self.status in (DllResourceStatus.METADATA_AVAILABLE,DllResourceStatus.ARCH_UNSUPPORTED)

    @property
    def has_generate_key_ex(self): return 'GenerateKeyEx' in self.exports

    @property
    def filename(self): return Path(self.path).name if self.path else ''


def inspect_dll_resource(value,*,base_dir=PROJECT_ROOT,process_bits=None) -> DllResourceMetadata:
    """Inspect a local PE file; relative paths resolve from the application root.

    METADATA_AVAILABLE means parseable headers/exports for the process architecture,
    not a verified ABI, signature, or permission to execute the library.
    """
    Status=DllResourceStatus
    if value in ('',None): return DllResourceMetadata(Status.NOT_CONFIGURED,'DLL not configured.')
    if not isinstance(value,str): return DllResourceMetadata(Status.INVALID_PATH,'Invalid DLL path.')
    raw=value.strip()
    if len(raw)>=2 and raw[0]==raw[-1]=='"': raw=raw[1:-1]
    if not raw: return DllResourceMetadata(Status.NOT_CONFIGURED,'DLL not configured.')
    if (any(ord(char)<32 for char in raw) or raw.startswith('\\\\') or '://' in raw
            or PureWindowsPath(raw).is_reserved()):
        return DllResourceMetadata(Status.INVALID_PATH,'Use a local file path; control characters, network/device paths and URIs are unsupported.')
    path=Path(raw)
    if path.drive and not path.is_absolute():
        return DllResourceMetadata(Status.INVALID_PATH,'Drive-relative DLL paths are unsupported.')
    try:
        path=path.expanduser()
        path=(path if path.is_absolute() else Path(base_dir)/path).resolve()
        if path.suffix.lower()!='.dll':
            return DllResourceMetadata(Status.INVALID_FILE,'Select a .dll file.',str(path))
        if not path.exists(): return DllResourceMetadata(Status.MISSING,'DLL missing or moved.',str(path))
        if not path.is_file(): return DllResourceMetadata(Status.INVALID_FILE,'DLL path must identify a regular file.',str(path))
        with path.open('rb') as handle:
            size=os.fstat(handle.fileno()).st_size
            if not 64<=size<=MAX_DLL_BYTES:
                return DllResourceMetadata(Status.MALFORMED,'DLL is truncated or exceeds the 16 MiB static inspection limit.',str(path))
            data=handle.read(MAX_DLL_BYTES+1)
        if len(data)!=size: return DllResourceMetadata(Status.MALFORMED,'DLL changed during static inspection.',str(path))
    except (OSError,ValueError,RuntimeError):
        return DllResourceMetadata(Status.INVALID_FILE,'DLL cannot be read.',str(path))
    try:
        import pefile
    except ImportError:
        return DllResourceMetadata(Status.INSPECTION_UNAVAILABLE,'Static PE parser unavailable; install project requirements.',str(path))
    try:
        with pefile.PE(data=data,fast_load=True,max_symbol_exports=MAX_EXPORTS) as pe:
            if not pe.FILE_HEADER.Characteristics&0x2000 or not 0<pe.FILE_HEADER.NumberOfSections<=96:
                raise ValueError('Not a supported DLL image.')
            magic=pe.OPTIONAL_HEADER.Magic
            bits={0x10B:32,0x20B:64}.get(magic)
            if bits is None: raise ValueError('Unsupported PE header.')
            machine=pe.FILE_HEADER.Machine
            if machine in (0x14C,0x8664,0xAA64) and bits != (32 if machine==0x14C else 64):
                raise ValueError('Inconsistent PE architecture.')
            directory=pe.OPTIONAL_HEADER.DATA_DIRECTORY[0]
            if directory.VirtualAddress or directory.Size:
                if not directory.VirtualAddress or directory.Size<40: raise ValueError('Invalid exports.')
                header=pe.get_data(directory.VirtualAddress,40)
                functions,names,func_table,name_table,ordinal_table=struct.unpack_from('<IIIII',header,20)
                if max(functions,names)>MAX_EXPORTS: raise ValueError('Export inspection budget exceeded.')
                for index in range(names):
                    ordinal=struct.unpack('<H',pe.get_data(ordinal_table+2*index,2))[0]
                    if ordinal>=functions: raise ValueError('Invalid export ordinal.')
                    rva=struct.unpack('<I',pe.get_data(name_table+4*index,4))[0]
                    if b'\0' not in pe.get_data(rva,MAX_EXPORT_NAME+1): raise ValueError('Invalid export name.')
                for index in range(functions):
                    rva=struct.unpack('<I',pe.get_data(func_table+4*index,4))[0]
                    if directory.VirtualAddress<=rva<directory.VirtualAddress+directory.Size:
                        if b'\0' not in pe.get_data(rva,MAX_EXPORT_NAME+1): raise ValueError('Invalid forwarder.')
                pe.parse_data_directories(directories=[pefile.DIRECTORY_ENTRY['IMAGE_DIRECTORY_ENTRY_EXPORT']])
                if not hasattr(pe,'DIRECTORY_ENTRY_EXPORT'): raise ValueError('Malformed export directory.')
                symbols=pe.DIRECTORY_ENTRY_EXPORT.symbols
                if len(symbols)>MAX_EXPORTS: raise ValueError('Export inspection budget exceeded.')
                exports=tuple(sorted({symbol.name.decode('ascii') for symbol in symbols if symbol.name}))
                if any(len(name)>MAX_EXPORT_NAME or any(ord(char)<32 or ord(char)>126 for char in name) for name in exports):
                    raise ValueError('Invalid export name.')
            else: exports=()
        native_bits=process_bits or struct.calcsize('P')*8
        expected=0x14C if native_bits==32 else 0xAA64 if platform.machine().lower() in ('arm64','aarch64') else 0x8664
        machine_name={0x14C:'x86',0x8664:'x64',0xAA64:'ARM64'}.get(machine,f'PE machine 0x{machine:04X}')
        compatible=machine==expected
        message=('DLL configured; static metadata available.' if compatible else
                 'DLL incompatible (x86 requires 32-bit helper).' if machine==0x14C and native_bits==64 else
                 'DLL architecture unsupported in this process.')
        message+=' GenerateKeyEx listed; ABI unverified.' if 'GenerateKeyEx' in exports else ' GenerateKeyEx not exported.'
        return DllResourceMetadata(Status.METADATA_AVAILABLE if compatible else Status.ARCH_UNSUPPORTED,
            message+' Security execution disabled.',str(path),machine_name,bits,exports)
    except (pefile.PEFormatError,ValueError,struct.error,IndexError,OverflowError,UnicodeError,AttributeError,TypeError):
        return DllResourceMetadata(Status.MALFORMED,'DLL has malformed or unsupported PE/export metadata.',str(path))
