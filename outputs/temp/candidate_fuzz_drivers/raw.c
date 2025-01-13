
#include <libxml/parser.h>
#include <libxml/xmlmemory.h>
#include <stdint.h>
#include <stddef.h>
#include <stdlib.h>
#include <string.h>

#define CHECK_NULL(ptr) if (ptr == NULL) { return 0; }
#define CLEANUP_AND_RETURN(code) { cleanup(); return code; }

static void cleanup() {
    // Add cleanup logic here
}

void myFreeFunc(void *mem) {
    free(mem);
}

char* myStrdupFunc(const char *str) {
    char *copy = (char *)malloc(strlen(str) + 1);
    if (copy) {
        strcpy(copy, str);
    }
    return copy;
}

int LLVMFuzzerTestOneInput(const uint8_t* data, size_t size) {
    if (data == NULL || size == 0) {
        CLEANUP_AND_RETURN(0);
    }

    // Create a copy of the data as a null-terminated string
    char* null_terminated_data = (char*)malloc(size + 1);
    if (null_terminated_data == NULL) {
        CLEANUP_AND_RETURN(0);
    }
    memcpy(null_terminated_data, data, size);
    null_terminated_data[size] = '\0';

    // Use first byte of data to switch between different functions to be fuzzed
    switch (data[0] % 4) { // Increase number of cases
        case 0:
            xmlMemSetup(myFreeFunc, malloc, realloc, myStrdupFunc);
            break;
        case 1:
            xmlSetExternalEntityLoader(xmlNoNetExternalEntityLoader);
            break;
        case 2:
            {
                xmlParserCtxtPtr ctxt = xmlCreateDocParserCtxt(BAD_CAST null_terminated_data);
                if (ctxt != NULL) {
                    xmlParseDocument(ctxt);
                    xmlFreeDoc(ctxt->myDoc);
                    xmlFreeParserCtxt(ctxt);
                }
            }
            break;
        case 3: 
            { 
                char *dup_val = myStrdupFunc(null_terminated_data); 
                myFreeFunc(dup_val); 
            } 
            break; 
    }

    xmlCleanupParser();
    free(null_terminated_data);
    CLEANUP_AND_RETURN(0);
}