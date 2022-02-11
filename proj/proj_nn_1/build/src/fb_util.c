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

#include <stdio.h>
#include <stdint.h>
#include <stdlib.h>
#include <string.h>

#include <generated/csr.h>
#include <generated/soc.h>
#include <generated/mem.h>
#include <system.h>

#include "menu.h"
#include "perf.h"

#include "fb_util.h"


#ifdef CSR_VIDEO_FRAMEBUFFER_BASE

#define FB_WIDTH       VIDEO_FRAMEBUFFER_HRES
#define FB_HEIGHT      VIDEO_FRAMEBUFFER_VRES
#define FB_BASE_ADDR   VIDEO_FRAMEBUFFER_BASE


extern const unsigned char BigFont[];
static int32_t dotfont_initilized = 0;
static struct dotfont_info df_info = { 0 };

static void dotfont_init();


static void dotfont_init()
{
    int32_t x = 0;
    unsigned char tmp_val = 0;
    struct font_basis *f_basis = NULL;


    df_info.font_width = BigFont[0];
    df_info.font_height = BigFont[1];
    df_info.font_length = BigFont[2];
    df_info.font_counts = BigFont[3];
    df_info.font_data = BigFont + 4;

    for (x = 0; x <= 0xFF; x++) {
        f_basis = (struct font_basis *) &df_info.f_basis[x];
        tmp_val = x;
        f_basis->data[0] = (tmp_val & 0x80) ? 'X' : '.';
        f_basis->data[1] = (tmp_val & 0x40) ? 'X' : '.';
        f_basis->data[2] = (tmp_val & 0x20) ? 'X' : '.';
        f_basis->data[3] = (tmp_val & 0x10) ? 'X' : '.';
        f_basis->data[4] = (tmp_val & 0x08) ? 'X' : '.';
        f_basis->data[5] = (tmp_val & 0x04) ? 'X' : '.';
        f_basis->data[6] = (tmp_val & 0x02) ? 'X' : '.';
        f_basis->data[7] = (tmp_val & 0x01) ? 'X' : '.';
    }

    dotfont_initilized = 1;
}

void fb_init()
{
    int i = 0;
    uint8_t *fb_ptr = NULL;
    uint32_t fb_len = 0;

    video_framebuffer_vtg_enable_write(0);
    video_framebuffer_dma_enable_write(0);

    for (i = 0; i < 0x10000; i++) {
        __asm__ __volatile__("add zero, zero, zero");
    }

    video_framebuffer_vtg_enable_write(1);
    video_framebuffer_dma_enable_write(1);

    for (i = 0; i < 0x10000; i++) {
        __asm__ __volatile__("add zero, zero, zero");
    }

    fb_ptr = (uint8_t *) FB_BASE_ADDR;
    fb_len = FB_WIDTH * FB_HEIGHT * sizeof(uint32_t);
    memset(fb_ptr, 0x00, fb_len);

    printf("\r\nFB Width x Height : %dx%d@0x%08X\r\n", FB_WIDTH, FB_HEIGHT,
           FB_BASE_ADDR);

    if (!dotfont_initilized)
        dotfont_init();
}

void fb_clear()
{
    uint8_t *fb_ptr = NULL;
    uint32_t fb_len = 0;

    fb_ptr = (uint8_t *) FB_BASE_ADDR;
    fb_len = FB_WIDTH * FB_HEIGHT * sizeof(uint32_t);
    memset(fb_ptr, 0x00, fb_len);
}

void fb_close()
{
    uint8_t *fb_ptr = NULL;
    uint32_t fb_len = 0;

    video_framebuffer_vtg_enable_write(0);
    video_framebuffer_dma_enable_write(0);

    fb_ptr = (uint8_t *) FB_BASE_ADDR;
    fb_len = FB_WIDTH * FB_HEIGHT * sizeof(uint32_t);
    memset(fb_ptr, 0x00, fb_len);
}

