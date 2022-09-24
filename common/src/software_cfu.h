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

#ifndef SOFTWARE_CFU_H
#define SOFTWARE_CFU_H

#include <stdint.h>

#ifdef __cplusplus
extern "C" {
#endif


// =============== Software implementation of custom op codes
uint32_t software_cfu(int funct3, int funct7, uint32_t rs1, uint32_t rs2);


#ifdef __cplusplus
}
#endif

#endif  // SOFTWARE_CFU_H
