#!/bin/bash
set -e -o pipefail

sed -i -e 's/\r$//' $2
