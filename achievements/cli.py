"""命令行入口：跑成就进度样例。"""

import argparse

from .core import Achievements


def build_parser():
    parser = argparse.ArgumentParser(prog="achievement-track", description="成就进度")
    parser.add_argument("--sample", default="dup", help="dup / cap / exact / scan")
    return parser


def main(argv=None):
    args = build_parser().parse_args(argv)
    if args.sample == "dup":
        book = Achievements()
        book.report("e1", "slayer", 5, 10)
        book.report("e1", "slayer", 5, 10)
        print("progress=%d done=%s" % (book.progress_of("slayer"), str(book.is_done("slayer")).lower()))
    elif args.sample == "cap":
        book = Achievements()
        book.report("e1", "slayer", 20, 10)
        print("progress=%d done=%s" % (book.progress_of("slayer"), str(book.is_done("slayer")).lower()))
    elif args.sample == "exact":
        book = Achievements()
        book.report("e1", "slayer", 10, 10)
        print("done=%s" % str(book.is_done("slayer")).lower())
    elif args.sample == "scan":
        book = Achievements()
        for index in range(3000):
            book.report("e-%d" % index, "a-%d" % index, 1, 100)
        for _ in range(3000):
            book.progress_of("a-2999")
        print("scanned=%d" % book.scanned_count())
    else:
        raise SystemExit("需要 --sample dup|cap|exact|scan")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
