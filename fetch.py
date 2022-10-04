#!/usr/bin/python3
import os
import requests, zipfile
from io import BytesIO
import hashlib
import subprocess
import tarfile
import glob
import shutil
import argparse
parser = argparse.ArgumentParser()
parser.add_argument("--host", help="provide target host triplet")
args = parser.parse_args()
host = ""
if args.host:
    host = args.host
    os.environ['host'] = host
elif os.environ['host']:
    host = os.environ['host']

assert host in ("arm-linux-gnueabihf",
                "aarch64-linux-gnu",
                "x86_64-pc-linux-gnu",
                "x86_64-apple-darwin14",
                "x86_64-w64-mingw32",
                "i686-w64-mingw32",
                "i686-pc-linux-gnu",), "Invalid architecture."

hash = ""
if host == "arm-linux-gnueabihf":
    ext = ".tar.gz"
    hash = "a7e5d970730747f75f81fc2d5e3d78b418eb45bf703a576761ce1b66491c5adb  libdogecoin-0.1.0-arm-linux-gnueabihf.tar.gz"
elif host == "aarch64-linux-gnu":
    ext = ".tar.gz"
    hash = "990f859a8ffd77375e3be75bc343a0696cb9dc8c76f96bf95c20a05130232bf2  libdogecoin-0.1.0-aarch64-linux-gnu.tar.gz"
elif host == "x86_64-w64-mingw32":
    ext = ".zip"
    hash = "c5734c42cedd8ae3a98a075ff0b3d124851a6decc3c1d9c1782dfc5cdec0da87  libdogecoin-0.1.0-x86_64-w64-mingw32.zip"
elif host == "i686-w64-mingw32":
    ext = ".zip"
    hash = "d666d35a3664a3ba347a8e547f36a5039645af722542fad5fb7f0a0e45c6cd38  libdogecoin-0.1.0-i686-w64-mingw32.zip"
elif host == "x86_64-apple-darwin14":
    ext = ".tar.gz"
    hash = "cf0aa8abce318378e031250560a64032e94c15c921e14ec6f0451cc5a67a5d7d  libdogecoin-0.1.0-x86_64-apple-darwin14.tar.gz"
elif host == "x86_64-pc-linux-gnu":
    ext = ".tar.gz"
    hash = "908c5dfc9e4b617aae0df9c8cd6986b5988a6b5086136df5cbac40ec63e0c31c  libdogecoin-0.1.0-x86_64-pc-linux-gnu.tar.gz"
elif host == "i686-pc-linux-gnu":
    ext = ".tar.gz"
    hash = "d70a438a3bc7d74e8baa99a00b70e33a806db19b673fb36617307603186208a4  libdogecoin-0.1.0-i686-pc-linux-gnu.tar.gz"

print('Downloading started')
file = "libdogecoin-0.1.0-" + host
base = "https://github.com/dogecoinfoundation/libdogecoin/releases/download/v0.1.0/"
url = base + file + ext
sha256sums = base + "SHA256SUMS.asc"

req_sha = requests.get(sha256sums)
checksum = sha256sums.split('/')[-1]
with open(checksum,'wb') as output_checksum:
    output_checksum.write(req_sha.content)
print("\033[1;32m> Downloading SHA256SUMS.asc Completed\033[0m")

req = requests.get(url)
filename = url.split('/')[-1]
with open(filename,'wb') as output_file:
    output_file.write(req.content)
print("\033[1;32m> Downloading " + filename + " Completed\033[0m")

sha256_hash = hashlib.sha256()
with open(filename,"rb") as f:
    for byte_block in iter(lambda: f.read(4096),b""):
        sha256_hash.update(byte_block)

with open("SHA256SUMS.asc", "r") as get_hash:
    for line in get_hash.readlines():
        if filename and hash in line:
            if line.strip() == hash:
                if sha256_hash.hexdigest() != line.split()[0]:
                    print("\033[31m> checksums don't match!\033[0m")
                    exit(1)
                else:
                    print("\033[1;32m> checksums match!\033[0m")
            else:
                print("\033[31m> no valid checksum found!\033[0m")
                exit(1)

if ext == ".zip":
    zipfile= zipfile.ZipFile(BytesIO(req.content))
    zipfile.extractall(os.getcwd())
else:
    with tarfile.open(fileobj=BytesIO(req.content), mode='r:gz') as tar:
        tar.extractall(os.getcwd())
        tar.close()

os.makedirs(os.path.join(os.getcwd(), "lib"), exist_ok = True)
os.makedirs(os.path.join(os.getcwd(), "include"), exist_ok = True)

deps_path = ["lib/libdogecoin.a", "include/libdogecoin.h"]
for f in deps_path:
    src = file + "/" + f
    if os.path.isfile(src):
        os.replace(src, f)

rmlist = ['./libdogecoin-*', './__pycache__', '*.egg-info', '*.tar.gz', '*.zip', '*.c']
for path in rmlist:
    for name in glob.glob(path):
        if os.path.isdir(name):
            try:
                shutil.rmtree(name)
            except OSError as e:
                print("Error: %s : %s" % (name, e.strerror))
        if os.path.isfile(name):
            try:
                os.remove(name)
            except OSError as e:
                print("Error: %s : %s" % (name, e.strerror))

