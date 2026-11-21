#!/usr/bin/env python3
"""Socket filter to run inside the sealed compiler runtime.

Wine may use Unix sockets for its private wineserver. The runtime must
hide other Unix services and make the dedicated compiler mounts independently.
"""
import ctypes
import errno
import os
import platform
import socket
import sys

BPF_LD_W_ABS = 0x20
BPF_JMP_JEQ_K = 0x15
BPF_JMP_JSET_K = 0x45
BPF_RET_K = 0x06
AUDIT_X86_64 = 0xC000003E
AUDIT_I386 = 0x40000003
X32_BIT = 0x40000000
ALLOW = 0x7FFF0000
DENY = 0x00050000 | errno.EPERM
KILL = 0x80000000
NO_NEW_PRIVS = 38
SET_SECCOMP = 22
FILTER_MODE = 2


class Instruction(ctypes.Structure):
    _fields_ = [("code", ctypes.c_ushort), ("jt", ctypes.c_ubyte), ("jf", ctypes.c_ubyte),
                ("k", ctypes.c_uint32)]


class Program(ctypes.Structure):
    _fields_ = [("len", ctypes.c_ushort), ("filter", ctypes.POINTER(Instruction))]


def load(offset):
    return Instruction(BPF_LD_W_ABS, 0, 0, offset)


def eq(value, yes, no):
    return Instruction(BPF_JMP_JEQ_K, yes, no, value)


def ret(decision):
    return Instruction(BPF_RET_K, 0, 0, decision)


def socket_rules(socket_calls, blocked, *, x32=False):
    output = [load(0)]
    if x32:
        output += [Instruction(BPF_JMP_JSET_K, 0, 1, X32_BIT), ret(DENY)]
    for number in blocked:
        output.extend((eq(number, 0, 1), ret(DENY)))
    for number in socket_calls:
        output.extend((eq(number, 0, 4), load(16), eq(socket.AF_UNIX, 0, 1), ret(ALLOW), ret(DENY)))
    output.append(ret(ALLOW))
    return output


def filter_network():
    if sys.platform != "linux" or platform.machine() != "x86_64":
        raise OSError(errno.ENOSYS, "The dedicated socket filter requires x86_64 Linux.")
    # Deny io_uring and foreign descriptor access as well as external socket creation.
    shared = (425, 426, 427, 438)
    x64 = socket_rules((41, 53), (101, 321, *shared), x32=True)
    x86 = socket_rules((359, 360), (26, 102, 357, *shared))
    instructions = [load(4), eq(AUDIT_X86_64, 2, 0), eq(AUDIT_I386, len(x64) + 1, 0), ret(KILL),
                    *x64, *x86]
    desc = (Instruction * len(instructions))(*instructions)
    rules = Program(len(desc), desc)
    c = ctypes.CDLL(None, use_errno=True)
    c.prctl.restype = ctypes.c_int
    if c.prctl(NO_NEW_PRIVS, 1, 0, 0, 0) or c.prctl(SET_SECCOMP, FILTER_MODE, ctypes.byref(rules), 0, 0):
        value = ctypes.get_errno()
        raise OSError(value, "The compiler socket filter did not install.")


if __name__ == "__main__":
    if len(sys.argv) < 2 or not os.path.isabs(sys.argv[1]):
        raise SystemExit("Usage: pool_network.py /absolute/installed/command ...")
    os.closerange(3, int(os.sysconf("SC_OPEN_MAX")))
    filter_network()
    os.execv(sys.argv[1], sys.argv[1:])

