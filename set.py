#!/usr/bin/python3
import os
import argparse
import subprocess
parser = argparse.ArgumentParser()
parser.add_argument("--host", help="provide target host triplet")
args = parser.parse_args()
if args.host:
    print(args.host)
    os.environ['host'] = args.host
    subprocess.Popen('export host="'+ args.host + '"', shell=True).wait()
    print(os.environ.get('host'))
    