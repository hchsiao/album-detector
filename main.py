# TODO: check https://github.com/flacon/flacon/issues/41
import argparse
import os

from utils import mkinfo

parser = argparse.ArgumentParser(description='TODO')
parser.add_argument('path') 

args = parser.parse_args()

path = os.path.normpath(args.path)
mkinfo(path)
