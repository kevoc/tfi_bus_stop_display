
"""
`telemetry`
====================================================

This file stores functions related to gathering information
to put into log files, to aid in debug later.

* Author: Kevin O'Connell

"""

import os
import gc
import machine
import platform

from .log_tools import open_logfile


def machine_id():
    """Return the machine id as a hex string."""
    return '-'.join([f'{b:02X}' for b in machine.unique_id()])


def _reset_cause():
    """Return a string representing the reset cause for the device."""

    cause = machine.reset_cause()
    if cause == machine.PWRON_RESET:
        return 'Power-On Reset'
    elif cause == machine.WDT_RESET:
        return 'Watchdog Timeout'


def get_telemetry():
    """Gather some telemetry about the system and its running state,
    and return it as a string."""

    libc, libc_ver = platform.libc_ver()

    free, alloc = gc.mem_free(), gc.mem_alloc()
    total = free + alloc

    # get filesystem related info
    #   f_bsize – file system block size
    #   f_frsize – fragment size
    #   f_blocks – size of fs in f_frsize units
    #   f_bfree – number of free blocks
    #   f_bavail – number of free blocks for unprivileged users
    #   f_files – number of inodes
    #   f_ffree – number of free inodes
    #   f_favail – number of free inodes for unprivileged users
    #   f_flag – mount flags
    #   f_namemax – maximum filename length
    f_bsize, f_frsize, f_blocks, f_bfree, f_bavail, f_files, \
    f_ffree, f_favail, f_flag, f_namemax = os.statvfs('/')

    # uname info
    #   sysname – the name of the underlying system
    #   nodename – the network name (can be the same as sysname)
    #   release – the version of the underlying system
    #   version – the MicroPython version and build date
    #   machine – an identifier for the underlying hardware (eg board, CPU)
    sysname, nodename, release, version, _machine = os.uname()

    response = f"""
        id: {machine_id()}
        
        platform: {platform.platform()}
        platform-compiler: {platform.python_compiler()}
        platform-libc: {libc}
        platform-libc-ver: {libc_ver}
        
        reset-cause: {_reset_cause()}
        
        memory-free: {free:,d} bytes ({free / total:.2%})
        memory-alloc: {alloc:,d} bytes ({alloc / total:.2%})
        
        fs-block-size: {f_bsize}
        fs-fragment-size: {f_frsize}
        fs-blocks-total: {f_blocks}
        fs-blocks-free: {f_bfree}
        fs-blocks-available: {f_bavail}
        
        uname-machine: {_machine}
        uname-system: {sysname}
        uname-node: {nodename}
        uname-release: {release}
        uname-version: {version}
    """

    return response


def record_telemetry(rotate=True):
    """Write telemetry to a file."""

    with open_logfile('telemetry.txt', 'w', rotate=rotate) as f:
        f.write(get_telemetry())
