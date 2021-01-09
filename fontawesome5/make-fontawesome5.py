#!/usr/bin/env python3
#
# Copyright (c) 2018 Weitian LI
# MIT License
#

"""
Create Font Awesome v5 mapping for XeLaTeX.

Credits:
* FontAwesome
  https://github.com/FortAwesome/Font-Awesome
* FontAwesome 5.0.0-beta.6 mapping for XeLaTeX
  https://gist.github.com/phyllisstein/b790f853dac935060087f78839043b36
* Awesome-CV / fontawesome.sty
  https://github.com/posquit0/Awesome-CV/blob/master/fontawesome.sty
* LaTeX - Creating Packages
  https://en.wikibooks.org/wiki/LaTeX/Creating_Packages
"""

import os
import sys
import argparse
import urllib.request
from datetime import datetime

# Require the 'PyYAML' package (or 'python3-yaml' package on Debian)
import yaml

FA_URL = "https://github.com/FortAwesome/Font-Awesome"
ICONS_URL = FA_URL + "/raw/master/metadata/icons.yml"  # NOTE: 'raw' is correct
ALLOWED_CHARS = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"

# Fonts styles
FONTS = {
    "regular": "FontAwesomeRegular",
    "solid": "FontAwesomeSolid",
    "brands": "FontAwesomeBrands",
}

# LaTeX style template
STY_TEMPLATE = """%%
%% Font Awesome v5 mapping for XeLaTeX
%%
%% Generated by: %(program)s
%% Date: %(date)s
%%
%% Usage
%% -----
%% 1. \\usepackage{fontawesome}  %% Prefer *Solid* style by default
%%    or
%%    \\usepackage[regular]{fontawesome}  %% Prefer *Regular* style
%%
%%    NOTE:
%%    The *Solid* style has much more icons than the *Regular* style.
%%    If one style doesn't have one icon, it fallbacks to the other style.
%%
%% 2. use an icon, e.g., \\faGitHub
%%

\\NeedsTeXFormat{LaTeX2e}[1994/06/01]
\\ProvidesPackage{fontawesome5}[%(date)s Font Awesome 5]

\\DeclareOption{regular}{\\def\\FA@regular{true}}
\\ProcessOptions\\relax

\\RequirePackage{fontspec}

%% Declare all variants
%% Solid (default)
\\newfontfamily\\FontAwesomeSolid[
  BoldFont={Font Awesome 5 Free Solid},
]{Font Awesome 5 Free Solid}
%% Regular
\\newfontfamily\\FontAwesomeRegular[
  BoldFont={Font Awesome 5 Free},
]{Font Awesome 5 Free}
%% Brands
\\newfontfamily\\FontAwesomeBrands[
  BoldFont={Font Awesome 5 Brands},
]{Font Awesome 5 Brands}

%% Generic command displaying an icon by its name
%% \\newcommand*{\\faicon}[1]{{\FA\csname faicon@#1\endcsname}}

%% Mappings
%(mappings)s

%% TeX commands
\\ifundef{\\FA@regular}{
%% [Solid] fallback to Regular style
%(cmds_solid)s
}{
%% [Regular] fallback to Solid style
%(cmds_regular)s
}
%% [Brands]
%(cmds_brands)s

\\endinput
%% EOF
"""


def get_icons_yml(url=ICONS_URL):
    print("Downloading icons.yml from: %s" % url)
    resp = urllib.request.urlopen(url)
    data = resp.read()
    return data.decode("utf-8")


def make_cmdname(name):
    cmdname = []
    upper = False
    for i, c in enumerate(name):
        if c == "-":
            upper = True
            continue
        if i == 0:
            upper = True
        if upper:
            cmdname.append(c.upper())
        else:
            cmdname.append(c)
        upper = False
    return "".join(cmdname)


def make_map(name, symbol):
    """
    Map Font Awesome icon names to unicode symbols
    """
    return '\\expandafter\\def\\csname faicon@%(name)s\\endcsname{\\symbol{"%(symbol)s}}' % {
        "name": name,
        "symbol": symbol.upper(),
    }


def make_cmd(name, icon, style="solid"):
    """
    Create LaTeX command to use Font Awesome icons
    """
    cmdname = make_cmdname(name)
    if style == "solid":
        fallback = "regular"
    elif style == "regular":
        fallback = "solid"
    elif style == "brands":
        fallback = None
    else:
        raise ValueError("Invalid style: %s" % style)

    if style in icon["styles"]:
        font = FONTS[style]
    elif fallback in icon["styles"]:
        font = FONTS[fallback]
    else:
        return None

    return '\\def\\fa%(cmdname)s{{\\%(font)s\\csname faicon@%(name)s\\endcsname}}' % {
        "font": font,
        "cmdname": cmdname,
        "name": name,
    }


def main():
    parser = argparse.ArgumentParser(
        description="Create Font Awesome v5 mapping for XeLaTeX")
    parser.add_argument("-C", "--clobber", action="store_true",
                        help="overwrite existing output file")
    parser.add_argument("-i", "--infile",
                        help="input icons.yml file of icons information " +
                        "(default: download from FontAwesome's repo)")
    parser.add_argument("-o", "--outfile", default="fontawesome5.sty",
                        help="output LaTeX style file " +
                        "(default: fontawesome5.sty)")
    args = parser.parse_args()

    if os.path.exists(args.outfile):
        if args.clobber:
            os.remove(args.outfile)
            print("Removed existing file: %s" % args.outfile)
        else:
            raise OSError("File already exists: %s" % args.outfile)

    if args.infile:
        data = open(args.infile).read()
    else:
        data = get_icons_yml()

    print("Loading icons data ...")
    icons = yaml.safe_load(data)
    icon_list = sorted(icons.keys())
    print("Number of icons: %d" % len(icon_list))

    mappings = [make_map(name, icons[name]["unicode"])
                for name in icon_list]
    cmds_regular = [make_cmd(name, icons[name], style="regular")
                    for name in icon_list]
    cmds_solid = [make_cmd(name, icons[name], style="solid")
                  for name in icon_list]
    cmds_brands = [make_cmd(name, icons[name], style="brands")
                   for name in icon_list]
    # Exclude None's
    cmds_regular = [cmd for cmd in cmds_regular if cmd]
    cmds_solid = [cmd for cmd in cmds_solid if cmd]
    cmds_brands = [cmd for cmd in cmds_brands if cmd]

    data = {
        "program": os.path.basename(sys.argv[0]),
        "date": datetime.now().strftime("%Y/%m/%d"),
        "mappings": "\n".join(mappings),
        "cmds_regular": "\n".join(cmds_regular),
        "cmds_solid": "\n".join(cmds_solid),
        "cmds_brands": "\n".join(cmds_brands),
    }

    open(args.outfile, "w").write(STY_TEMPLATE % data)
    print("Mapping writen to file: %s" % args.outfile)


if __name__ == "__main__":
    main()
