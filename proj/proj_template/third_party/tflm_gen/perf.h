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

#ifndef CFU_PLAYGROUND_PERF_H_
#define CFU_PLAYGROUND_PERF_H_


#define NUM_PERF_COUNTERS 8


inline unsigned get_mcycle()
{
        unsigned result;
        asm volatile ("csrr %0, mcycle" : "=r"(result));
        return result;
}

inline void set_mcycle(unsigned cyc)
{
        asm volatile ("csrw mcycle, %0" :: "r"(cyc));
}


inline unsigned get_counter(int counter_num)
{
        unsigned count=0;
        switch (counter_num) {
            case 0: asm volatile ("csrr %0, 0xB04" : "=r"(count)); break;
            case 1: asm volatile ("csrr %0, 0xB06" : "=r"(count)); break;
            case 2: asm volatile ("csrr %0, 0xB08" : "=r"(count)); break;
            case 3: asm volatile ("csrr %0, 0xB0A" : "=r"(count)); break;
            case 4: asm volatile ("csrr %0, 0xB0C" : "=r"(count)); break;
            case 5: asm volatile ("csrr %0, 0xB0E" : "=r"(count)); break;
            case 6: asm volatile ("csrr %0, 0xB10" : "=r"(count)); break;
            case 7: asm volatile ("csrr %0, 0xB12" : "=r"(count)); break;
            default: ;
        }
        return count;
}

inline unsigned get_counter_enable(int counter_num)
{
        unsigned en=0;
        switch (counter_num) {
            case 0: asm volatile ("csrr %0, 0xB05" : "=r"(en)); break;
            case 1: asm volatile ("csrr %0, 0xB07" : "=r"(en)); break;
            case 2: asm volatile ("csrr %0, 0xB09" : "=r"(en)); break;
            case 3: asm volatile ("csrr %0, 0xB0B" : "=r"(en)); break;
            case 4: asm volatile ("csrr %0, 0xB0D" : "=r"(en)); break;
            case 5: asm volatile ("csrr %0, 0xB0F" : "=r"(en)); break;
            case 6: asm volatile ("csrr %0, 0xB11" : "=r"(en)); break;
            case 7: asm volatile ("csrr %0, 0xB13" : "=r"(en)); break;
            default: ;
        }
        return en;
}

inline void set_counter(int counter_num, unsigned count)
{
        switch (counter_num) {
            case 0: asm volatile ("csrw 0xB04, %0" :: "r"(count)); break;
            case 1: asm volatile ("csrw 0xB06, %0" :: "r"(count)); break;
            case 2: asm volatile ("csrw 0xB08, %0" :: "r"(count)); break;
            case 3: asm volatile ("csrw 0xB0A, %0" :: "r"(count)); break;
            case 4: asm volatile ("csrw 0xB0C, %0" :: "r"(count)); break;
            case 5: asm volatile ("csrw 0xB0E, %0" :: "r"(count)); break;
            case 6: asm volatile ("csrw 0xB10, %0" :: "r"(count)); break;
            case 7: asm volatile ("csrw 0xB12, %0" :: "r"(count)); break;
            default: ;
        }
}

inline void set_counter_enable(int counter_num, unsigned en)
{
        switch (counter_num) {
            case 0: asm volatile ("csrw 0xB05, %0" :: "r"(en)); break;
            case 1: asm volatile ("csrw 0xB07, %0" :: "r"(en)); break;
            case 2: asm volatile ("csrw 0xB09, %0" :: "r"(en)); break;
            case 3: asm volatile ("csrw 0xB0B, %0" :: "r"(en)); break;
            case 4: asm volatile ("csrw 0xB0D, %0" :: "r"(en)); break;
            case 5: asm volatile ("csrw 0xB0F, %0" :: "r"(en)); break;
            case 6: asm volatile ("csrw 0xB11, %0" :: "r"(en)); break;
            case 7: asm volatile ("csrw 0xB13, %0" :: "r"(en)); break;
            default: ;
        }
}

inline void enable_counter(int counter_num)
{
        set_counter_enable(counter_num, 1);
}

inline void disable_counter(int counter_num)
{
        set_counter_enable(counter_num, 0);
}


#endif  // CFU_PLAYGROUND_PERF_H_
