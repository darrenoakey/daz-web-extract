#!/usr/bin/env python3
import argparse
import asyncio
import json
import sys

import setproctitle


# ##################################################################
# command extract
# extract content from a url and print results
def command_extract(args: argparse.Namespace) -> int:
    from daz_web_extract import extract
    result = asyncio.run(extract(args.url))
    if args.raw:
        print(json.dumps(result.to_dict(), indent=2))
    else:
        if result.success:
            print(f"Title: {result.title}")
            print(f"Method: {result.fetch_method}")
            print(f"Length: {result.content_length} chars")
            print(f"Time: {result.elapsed_ms}ms")
            print()
            print(result.body)
        else:
            print(f"Failed: {result.error}", file=sys.stderr)
    return 0 if result.success else 1


# ##################################################################
# main
# parse arguments and dispatch
def main(argv: list[str]) -> int:
    setproctitle.setproctitle("daz-web-extract")
    parser = argparse.ArgumentParser(prog="daz-web-extract")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_extract = sub.add_parser("extract", help="Extract content from a URL")
    p_extract.add_argument("url", help="URL to extract")
    p_extract.add_argument("--raw", action="store_true", help="Output raw JSON")
    p_extract.set_defaults(func=command_extract)

    args = parser.parse_args(argv)
    return args.func(args)


# ##################################################################
# entry point
if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
