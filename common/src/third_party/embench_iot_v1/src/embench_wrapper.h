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
#if defined(INCLUDE_EMBENCH_AHA_MONT64) || defined(INCLUDE_ALL_EMBENCH_EXAMPLES)
    EMBENCH_WRAPPER_PROTOTYPE(aha_mont64)
#endif
#if defined(INCLUDE_EMBENCH_CRC_32) || defined(INCLUDE_ALL_EMBENCH_EXAMPLES)
    EMBENCH_WRAPPER_PROTOTYPE(crc_32)
#endif
#if defined(INCLUDE_EMBENCH_CUBIC) || defined(INCLUDE_ALL_EMBENCH_EXAMPLES)
    EMBENCH_WRAPPER_PROTOTYPE(cubic)
#endif
#if defined(INCLUDE_EMBENCH_EDN) || defined(INCLUDE_ALL_EMBENCH_EXAMPLES)
    EMBENCH_WRAPPER_PROTOTYPE(edn)
#endif
#if defined(INCLUDE_EMBENCH_HUFFBENCH) || defined(INCLUDE_ALL_EMBENCH_EXAMPLES)
    EMBENCH_WRAPPER_PROTOTYPE(huffbench)
#endif
#if defined(INCLUDE_EMBENCH_MATMUL) || defined(INCLUDE_ALL_EMBENCH_EXAMPLES)
    EMBENCH_WRAPPER_PROTOTYPE(matmul)
#endif
#if defined(INCLUDE_EMBENCH_MD5) || defined(INCLUDE_ALL_EMBENCH_EXAMPLES)
    EMBENCH_WRAPPER_PROTOTYPE(md5)
#endif
#if defined(INCLUDE_EMBENCH_NBODY) || defined(INCLUDE_ALL_EMBENCH_EXAMPLES)
    EMBENCH_WRAPPER_PROTOTYPE(nbody)
#endif
#if defined(INCLUDE_EMBENCH_NETTLE_AES) || defined(INCLUDE_ALL_EMBENCH_EXAMPLES)
    EMBENCH_WRAPPER_PROTOTYPE(nettle_aes)
#endif
#if defined(INCLUDE_EMBENCH_NETTLE_SHA256) || defined(INCLUDE_ALL_EMBENCH_EXAMPLES)
    EMBENCH_WRAPPER_PROTOTYPE(nettle_sha256)
#endif
#if defined(INCLUDE_EMBENCH_NSICHNEU) || defined(INCLUDE_ALL_EMBENCH_EXAMPLES)
    EMBENCH_WRAPPER_PROTOTYPE(nsichneu)
#endif
#if defined(INCLUDE_EMBENCH_PICOJPEG) || defined(INCLUDE_ALL_EMBENCH_EXAMPLES)
    EMBENCH_WRAPPER_PROTOTYPE(picojpeg)
#endif
#if defined(INCLUDE_EMBENCH_QRDUINO) || defined(INCLUDE_ALL_EMBENCH_EXAMPLES)
    EMBENCH_WRAPPER_PROTOTYPE(qrduino)
#endif
#if defined(INCLUDE_EMBENCH_SLRE) || defined(INCLUDE_ALL_EMBENCH_EXAMPLES)
    EMBENCH_WRAPPER_PROTOTYPE(slre)
#endif
#if defined(INCLUDE_EMBENCH_ST) || defined(INCLUDE_ALL_EMBENCH_EXAMPLES)
    EMBENCH_WRAPPER_PROTOTYPE(st)
#endif
#if defined(INCLUDE_EMBENCH_STATEMATE) || defined(INCLUDE_ALL_EMBENCH_EXAMPLES)
    EMBENCH_WRAPPER_PROTOTYPE(statemate)
#endif
#if defined(INCLUDE_EMBENCH_TARFIND) || defined(INCLUDE_ALL_EMBENCH_EXAMPLES)
    EMBENCH_WRAPPER_PROTOTYPE(tarfind)
#endif
#if defined(INCLUDE_EMBENCH_UD) || defined(INCLUDE_ALL_EMBENCH_EXAMPLES)
    EMBENCH_WRAPPER_PROTOTYPE(ud)
#endif
#if defined(INCLUDE_EMBENCH_WIKISORT) || defined(INCLUDE_ALL_EMBENCH_EXAMPLES)
    EMBENCH_WRAPPER_PROTOTYPE(wikisort)
#endif
#ifdef __cplusplus
}
#endif

#endif  // _EMBENCH_WRAPPER_H
