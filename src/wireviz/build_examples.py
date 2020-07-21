#!/usr/bin/python3
# -*- coding: utf-8 -*-

import argparse
import sys
import os
from pathlib import Path

script_path = Path(__file__).absolute()

sys.path.insert(0, str(script_path.parent.parent))  # to find wireviz module
from wireviz import wireviz
from wv_helper import open_file_write, open_file_read, open_file_append


readme = 'readme.md'
paths = {}
paths['examples'] = {'path': Path(script_path).parent.parent.parent / 'examples',
                     'prefix': 'ex',
                     readme: [], # Include no files
                     'title': 'Example Gallery'}
paths['tutorial'] = {'path': Path(script_path).parent.parent.parent / 'tutorial',
                     'prefix': 'tutorial',
                     readme: ['md', 'yml'], # Include .md and .yml files
                     'title': 'WireViz Tutorial'}
paths['demos']    = {'path': Path(script_path).parent.parent.parent / 'examples',
                     'prefix': 'demo'}

input_extensions = ['.yml']
generated_extensions = ['.gv', '.png', '.svg', '.html', '.bom.tsv']
extensions_not_from_graphviz = [ext for ext in generated_extensions if ext[-1] == 'v']


def collect_filenames(description, pathkey, ext_list, extrafile = None):
    path = paths[pathkey]['path']
    patterns = [f"{paths[pathkey]['prefix']}*{ext}" for ext in ext_list]
    if extrafile is not None:
        patterns.append(extrafile)
    print(f"{description} {path}")
    return sorted([filename for pattern in patterns for filename in path.glob(pattern)])


def build(dirname):
    # build files
    path = paths[dirname]['path']
    build_readme = readme in paths[dirname]
    if build_readme:
        include_readme = 'md' in paths[dirname][readme]
        include_source = 'yml' in paths[dirname][readme]
        with open_file_write(path / 'readme.md') as out:
            out.write(f'# {paths[dirname]["title"]}\n\n')
    # collect and iterate input YAML files
    for yaml_file in collect_filenames('Building', dirname, input_extensions):
        print(f'  {yaml_file}')
        wireviz.parse_file(yaml_file)

        if build_readme:
            i = ''.join(filter(str.isdigit, yaml_file.stem))

            with open_file_append(path / readme) as out:
                if include_readme:
                    with open_file_read(path / f'{yaml_file.stem}.md') as info:
                        for line in info:
                            out.write(line.replace('## ', '## {} - '.format(i)))
                        out.write('\n\n')
                else:
                    out.write(f'## Example {i}\n')

                if include_source:
                    with open_file_read(yaml_file) as src:
                        out.write('```yaml\n')
                        for line in src:
                            out.write(line)
                        out.write('```\n')
                    out.write('\n')

                out.write(f'![]({yaml_file.stem}.png)\n\n')
                out.write(f'[Source]({yaml_file.name}) - [Bill of Materials]({yaml_file.stem}.bom.tsv)\n\n\n')


def clean_generated(pathkeys):
    for key in pathkeys:
        # collect and remove files
        for filename in collect_filenames('Cleaning', key, generated_extensions, readme if readme in paths[key] else None):
            if filename.is_file():
                print(f'  rm {filename}')
                os.remove(filename)


def compare_generated(pathkeys, include_from_graphviz = False):
    compare_extensions = generated_extensions if include_from_graphviz else extensions_not_from_graphviz
    for key in pathkeys:
        # collect and compare files
        for filename in collect_filenames('Comparing', key, compare_extensions, readme if readme in paths[key] else None):
            cmd = f'git --no-pager diff {filename}'
            print(f'  {cmd}')
            os.system(cmd)


def restore_generated(pathkeys):
    for key in pathkeys:
        # collect input YAML files
        filename_list = collect_filenames('Restoring', key, input_extensions)
        # collect files to restore
        filename_list = [fn.with_suffix(ext) for fn in filename_list for ext in generated_extensions]
        if readme in paths[key]:
            filename_list.append(paths[key]['path'] / readme)
        # restore files
        for filename in filename_list:
            cmd = f'git checkout -- {filename}'
            print(f'  {cmd}')
            os.system(cmd)


def parse_args():
    parser = argparse.ArgumentParser(description='Wireviz Example Manager',)
    parser.add_argument('action', nargs='?', action='store', choices=['build','clean','compare','restore'], default='build')
    parser.add_argument('-generate', nargs='*', choices=paths.keys(), default=paths.keys())
    return parser.parse_args()


def main():
    args = parse_args()
    if args.action == 'build':
        for gentype in args.generate:
            build(gentype)
    elif args.action == 'clean':
        clean_generated(args.generate)
    elif args.action == 'compare':
        compare_generated(args.generate)
    elif args.action == 'restore':
        restore_generated(args.generate)


if __name__ == '__main__':
    main()
