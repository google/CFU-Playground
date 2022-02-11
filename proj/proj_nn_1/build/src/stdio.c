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

/* Currently, we use libc++ from the toolchain. This library expects
   readchar and putsnonl to be symbols, while picolibc defines those
   as macros. The following code works sround this */

#undef readchar
#undef putsnonl

extern int readchar_nonblock(void);

char readchar(void)
{
  return (char) getchar();
}

void putsnonl(const char *s)
{
  while(*s) {
    putchar(*s);
    s++;
  }
}
