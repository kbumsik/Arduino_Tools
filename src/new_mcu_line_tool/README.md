# new_mcu_line_tool

This is a tool to automate some dirty works when adding a new MCU line in [the Arduino Core for STM32](https://github.com/stm32duino/Arduino_Core_STM32).

This adds `#include` preprocessor directives for the new MCU line in the following files:

* `cores/arduino/stm32/LL/stm32yyxx_ll_xxxx.c`
* `cores/arduino/stm32/HAL/stm32yyxx_hal_xxxx.c`

The user must include necessary HAL drivers in `system/Drivers/STM32yyxx_HAL_Driver`.

It is the user's responsibility to review them carefully after running this automation tool.
