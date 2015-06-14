# -*- coding: utf-8 -*-
# ---------------------------------------------------------------------------
# Zdroj: https://mail.python.org/pipermail/python-list/2007-May/460639.html
#
# Description: Rozboci vystup stderr a stdout i do souboru (log)
# Upravil: f:D
#
# Volani: (pomoci r'.\py_tools\__init__.py')
#    import py_tools.Tee
#    out=py_tools.Tee.Tee2File(logfilename, 'w')
# Ukonceni:
#    out.close()
#    del out
# ---------------------------------------------------------------------------

import sys

class Tee2File(object):
    # 
     def __init__(self, name, mode):
         self.file = open(name, mode)
         self.stdout = sys.stdout
         sys.stdout = self
     def close(self):
         if self.stdout is not None:
             sys.stdout = self.stdout
             self.stdout = None
         if self.file is not None:
             self.file.close()
             self.file = None
     def write(self, data):
         self.file.write(data)
         self.stdout.write(data)
     def flush(self):
         self.file.flush()
         self.stdout.flush()
     def __del__(self):
         self.close()
