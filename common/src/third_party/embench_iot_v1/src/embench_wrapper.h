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

#define EMBENCH_WRAPPER_PROTOTYPE(benchname) \
void embench_wrapper_##benchname (); 

#ifndef _EMBENCH_WRAPPER_H
#define _EMBENCH_WRAPPER_H

#ifdef __cplusplus
extern "C" {
#endif

#if defined(INCLUDE_EMBENCH_PRIMECOUNT) || defined(INCLUDE_ALL_EMBENCH_EXAMPLES)
    EMBENCH_WRAPPER_PROTOTYPE(primecount)
#endif
#if defined(INCLUDE_EMBENCH_MINVER) || defined(INCLUDE_ALL_EMBENCH_EXAMPLES)
    EMBENCH_WRAPPER_PROTOTYPE(minver)
#endif

#ifdef __cplusplus
}
#endif

#endif  // _EMBENCH_WRAPPER_H
