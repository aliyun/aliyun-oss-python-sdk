#!/usr/bin/python

import os
import hyper
import h2

def fix_hyper():
    if hyper.__version__ == "0.7.0":
        hyper_dir = os.path.dirname(hyper.__file__)
        fix_file_path = hyper_dir + "/common/headers.py"
    
        f_read = open(fix_file_path,'r+')
        flist = f_read.readlines()
        if flist[244] == """    SPECIAL_SNOWFLAKES = set([b'set-cookie', b'set-cookie2'])\n""":
            flist[244] = """    SPECIAL_SNOWFLAKES = set([b'set-cookie', b'set-cookie2', b'date', b'if-modified-since', b'if-unmodified-since', b'authorization'])\n"""
    
            print " ====================================================================================="
            print " # OSS already patch to fix hyper library "
            print " # fixed file name: ", fix_file_path
            print " # fixed line number: 244"
            print " # More detail to see: https://github.com/Lukasa/hyper/issues/314 "
            print " ====================================================================================="
        f_read.close()
    
        f_wte = open(fix_file_path, 'w+')
        f_wte.writelines(flist)
        f_wte.close()

def fix_h2():
    if h2.__version__ == "2.6.2":
        h2_dir = os.path.dirname(h2.__file__)
        fix_file_path = h2_dir + "/stream.py"
    
        f_read = open(fix_file_path, 'r+')
        flist = f_read.readlines()
        if flist[337] == """        raise StreamClosedError(self.stream_id)\n""":
            flist[337] = """        #raise StreamClosedError(self.stream_id)\n        return []\n"""
            print " ====================================================================================="
            print " # OSS already patch to fix h2 library "
            print " # fixed file name: ", fix_file_path
            print " # fixed line number: 337"
            print " ====================================================================================="
        f_read.close()
    
        f_wte = open(fix_file_path, 'w+')
        f_wte.writelines(flist)
        f_wte.close()

def main():
    fix_hyper()
    fix_h2()


if __name__ == "__main__":
    main()
