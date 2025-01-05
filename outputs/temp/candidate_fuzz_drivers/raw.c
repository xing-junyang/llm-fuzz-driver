
#define CHECK_NULL(ptr) if (ptr == NULL) { return 0; }
#define CLEANUP_AND_RETURN(code) { cleanup(); return code; }

static void cleanup() {
    // Add cleanup logic here
}

#include <stdint.h>
#include <stddef.h>
#include <stdlib.h>
#include <string.h>

#include <stdlib.h>
#include <string.h>
#include <libxml/xmlmemory.h>
#include <libxml/parser.h>

// Define your custom functions
void myFreeFunc(void *mem) {
    free(mem);
}

char *myStrdupFunc(const char *str) {
    return strdup(str);
}

xmlExternalEntityLoader myEntityLoaderFunc(const char *URL, const char *ID, xmlParserCtxtPtr context) {
    // Your implementation here
    return NULL;
}

int LLVMFuzzerTestOneInput(const uint8_t* data, size_t size) {
    // Check if data is NULL or size is zero
    if (data == NULL || size == 0) {
        return 0;
    }

    // Copy data to a new null-terminated string
    char *testString = malloc(size + 1);
    memcpy(testString, data, size);
    testString[size] = '\0';  // Null-terminate the string

    // Feed the functions with the fuzzer-generated string
    xmlMemSetup(myFreeFunc, malloc, realloc, myStrdupFunc);
    xmlSetExternalEntityLoader(myEntityLoaderFunc);  
    xmlCleanupParser();

    free(testString);
    return 0;
}