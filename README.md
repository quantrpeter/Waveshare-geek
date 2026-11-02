# Waveshare-geek

ESP32-S3-GEEK MicroPython demos for [lvgl_micropython](https://github.com/lvgl-micropython/lvgl_micropython). Board: 1.14" 240x135 ST7789, 16MB flash, 2MB Octal PSRAM.

[](https://peter.hkprog.org/2026/11/waveshare-esp32-geek-lvgl_micropython/)

## Firmware

```sh
python3 make.py esp32 \
    --flash-size=16 \
    BOARD=ESP32_GENERIC_S3 \
    DISPLAY=st7789 \
    BOARD_VARIANT=SPIRAM_OCT
```

## LCD demo

[LCD/lcd.py](LCD/lcd.py) draws color bars, a white frame (so a bad GRAM offset is obvious), and a moving marker. BOOT toggles color inversion.

```sh
cd LCD
make run
```

Panel pins: MOSI 11, SCK 12, CS 10, DC 8, RST 9, BL 7. Landscape window is MADCTL `0x70` with offsets x=40, y=53.

