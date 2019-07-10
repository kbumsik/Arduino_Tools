
import argparse
import datetime
import fnmatch
import json
import os
import re
import sys
import textwrap

# by default, generate for all mcu xml files description
parser = argparse.ArgumentParser(
    description=textwrap.dedent(
        """\
"""
    ),
    epilog=textwrap.dedent(
        """\
This is a tool to automate some dirty works when adding a new MCU line
in the Arduino Core for STM32. This adds #include preprocessor directives
for the new MCU line in the following files:
- Arduino_Core_STM32/cores/arduino/stm32/LL/stm32yyxx_ll_xxxx.c
- Arduino_Core_STM32/cores/arduino/stm32/HAL/stm32yyxx_hal_xxxx.c

The user must include necessary HAL drivers in
Arduino_Core_STM32/system/Drivers/STM32yyxx_HAL_Driver. It is the user's
responsibility to review them carefully after running this automation tool.
"""
    ),
    formatter_class=argparse.RawTextHelpFormatter,
)
parser.add_argument('mcu_line',
                    help='Name of MCU line (e.g. STM32MP1xx)')
parser.add_argument('core_path',
                    help='Path to local git repository of Arduino_Core_STM32')
args = parser.parse_args()

DRIVER_PATH = os.path.join(args.core_path, 'system/Drivers')
ARDUINO_HAL_PATH = os.path.join(args.core_path, 'cores/arduino/stm32/HAL')
ARDUINO_LL_PATH = os.path.join(args.core_path, 'cores/arduino/stm32/LL')
HAL_DRIVER_PATH = os.path.join(DRIVER_PATH, f'{args.mcu_line}_HAL_Driver')

# Parameter and paths check
path_check_list = [
    (DRIVER_PATH, 'HAL driver path'),
    (ARDUINO_HAL_PATH, 'Target Arduino HAL driver path'),
    (ARDUINO_LL_PATH, 'Target Arduino LL driver path'),
    (HAL_DRIVER_PATH, f'HAL driver for {args.mcu_line}')
]
for (path, name) in path_check_list:
    if not os.path.isdir(path):
        print(f'{name} not found: {path}')
        print('Please check the correct path to Arduino_Core_STM32.')
        quit()

"""
1. Get list of all files in the HAL driver
2. Match each files with a file in the target HAL/LL folder
3. Add/replace #include directives to the matched file
4. If not found, just warn user so that the user can consider adding it
"""

source_files = {} # 'filename': 'file path'
target_files = {} # 'filename': 'file path'
file_pattern = re.compile(r'^(\S+)_(hal|ll)(_(\S+))?.(c|h)$')
"""
Catches the following format:
#ifdef STM32F2xx
#include "stm32f2xx_ll_usb.h"
#endif
"""
include_str = r'#ifdef\s+(\S+)\s+#include\s+[\"|\'](\S+)[\"|\']\s+#endif\s*'
include_pattern = re.compile(f'^{include_str}$', re.MULTILINE)
include_block_pattern = re.compile(f'({include_str})+', re.MULTILINE)


# 1. Get list of all HAL source files
for dirname in ('Inc', 'Src'):
    # Original HAL directory
    path = os.path.join(HAL_DRIVER_PATH, dirname)
    new_files = {
        f: os.path.join(path, f)
        for f in os.listdir(path)
        if os.path.isfile(os.path.join(path, f))
            # filter out such as stm32mp1xx_hal_adc.h since header files for HAL not used in the target.
            and not (dirname == 'Inc' and '.h' in f and '_hal_' in f)
    }
    source_files = {**source_files, **new_files}
for path in (ARDUINO_HAL_PATH, ARDUINO_LL_PATH):
    # Target directories
    new_files = {
        f: os.path.join(path, f)
        for f in os.listdir(path)
        if os.path.isfile(os.path.join(path, f))
    }
    target_files = {**target_files, **new_files}

for name, path in source_files.items():
    match = re.match(file_pattern, name)
    if match and match.group(4):
        # e.g stm32mp1xx_hal_adc_ex.c => stm32yyxx_hal_adc_ex.c
        target_name = re.sub(file_pattern, r'stm32yyxx_\2_\4.\5', name)
    elif match and match.group(2):
        # e.g stm32mp1xx_hal.c => stm32yyxx_hal.c
        target_name = re.sub(file_pattern, r'stm32yyxx_\2.\5', name)
    else:
        target_name = name
    # 2. Match each files with the target files
    if target_name not in target_files:
        print(f'WARNING: {target_name} is not found in the target path.')
        continue
    # 3. Get list of existing #include directives in a file
    content = open(target_files[target_name]).read()
    output = ''
    mcu_printed = False
    include_str = f"""\
#ifdef {args.mcu_line}
#include "{name}"
#endif
"""
    for s in re.finditer(include_pattern, content):
        if not mcu_printed and args.mcu_line <= s.group(1):
            mcu_printed = True
            output += include_str
        if args.mcu_line == s.group(1):
            continue
        output += s.group(0).rstrip() + '\n'
    if not mcu_printed:
        output += include_str
    open(target_files[target_name], 'w').write(re.sub(include_block_pattern, output, content))
