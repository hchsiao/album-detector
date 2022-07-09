import argparse
import os
import json

def main():
    parser = argparse.ArgumentParser(description='TODO')
    parser.add_argument('path') 
    args = parser.parse_args()
    with open(args.path, 'r') as f:
        indexes = json.load(f)
        print(indexes)

if __name__ == "__main__":
    main()
