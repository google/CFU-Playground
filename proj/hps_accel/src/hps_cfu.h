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
#ifndef _HPS_CFU_H
#define _HPS_CFU_H

#include "cfu.h"
#include "gateware_constants.h"

// Convenience macros for get/set
#define cfu_set(reg, val) cfu_op(INS_SET, reg, val, 0)
#define cfu_setx(reg, val1, val2) cfu_op(INS_SET, reg, val1, val2)
#define cfu_get(reg) cfu_op(INS_GET, reg, 0, 0)

// Ping instructions for checking CFU is available
#define cfu_ping(val1, val2) cfu_op(INS_PING, 0, val1, val2)

#endif  // _HPS_CFU_H