int32_t
fb_fill_rect(uint32_t left, uint32_t top, uint32_t width, uint32_t height,
             uint32_t color)
{
    int32_t ret_val = 0;
    uint32_t i = 0;
    uint32_t *fb32_ptr = NULL;
    uint32_t fb_offset = 0;
    uint32_t bar_line[FB_WIDTH] = { 0 };

    width = (left + width) > FB_WIDTH ? (FB_WIDTH - left) : width;
    height = (top + height) > FB_HEIGHT ? (FB_HEIGHT - top) : height;

    for (i = 0; i < width; i++)
        bar_line[i] = color;

    fb_offset = top * FB_WIDTH + left;
    fb32_ptr = (uint32_t *) FB_BASE_ADDR;
    fb32_ptr = fb32_ptr + fb_offset;
    for (i = 0; i < height; i++) {
        memcpy((uint8_t *) fb32_ptr, (uint8_t *) bar_line,
               (width * sizeof(uint32_t)));
        fb32_ptr += FB_WIDTH;
    }

    return ret_val;
}

int32_t
fb_draw_rect(uint32_t left, uint32_t top, uint32_t width, uint32_t height,
             uint32_t color)
{
    int32_t ret_val = 0;
    uint32_t i = 0;
    uint32_t *fb32_ptr0 = NULL;
    uint32_t *fb32_ptr1 = NULL;
    uint32_t fb_offset = 0;

    width = (left + width) > FB_WIDTH ? (FB_WIDTH - left) : width;
    height = (top + height) > FB_HEIGHT ? (FB_HEIGHT - top) : height;

    fb32_ptr0 = (uint32_t *) FB_BASE_ADDR;
    fb32_ptr1 = (uint32_t *) FB_BASE_ADDR;
    fb_offset = top * FB_WIDTH + left;
    fb32_ptr0 = fb32_ptr0 + fb_offset;
    fb32_ptr1 = fb32_ptr1 + fb_offset + width;
    for (i = 0; i < height; i++) {
        *(fb32_ptr0) = color;
        *(fb32_ptr1) = color;
        fb32_ptr0 += FB_WIDTH;
        fb32_ptr1 += FB_WIDTH;
    }

    fb32_ptr1 = (uint32_t *) FB_BASE_ADDR;
    fb32_ptr0 = (uint32_t *) FB_BASE_ADDR;
    fb_offset = top * FB_WIDTH + left;
    fb32_ptr0 = fb32_ptr0 + fb_offset;
    fb_offset = (top + height - 1) * FB_WIDTH + left;
    fb32_ptr1 = fb32_ptr1 + fb_offset;
    for (i = 0; i < width; i++) {
        *(fb32_ptr0 + i) = color;
        *(fb32_ptr1 + i) = color;
    }

    return ret_val;
}

int32_t
fb_draw_line(uint32_t x0, uint32_t y0, uint32_t x1, uint32_t y1,
             uint32_t color, int32_t width)
{
    int32_t ret_val = 0;
    uint32_t start = 0;
    uint32_t stop = 0;
    uint32_t i = 0;
    uint32_t *fb32_ptr = NULL;
    uint32_t fb_offset = 0;
    int32_t dx = 0;
    int32_t dy = 0;
    int32_t d = 0;
    int32_t x_end = 0;
    int32_t x = 0;
    int32_t y = 0;
    int32_t x_Increment = 0;
    int32_t y_Increment = 0;
    int32_t flip = 0;


    dx = x1 - x0;
    dy = y1 - y0;
    fb32_ptr = (uint32_t *) FB_BASE_ADDR;

    if (dx == 0 && dy == 0) {   // single point
        fb_offset = y0 * FB_WIDTH + x0;
        *(fb32_ptr + fb_offset) = color;
    } else if (dx == 0) {       // vertical line
        start = y0 < y1 ? y0 : y1;
        stop = y0 < y1 ? y1 : y0;
        fb_offset = start * FB_WIDTH + x0;
        for (i = start; i <= stop; i++) {
            *(fb32_ptr + fb_offset) = color;
            fb_offset += FB_WIDTH;
        }
    } else if (dy == 0) {       // horizontal line
        start = x0 < x1 ? x0 : x1;
        stop = x0 < x1 ? x1 : x0;
        fb_offset = y0 * FB_WIDTH;
        fb32_ptr = fb32_ptr + fb_offset;
        for (i = start; i <= stop; i++) {
            *(fb32_ptr + i) = color;
        }
    } else {                    // other case
        if (x1 < x0) {
            x_end = x1;
            x1 = x0;
            x0 = x_end;
            x_end = y1;
            y1 = y0;
            y0 = x_end;
        }

        flip = 0;
        if (y1 < y0) {
            flip = 1;
            x_end = y1;
            y1 = y0;
            y0 = x_end;
        }

        x = x0;
        y = y0;
        x_end = x1;
        dx = x1 - x0;
        dy = y1 - y0;
        d = 2 * dy - dx;
        x_Increment = 2 * dy;
        y_Increment = 2 * (dy - dx);

        while (x <= x_end) {
            if (flip == 0)
                fb_offset = y * FB_WIDTH + x;
            else
                fb_offset = (y0 + y1 - y) * FB_WIDTH + x;

            *(fb32_ptr + fb_offset) = color;
            if (d <= 0) {
                d += x_Increment;
            } else {
                y++;
                d += y_Increment;
            }
            x++;
        }
    }

    return ret_val;
}

