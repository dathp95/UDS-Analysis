"""Windows process-tree lifetime, independent of any OEM DLL ABI.

Start suspended, attach to a non-breakaway job, then resume the owned main thread.
Source: https://learn.microsoft.com/en-us/windows/win32/procthread/job-objects
"""
import ctypes
from ctypes import wintypes as W


class _BasicLimits(ctypes.Structure):
    _fields_ = [('process_time',ctypes.c_int64),('job_time',ctypes.c_int64),('flags',W.DWORD),
                ('min_working',ctypes.c_size_t),('max_working',ctypes.c_size_t),
                ('active_processes',W.DWORD),('affinity',ctypes.c_size_t),
                ('priority',W.DWORD),('scheduling',W.DWORD)]


class _ExtendedLimits(ctypes.Structure):
    _fields_ = [('basic',_BasicLimits),('io_counters',ctypes.c_uint64*6),
                ('process_memory',ctypes.c_size_t),('job_memory',ctypes.c_size_t),
                ('peak_process',ctypes.c_size_t),('peak_job',ctypes.c_size_t)]


class _ThreadEntry(ctypes.Structure):
    _fields_ = [('size',W.DWORD),('usage',W.DWORD),('thread_id',W.DWORD),('process_id',W.DWORD),
                ('base_priority',W.LONG),('delta_priority',W.LONG),('flags',W.DWORD)]


class WindowsWorkerJob:
    def __init__(self):
        kernel = ctypes.WinDLL('kernel32',use_last_error=True)
        signatures = {
            'CreateJobObjectW': ([W.LPVOID,W.LPCWSTR],W.HANDLE),
            'SetInformationJobObject': ([W.HANDLE,ctypes.c_int,W.LPVOID,W.DWORD],W.BOOL),
            'AssignProcessToJobObject': ([W.HANDLE,W.HANDLE],W.BOOL),
            'OpenProcess': ([W.DWORD,W.BOOL,W.DWORD],W.HANDLE),
            'CloseHandle': ([W.HANDLE],W.BOOL),
            'CreateToolhelp32Snapshot': ([W.DWORD,W.DWORD],W.HANDLE),
            'Thread32First': ([W.HANDLE,ctypes.POINTER(_ThreadEntry)],W.BOOL),
            'Thread32Next': ([W.HANDLE,ctypes.POINTER(_ThreadEntry)],W.BOOL),
            'OpenThread': ([W.DWORD,W.BOOL,W.DWORD],W.HANDLE),
            'ResumeThread': ([W.HANDLE],W.DWORD),
        }
        for name,(args,result) in signatures.items():
            function=getattr(kernel,name)
            function.argtypes,function.restype=args,result
        self._kernel=kernel
        self._handle=kernel.CreateJobObjectW(None,None)
        if not self._handle:
            raise OSError('Cannot create worker job.')
        limits=_ExtendedLimits()
        limits.basic.flags=0x2000  # JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE, no breakaway.
        if not kernel.SetInformationJobObject(self._handle,9,ctypes.byref(limits),ctypes.sizeof(limits)):
            self.close()
            raise OSError('Cannot bound worker process tree.')

    def attach_and_resume(self,pid):
        kernel=self._kernel
        process=kernel.OpenProcess(0x0100|0x0001,False,pid)  # SET_QUOTA | TERMINATE
        if not process:
            raise OSError('Cannot attach worker process.')
        try:
            if not kernel.AssignProcessToJobObject(self._handle,process):
                raise OSError('Cannot isolate worker process tree.')
        finally:
            kernel.CloseHandle(process)
        # Popen closes its primary thread handle. Enumerate only to resume our
        # still-suspended process, before it can execute code or spawn children.
        snapshot=kernel.CreateToolhelp32Snapshot(4,0)  # TH32CS_SNAPTHREAD
        if snapshot == ctypes.c_void_p(-1).value:
            raise OSError('Cannot enumerate worker thread.')
        try:
            entry=_ThreadEntry()
            entry.size=ctypes.sizeof(entry)
            found=kernel.Thread32First(snapshot,ctypes.byref(entry))
            while found:
                if entry.process_id == pid:
                    thread=kernel.OpenThread(0x0002,False,entry.thread_id)  # SUSPEND_RESUME
                    if not thread:
                        raise OSError('Cannot resume worker thread.')
                    try:
                        if kernel.ResumeThread(thread) == 0xFFFFFFFF:
                            raise OSError('Cannot resume worker thread.')
                        return
                    finally:
                        kernel.CloseHandle(thread)
                found=kernel.Thread32Next(snapshot,ctypes.byref(entry))
            raise OSError('Worker main thread not found.')
        finally:
            kernel.CloseHandle(snapshot)

    def close(self):
        if self._handle:
            handle,self._handle=self._handle,None
            if not self._kernel.CloseHandle(handle):
                raise OSError('Cannot finalize worker process tree.')
