#include "libxml/parser.h"
#include "libxml/tree.h"
#include "libxml/xmlmemory.h"
#include "libxml/xmlschemas.h"
#include <stdlib.h>
#include <string.h>
#include <stdint.h>

void* myMallocFunc(size_t size) {
    return malloc(size);
}

void* myReallocFunc(void* ptr, size_t size) {
    return realloc(ptr, size);
}

void myFreeFunc(void* ptr) {
    free(ptr);
}

char* myStrdupFunc(const char* str) {
    // Check if strdup is available on the system
    size_t len = strlen(str) + 1;
    char* copy = malloc(len);
    if (copy) {
        memcpy(copy, str, len);
    }
    return copy;
}

// LibFuzzer 测试入口
int LLVMFuzzerTestOneInput(const uint8_t* data, size_t size) {
    if (data == NULL || size == 0) {
        return 0;
    }

    // 配置 XML 的内存管理器
    xmlMemSetup(myFreeFunc, myMallocFunc, myReallocFunc, myStrdupFunc);

    // 将输入数据转换为字符串
    char* fuzzInput = malloc(size + 1);
    if (!fuzzInput) {
        return 0;
    }
    memcpy(fuzzInput, data, size);
    fuzzInput[size] = '\0';

    // 解析 XML 输入
    xmlDocPtr doc = xmlParseMemory(fuzzInput, size);
    if (doc) {
        xmlFreeDoc(doc);
    }

    free(fuzzInput);
    xmlCleanupParser();

    return 0;
}