int32_t
fb_draw_buffer(uint32_t left, uint32_t top, uint32_t width,
               uint32_t height, const uint8_t * src_buff,
               uint32_t color_channels)
{
    int32_t ret_val = 0;
    uint32_t *fb32_ptr = NULL;
    uint8_t *dst_ptr = NULL;
    const uint8_t *src_ptr = NULL;
    uint32_t i = 0;
    uint32_t j = 0;


    if (src_buff == NULL) {
        ret_val = -1;
        return ret_val;
    }

    fb32_ptr = (uint32_t *) FB_BASE_ADDR;
    fb32_ptr += top * FB_WIDTH + left;

    dst_ptr = (uint8_t *) fb32_ptr;
    src_ptr = src_buff;

    switch (color_channels) {
    case 1:
        for (j = 0; j < height; j++) {
            for (i = 0; i < width; i++) {
                dst_ptr[4 * i + 0] = src_ptr[i];
                dst_ptr[4 * i + 1] = src_ptr[i];
                dst_ptr[4 * i + 2] = src_ptr[i];
            }
            src_ptr += (color_channels * width);
            dst_ptr += (sizeof(uint32_t) * FB_WIDTH);
        }
        break;

    case 3:
        for (j = 0; j < height; j++) {
            for (i = 0; i < width; i++) {
                dst_ptr[4 * i + 0] = src_ptr[3 * i + 0];
                dst_ptr[4 * i + 1] = src_ptr[3 * i + 1];
                dst_ptr[4 * i + 2] = src_ptr[3 * i + 2];
            }
            src_ptr += (color_channels * width);
            dst_ptr += (sizeof(uint32_t) * FB_WIDTH);
        }
        break;

    case 4:
        for (j = 0; j < height; j++) {
            // for pixel order adjust
            for (i = 0; i < width; i++) {
                dst_ptr[4 * i + 0] = src_ptr[4 * i + 0];
                dst_ptr[4 * i + 1] = src_ptr[4 * i + 1];
                dst_ptr[4 * i + 2] = src_ptr[4 * i + 2];
            }
            // if pixel order is the same, just memory copy
            //memcpy(dst_ptr, src_ptr, width);
            src_ptr += (color_channels * width);
            dst_ptr += (sizeof(uint32_t) * FB_WIDTH);
        }
        break;

    default:
        break;
    }

    return ret_val;
}

