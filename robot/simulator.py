"""Run python -m robot.simulator --correct [--absent]. No hardware access."""
import argparse
import json
from robot.service import react

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--correct', action='store_true')
    parser.add_argument('--absent', action='store_true')
    args = parser.parse_args()
    print(json.dumps(react(args.correct, not args.absent), ensure_ascii=False, indent=2))

if __name__ == '__main__': main()
