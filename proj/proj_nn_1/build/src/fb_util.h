/*
 * Copyright 2021 The CFU-Playground Authors
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *      http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */

#ifndef FB_UTIL_H
#define FB_UTIL_H

#include <stdio.h>
#include <stdint.h>
#include <stdlib.h>
#include <string.h>

#include <generated/csr.h>
#include <generated/soc.h>
#include <generated/mem.h>

struct font_basis {
    uint8_t data[8];
};

struct dotfont_info {
    uint8_t font_width;
    uint8_t font_height;
    uint8_t font_length;
    uint8_t font_counts;
    struct font_basis f_basis[256];
    const uint8_t *font_data;
};

void fb_init();
void fb_clear();
void fb_close();

int32_t fb_fill_rect(uint32_t left, uint32_t top, uint32_t width,
                     uint32_t height, uint32_t color);
int32_t fb_draw_rect(uint32_t left, uint32_t top, uint32_t width,
                     uint32_t height, uint32_t color);
int32_t fb_draw_buffer(uint32_t left, uint32_t top, uint32_t width,
                       uint32_t height, const uint8_t * src_buff,
                       uint32_t color_channels);
int32_t fb_draw_line(uint32_t x0, uint32_t y0, uint32_t x1, uint32_t y1,
                     uint32_t color, int32_t width);
int32_t fb_draw_string(uint32_t x, uint32_t y, uint32_t color,
                       const char *msg_str);

void framebuffer_menu(void);

#endif                          // FB_UTIL_H
