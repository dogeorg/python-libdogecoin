#!/usr/bin/python3
import os
import argparse
parser = argparse.ArgumentParser()
parser.add_argument("--host", help="provide target host triplet")
args = parser.parse_args()
if args.host:
    print(args.host)
    os.environ['host'] = args.host
    print(os.getenv('host'))
    