" Copyright 2018 The Chromium OS Authors. All rights reserved.
" Use of this source code is governed by a BSD-style license that can be
" found in the LICENSE file.
"
" Sort python imports
" we only care about python2
"
" According to python coding style, the import lines are sorted by package
" path.
if has('python')
  command! -range -nargs=* VimPython <line1>,<line2>python <args>
elseif has('python3')
  command! -range -nargs=* VimPython <line1>,<line2>python3 <args>
else
  echoerr "sort_import plugin will not work because the version of vim" .
      \ " supports neither python nor python3"
  finish
endif

if !exists('g:vim_sort_import_map')
  let g:vim_sort_import_map = '<Leader>si'
endif

if g:vim_sort_import_map != ''
  execute "vnoremap <buffer>" g:vim_sort_import_map
      \ ":VimPython SortImports()<CR>"
endif

VimPython <<EOF
from __future__ import print_function
import vim

def SortImports():
  text_range = vim.current.range

  def _ImportLineToKey(line):
    if line.startswith('import '):
      return line.replace('import ', '').lower()
    return line.replace('from ', '').replace(' import ', '.').lower()
  text_range[:] = sorted(text_range, key=_ImportLineToKey)
EOF
