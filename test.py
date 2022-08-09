#!/usr/bin/python3
import os
import subprocess
import glob

target_wheel = ""
target_path = ""
print(os.getcwd())

if os.name == "nt":
    target_path = os.getcwd() + "\dist\*.whl"
else:
    target_path = os.getcwd() + "/dist/*.whl"

print(target_path)

for name in glob.glob(target_path):
    if os.path.isfile(name):
        target_wheel = name

print(target_wheel)

if os.name == "nt":
    target_path = os.getcwd() + "\libdogecoin-*\*.so"
else:
    target_path = os.getcwd() + "/libdogecoin-*/*.so"

subprocess.run(["python -m wheel unpack " + target_wheel], shell=True, check=True)
for so in glob.glob():
    if os.path.isfile(so):
        print(so)
        file = so.split('\\')[-1]
        print(file)
        # os.rename(so, )
# python3 -m venv .venv
# source .venv/bin/activate
# python3 -m pip install --upgrade wheel pytest
# wheel unpack "$TARGET_WHEEL"
# cp -r libdogecoin-*/* .
# python3 -m pytest
# deactivate
# rm -rf .venv *.so libdogecoin-*/ *.libs tests/__pycache__ .pytest_cache