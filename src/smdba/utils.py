# coding: utf-8
"""
General utils
"""

import os
import sys
import grp
import pwd
import typing


class TablePrint:
    """
    Print table on the CLI.
    """

    def __init__(self, table: typing.List[typing.List[str]]) -> None:
        """
        Table is [(1,2,3,), (4,5,6,),] etc data.
        """
        self.table = table
        self.widths: typing.List[int] = []

    def _check(self) -> None:
        """
        Check if table is consistent grid.
        Header is a leader here.
        """
        if not self.table:
            raise Exception("Table is empty!")

        header = None
        for row in self.table:
            if header is None:
                header = len(row)
                continue
            if len(row) != header:
                raise Exception("Table has different row widths.")

    def _get_widths(self) -> None:
        """
        Find extra-widths by max width of any value.
        """

        self.widths = [0 for _ in self.table[0]]
        for row in self.table:
            for idx, cell in enumerate(row):
                cell_len = len(str(cell))
                if cell_len > self.widths[idx]:
                    self.widths[idx] = cell_len

    def _format(self) -> str:
        """
        Format the output.
        """
        out = []
        ftable = []
        for row in self.table:
            frow = []
            for idx, cell in enumerate(row):
                frow.append(str(cell) + (" " * (self.widths[idx] - len(str(cell)))))
            ftable.append(frow)

        for idx, row in enumerate(ftable):
            out.append(' | '.join(row))
            if not idx:
                out.append('-+-'.join(["-" * len(item) for item in row]))

        return '\n'.join(out)

    def __str__(self) -> str:
        self._check()
        self._get_widths()
        return self._format()


def create_dirs(path: str, owner: str, mode: int = 0o700) -> bool:
    """
    Create path and change owner of it accordingly.
    Default mode is 0700
    """
    if not os.path.exists(path):
        os.makedirs(path, mode=mode)
        _owner = pwd.getpwnam(owner)
        os.chown(path, _owner.pw_uid, _owner.pw_gid)
        ret = True
    else:
        ret = False

    return ret


class Owner:
    """
    Owner object.
    """
    def __init__(self) -> None:
        self.uid: int = -1
        self.gid: int = -1
        self.user: typing.Optional[str] = None
        self.group: typing.Optional[str] = None


def get_path_owner(path: str) -> Owner:
    """
    Returns the owner and group IDs of a directory.
    """
    owner = Owner()
    stat_info = os.stat(path)
    owner.uid = stat_info.st_uid
    owner.gid = stat_info.st_gid
    owner.user = pwd.getpwuid(owner.uid)[0]
    owner.group = grp.getgrgid(owner.gid)[0]

    return owner


def eprint(*args: typing.Any, **kwargs: typing.Any) -> None:
    """
    Print to the STDERR.

    :param args: print arguments
    :param kwargs: keywords
    :return: None
    """
    print(*args, file=sys.stderr, **kwargs)
