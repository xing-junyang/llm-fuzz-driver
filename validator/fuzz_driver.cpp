
#define CHECK_NULL(ptr) if (ptr == NULL) { return 0; }
#define CLEANUP_AND_RETURN(code) { cleanup(); return code; }

static void cleanup() {
    // Add cleanup logic here
}

#include <stdint.h>
#include <stddef.h>
#include <stdlib.h>
#include <string.h>

#include <algorithm>
#include <cstdint>
#include <stdio.h>
#include <jpeglib.h>
#include <setjmp.h>

extern "C" int LLVMFuzzerTestOneInput(const uint8_t *data, size_t size) {

    if (size < 1) {
        return 0;
    }

    struct jpeg_decompress_struct cinfo;
    struct jpeg_error_mgr jerr;

    cinfo.err = jpeg_std_error(&jerr);
    jpeg_create_decompress(&cinfo);

    jpeg_mem_src(&cinfo, data, size);

    jpeg_read_header(&cinfo, TRUE);

    jpeg_destroy_decompress(&cinfo);

    return 0;
}