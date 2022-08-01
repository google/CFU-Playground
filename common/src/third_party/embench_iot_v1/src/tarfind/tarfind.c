/*
 * This benchmark simulates the search in a TAR archive
 * for a set of filenames
 *
 * Created by Julian Kunkel for Embench-iot
 * Licensed under MIT
 */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>

#include "third_party/embench_iot_v1/support/support.h"

#define LOCAL_SCALE_FACTOR 47

// number of files in the archive
#define ARCHIVE_FILES 35

#define N_SEARCHES 5

/* BEEBS heap is just an array */
/* 8995 = sizeof(tar_header_t) * ARCHIVE_FILES */
#define roundup(d, u) ((((d)+(u))/(u))*(u))
#define HEAP_SIZE roundup(8995, sizeof(void *))
static char heap[HEAP_SIZE];

void
initialise_benchmark_tarfind (void)
{
}


static int benchmark_body_tarfind (int rpt);

void
warm_caches_tarfind (int  heat)
{
  benchmark_body_tarfind (heat);
  return;
}


int
benchmark_tarfind (void)
{
  return benchmark_body_tarfind (LOCAL_SCALE_FACTOR * CPU_MHZ);
}

// this is the basic TAR header format which is in ASCII
typedef struct {
  char filename[100];
  char mode[8];  // file mode
  char uID[8];   // user id
  char gID[8];   // group id
  char size[12]; // in bytes octal base
  char mtime[12]; // numeric Unix time format (octal)
  char checksum[8]; // for the header, ignored herew2
  char isLink;
  char linkedFile[100];
} tar_header_t;


static int __attribute__ ((noinline))
benchmark_body_tarfind (int rpt)
{
  int i, j, p;
  tar_header_t * hdr;
  int found;

  for (j = 0; j < rpt; j++) {
    init_heap_beebs ((void *) heap, HEAP_SIZE);

    // always create ARCHIVE_FILES files in the archive
    int files = ARCHIVE_FILES;
    hdr = malloc_beebs(sizeof(tar_header_t) * files);
    for (i = 0; i < files; i++){
      // create record
      tar_header_t * c = & hdr[i];
      // initialize here for cache efficiency reasons
      memset(c, 0, sizeof(tar_header_t));
      int flen = 5 + i % 94; // vary file lengths
      c->isLink = '0';
      for(p = 0; p < flen; p++){
        c->filename[p] = rand_beebs() % 26 + 65;
      }
      c->size[0] = '0';
    }

    found = 0; // number of times a file was found
    // actual benchmark, strcmp with a set of N_SEARCHES files
    // the memory access here is chosen inefficiently on purpose
    for (p = 0; p < N_SEARCHES; p++){
      // chose the position of the file to search for from the mid of the list
      char * search = hdr[(p + ARCHIVE_FILES/2) % ARCHIVE_FILES].filename;

      // for each filename iterate through all files until found
      for (i = 0; i < files; i++){
        /*tar_header_t * cur = & hdr[i]; Unused variable */
        // implementation of strcmp
        char *c1;
        char *c2;
        for (c1 = hdr[i].filename, c2 = search; (*c1 != '\0' && *c2 != '\0' && *c1 == *c2) ; c1++, c2++);
        // complete match?
        if(*c1 == '\0' && *c2 == '\0'){
          found++;
          break;
        }
      }
    }
    free_beebs(hdr);
  }

  return found == N_SEARCHES;
}


int
verify_benchmark_tarfind (int r)
{
  return r == 1;
}
