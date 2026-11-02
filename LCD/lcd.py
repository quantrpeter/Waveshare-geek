import lcd_bus
import machine
import st7789
import lvgl as lv
from time import sleep

# ESP32-S3-GEEK 1.14" IPS, ST7789, 240x135.
# Pins and the landscape GRAM window match Waveshare's LCD_1inch14 example:
#   MOSI=11 SCK=12 CS=10 DC=8 RST=9 BL=7  MADCTL=0x70
#   CASET 0x28..0x117 (x offset 40)  RASET 0x35..0xBB (y offset 53)
_WIDTH = 240
_HEIGHT = 135
_MOSI = 11
_MISO = -1
_SCK = 12
_HOST = 1
_CS = 10
_DC = 8
_RST = 9
_BL = 7
_BOOT = 0
_LCD_FREQ = 40000000
_OFFSET_X = 40
_OFFSET_Y = 53
_MADCTL = 0x70  # MX | MV | ML
_DRAW_LINES = 45
_COLOR_ORDER = st7789.BYTE_ORDER_BGR  # RGB swaps red and blue on this panel

_BARS = (
    0xE53935,  # red
    0xFB8C00,  # orange
    0xFDD835,  # yellow
    0x43A047,  # green
    0x1E88E5,  # blue
    0x8E24AA,  # purple
    0xFFFFFF,  # white
)


def _allocate_draw_buffers(display_bus, width, lines):
    buf_size = width * lines * lv.color_format_get_size(lv.COLOR_FORMAT.RGB565)
    print("Allocating draw buffer:", width, "x", lines, "=", buf_size, "bytes")

    for flags, label in (
        (lcd_bus.MEMORY_SPIRAM | lcd_bus.MEMORY_DMA, "SPIRAM|DMA"),
        (lcd_bus.MEMORY_SPIRAM, "SPIRAM"),
        (lcd_bus.MEMORY_INTERNAL | lcd_bus.MEMORY_DMA, "INTERNAL|DMA"),
        (lcd_bus.MEMORY_INTERNAL, "INTERNAL"),
    ):
        try:
            buf1 = display_bus.allocate_framebuffer(buf_size, flags)
            print("Framebuffer 1:", label)
        except MemoryError:
            continue

        buf2 = None
        try:
            buf2 = display_bus.allocate_framebuffer(buf_size, flags)
            print("Framebuffer 2:", label)
        except MemoryError:
            print("Second framebuffer unavailable, using single buffering")

        return buf1, buf2

    raise MemoryError("Unable to allocate draw buffers")


def _rect(parent, x, y, w, h, color):
    obj = lv.obj(parent)
    obj.set_scrollbar_mode(lv.SCROLLBAR_MODE.OFF)
    obj.set_style_bg_color(lv.color_hex(color), 0)
    obj.set_style_bg_opa(lv.OPA.COVER, 0)
    obj.set_style_border_width(0, 0)
    obj.set_style_radius(0, 0)
    obj.set_style_pad_all(0, 0)
    obj.set_size(w, h)
    obj.set_pos(x, y)
    return obj


print("Initializing SPI bus...")
spi_bus = machine.SPI.Bus(
    host=_HOST,
    mosi=_MOSI,
    miso=_MISO,
    sck=_SCK,
)

print("Initializing display bus...")
display_bus = lcd_bus.SPIBus(
    spi_bus=spi_bus,
    dc=_DC,
    cs=_CS,
    freq=_LCD_FREQ,
    spi_mode=0,
)

buf1, buf2 = _allocate_draw_buffers(display_bus, _WIDTH, _DRAW_LINES)

print("Initializing ST7789...")
display = st7789.ST7789(
    data_bus=display_bus,
    display_width=_WIDTH,
    display_height=_HEIGHT,
    frame_buffer1=buf1,
    frame_buffer2=buf2,
    reset_pin=_RST,
    reset_state=st7789.STATE_LOW,
    backlight_pin=_BL,
    backlight_on_state=st7789.STATE_HIGH,
    offset_x=_OFFSET_X,
    offset_y=_OFFSET_Y,
    color_byte_order=_COLOR_ORDER,
    color_space=lv.COLOR_FORMAT.RGB565,
    rgb565_byte_swap=True,
)

# Active-low reset, then the driver init (which also sends INVON).
display.reset()
sleep(0.02)
display.init()

# Driver init writes orientation 0 (MADCTL 0x00). This panel's 240x135
# window is the Waveshare landscape map, so force that MADCTL afterwards.
display.set_params(0x36, bytes([_MADCTL | _COLOR_ORDER]))
# This panel needs INVON, or it shows a negative picture.
display.set_params(0x21)
display.set_backlight(100)
print("Display ready")

scrn = lv.screen_active()
scrn.set_style_bg_color(lv.color_hex(0x101418), 0)
scrn.set_scrollbar_mode(lv.SCROLLBAR_MODE.OFF)

_rect(scrn, 0, 0, _WIDTH, 2, 0xFFFFFF)
_rect(scrn, 0, _HEIGHT - 2, _WIDTH, 2, 0xFFFFFF)
_rect(scrn, 0, 0, 2, _HEIGHT, 0xFFFFFF)
_rect(scrn, _WIDTH - 2, 0, 2, _HEIGHT, 0xFFFFFF)

title = lv.label(scrn)
title.set_text("ESP32-S3-GEEK")
title.set_style_text_color(lv.color_hex(0xFFFFFF), 0)
title.set_style_text_font(lv.font_montserrat_14, 0)
title.align(lv.ALIGN.TOP_MID, 0, 6)

subtitle = lv.label(scrn)
subtitle.set_text("240x135 ST7789")
subtitle.set_style_text_color(lv.color_hex(0x90A4AE), 0)
subtitle.set_style_text_font(lv.font_montserrat_14, 0)
subtitle.align(lv.ALIGN.TOP_MID, 0, 24)

bar_y = 46
bar_h = 48
bar_gap = 3
bar_w = (_WIDTH - 8 - bar_gap * (len(_BARS) - 1)) // len(_BARS)
bar_x = 4
for color in _BARS:
    _rect(scrn, bar_x, bar_y, bar_w, bar_h, color)
    bar_x += bar_w + bar_gap

marker = _rect(scrn, 4, 102, 16, 16, 0x00E5FF)
status = lv.label(scrn)
status.set_style_text_color(lv.color_hex(0xFFFFFF), 0)
status.set_style_text_font(lv.font_montserrat_14, 0)
status.align(lv.ALIGN.BOTTOM_LEFT, 24, -6)
status.set_text("frame 0")

boot = machine.Pin(_BOOT, machine.Pin.IN, machine.Pin.PULL_UP)
marker_x = 4
marker_dx = 4
frame = 0
boot_was_down = False
invert = True

print("LCD demo running (BOOT toggles invert)")
lv.refr_now(None)

while True:
    marker_x += marker_dx
    if marker_x <= 4 or marker_x >= _WIDTH - 20:
        marker_dx = -marker_dx
        marker_x += marker_dx
    marker.set_pos(marker_x, 102)

    frame += 1
    if frame % 5 == 0:
        status.set_text("frame %d" % frame)

    boot_down = boot.value() == 0
    if boot_down and not boot_was_down:
        invert = not invert
        display.set_color_inversion(invert)
        print("invert", invert)
    boot_was_down = boot_down

    lv.task_handler()
    lv.refr_now(None)
    sleep(0.03)
