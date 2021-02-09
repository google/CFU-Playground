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
        unsigned count;

        if (counter_num == 0) asm volatile ("csrr %0, 0xB04" : "=r"(count));
                         else asm volatile ("csrr %0, 0xB06" : "=r"(count));

        return count;
}

inline unsigned get_counter_enable(int counter_num)
{
        unsigned en;

        if (counter_num == 0) asm volatile ("csrr %0, 0xB05" : "=r"(en));
                         else asm volatile ("csrr %0, 0xB07" : "=r"(en));

        return en;
}

inline void set_counter(int counter_num, unsigned count)
{
        if (counter_num == 0) asm volatile ("csrw 0xB04, %0" :: "r"(count));
                         else asm volatile ("csrw 0xB06, %0" :: "r"(count));
}

inline void set_counter_enable(int counter_num, unsigned en)
{
        if (counter_num == 0) asm volatile ("csrw 0xB05, %0" :: "r"(en));
                         else asm volatile ("csrw 0xB07, %0" :: "r"(en));
}


