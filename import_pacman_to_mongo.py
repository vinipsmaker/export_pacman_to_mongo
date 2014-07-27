#!/usr/bin/env python

#  Copyright (c) 2014 Vinícius dos Santos Oliveira
#
#  Permission is hereby granted, free of charge, to any person obtaining a copy
#  of this software and associated documentation files (the "Software"), to deal
#  in the Software without restriction, including without limitation the rights
#  to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
#  copies of the Software, and to permit persons to whom the Software is
#  furnished to do so, subject to the following conditions:
#
#  The above copyright notice and this permission notice shall be included in all
#  copies or substantial portions of the Software.
#
#  THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
#  IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#  FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
#  AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
#  LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
#  OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
#  SOFTWARE.

import os
import subprocess
import dateutil.parser

import pymongo

for localekey in ('LANG', 'LANGUAGE', 'LC_CTYPE', 'LC_NUMERIC', 'LC_TIME',
                  'LC_COLLATE', 'LC_MONETARY', 'LC_MESSAGES', 'LC_PAPER',
                  'LC_NAME', 'LC_ADDRESS', 'LC_TELEPHONE', 'LC_MEASUREMENT',
                  'LC_IDENTIFICATION'):
    os.environ[localekey] = 'en_US.UTF-8'

def identity(x):
    return x

def provides_value_to_hierarchical(value):
    try:
        offset = value.index('=')
        return {'name': value[:offset], 'version': value[offset+1:]}
    except ValueError:
        return {'name': value}

def depends_on_value_to_hierarchical(value):
    comparisons = ['>=', '<=', '=', '>', '<']

    for c in comparisons:
        try:
            offset = value.index(c)
            return {'name': value[:offset],
                    'version': {'comparison': c,
                                'value': value[offset+len(c):]}}
        except ValueError:
            pass

    return {'name': value}

def optional_deps_to_hierarchical(buffer):
    if buffer[0].endswith('None'):
        return None

    delim = ': '
    offset = buffer[0].index(delim) + len(delim)

    for i in range(len(buffer)):
        buffer[i] = buffer[i][offset:]

    extra_info = ' [installed]'
    for i in range(len(buffer)):
        if buffer[i].endswith(extra_info):
            buffer[i] = buffer[i][:-len(extra_info)]

    ret = []

    for spec in buffer:
        try:
            offset = spec.index(delim)
            ret.append({'name': spec[:offset],
                        'reason': spec[offset+len(delim):]})
        except ValueError:
            ret.append({'name': spec})

    return ret

def package_to_hierarchical(package, repo):
    delim = ': '

    # optional_deps is handled separately
    multi_valued_properties = {'licenses': identity,
                               'groups': identity,
                               'provides': provides_value_to_hierarchical,
                               'depends_on': depends_on_value_to_hierarchical,
                               'required_by': identity,
                               'optional_for': identity,
                               'conflicts_with': depends_on_value_to_hierarchical,
                               'replaces': depends_on_value_to_hierarchical}
    special_properties = {'build_date': dateutil.parser.parse,
                          'install_date': dateutil.parser.parse}

    ret = {}
    output = subprocess.check_output(
        ['pacman', '-Qi', package], universal_newlines=True).split('\n')[:-2]
    offset = output[0].index(delim) + len(delim)

    # begin of 'Optional Deps' handling

    nextfield = 10
    while output[nextfield][offset - len(delim)] != delim[0]:
        nextfield += 1

    optional_deps = optional_deps_to_hierarchical(list(output[9:nextfield]))
    if optional_deps:
        ret['optional_deps'] = optional_deps
    del output[9:nextfield]

    # end of 'Optional Deps' handling

    for line in output:
        value = line[offset:]

        if value == 'None':
            continue

        key = line.split(delim)[0].strip().lower().replace(' ', '_')
        if key not in multi_valued_properties.keys():
            ret[key] = value if key not in special_properties else (
                special_properties[key](value))
        else:
            ret[key] = [multi_valued_properties[key](i)
                        for i in value.split('  ')]

    # begin of 'repo' handling

    if repo != "":
        ret["repo"] = repo

    # end of 'repo' handling

    return ret

packages = [i.split(' ')[0]
            for i in str(subprocess.check_output(['pacman', '-Q'],
                                                 universal_newlines=True))
                     .split('\n')[:-1]]

local_packages = [i.split(' ')[0]
                  for i in str(subprocess.check_output(['pacman', '-Qm'],
                                                       universal_newlines=True))
                           .split('\n')[:-1]]

client = pymongo.MongoClient()

# TODO: allow user to specify database and collection
db = client.pacman
coll = db.packages

nimported = 0
for p in packages:
    repo = "local" if p in local_packages else ""
    coll.insert(package_to_hierarchical(p, repo))
    nimported += 1
    print("Imported:", str(nimported) + '/' + str(len(packages)))