int32_t
fb_draw_string(uint32_t x, uint32_t y, uint32_t color, const char *msg_str)
{
    int32_t ret_val = 0;
    int32_t c_pos = 0;
    int32_t i = 0;
    int32_t j = 0;
    int32_t k = 0;
    int32_t l = 0;
    int32_t width = 0;
    int32_t height = 0;
    int32_t font_width = 0;
    int32_t font_height = 0;
    int32_t font_x_min = 0;
    int32_t font_y_min = 0;
    int32_t font_x_max = 0;
    int32_t font_y_max = 0;
    int32_t font_offset = 0;
    int8_t current_char = 0x00;
    uint32_t *dst_ptr = NULL;
    const uint8_t *font_data_ptr = NULL;
    struct font_basis *f_basis = NULL;

    if (!dotfont_initilized)
        dotfont_init();

    width = FB_WIDTH;
    height = FB_HEIGHT;
    dst_ptr = (uint32_t *) FB_BASE_ADDR;
    font_width = df_info.font_width;
    font_height = df_info.font_height;
    font_offset = font_width >> 3;

    c_pos = 0;
    font_y_min = y;
    font_y_max =
        ((int32_t) y + font_height) >
        height ? (height - (int32_t) y) : ((int32_t) y + font_height);

    while (1) {
        if (msg_str[c_pos] == 0x00)
            break;
        current_char = msg_str[c_pos];
        font_data_ptr =
            df_info.font_data + (current_char -
                                 ' ') * (font_height * font_offset);

        font_x_min = x + c_pos * font_width;
        font_x_max =
            (font_x_min + font_width) >
            width ? (height - font_x_min) : (font_x_min + font_width);
        font_x_max = (font_x_max >> 3) << 3;

        //printf("'%c':(%3d, %3d) - (%3d, %3d)\r\n", current_char, font_x_min, font_y_min, font_x_max, font_y_max);
        for (i = 0, j = font_y_min; j < font_y_max; j++, i += 2) {
            f_basis =
                (struct font_basis *)
                &df_info.f_basis[font_data_ptr[i + 0]];
            for (l = 0, k = 0; k < 8; k++, l++) {
                //printf("%d ", font_x_min + k);
                if (f_basis->data[l] == 'X')
                    *(dst_ptr + j * width + font_x_min + k) = color;
            }

            f_basis =
                (struct font_basis *)
                &df_info.f_basis[font_data_ptr[i + 1]];
            for (l = 0, k = 8; k < 16; k++, l++) {
                //printf("%d ", font_x_min + k);
                if (f_basis->data[l] == 'X')
                    *(dst_ptr + j * width + font_x_min + k) = color;
            }
        }
        c_pos++;
    }

    return ret_val;
}

void fb_fill(void)
{
    fb_fill_rect(0, 0, 320, 240, 0x00FF0000);
    fb_fill_rect(320, 240, 320, 240, 0x00FF0000);
    flush_cpu_dcache();
    flush_l2_cache();
}

void fb_draw(void)
{
    fb_draw_rect(0, 0, 320, 240, 0x00FFFF00);
    fb_draw_rect(320, 240, 320, 240, 0x00FF0000);
    flush_cpu_dcache();
    flush_l2_cache();
}

void fb_line(void)
{
    fb_draw_line(50, 50, 50, 50, 0x000000FF, 1);
    fb_draw_line(100, 0, 100, 100, 0x00000FFF, 1);
    fb_draw_line(0, 100, 100, 100, 0x0000FFFF, 1);
    fb_draw_line(0, 0, 320, 240, 0x000FFFFF, 1);
    fb_draw_line(0, 240, 320, 0, 0x00FFFFFF, 1);
    flush_cpu_dcache();
    flush_l2_cache();
}

void fb_msg(void)
{
    static uint32_t x = 0;
    static uint32_t color = 0x00889922;

    fb_draw_string(0, x, color, "Hello CFU Playground!!");
    x = (x > FB_HEIGHT) ? 0 : (x + 16);
    if (x == 0)
        fb_clear();
    color += 0x1234;
    flush_cpu_dcache();
    flush_l2_cache();
}

/*
void fb_buff(void) {
    fb_draw_buffer(200, 200, 160, 160, (const uint8_t *)image_buff, 3);
}
*/


static struct Menu MENU = {
    "Framebuffer Debugging Menu",
    "framebuffer",
    {
     MENU_ITEM('i', "framebuffer initial", fb_init),
     MENU_ITEM('c', "framebuffer clear", fb_clear),
     MENU_ITEM('f', "fill rectangle", fb_fill),
     MENU_ITEM('d', "draw rectangle", fb_draw),
     MENU_ITEM('l', "draw line", fb_line),
     MENU_ITEM('m', "draw message", fb_msg),
     //MENU_ITEM('b', "draw buffer", fb_buff),
     MENU_END,
      },
};

void framebuffer_menu(void)
{
    menu_run(&MENU);
}

#else

void framebuffer_menu(void)
{

}

#endif
