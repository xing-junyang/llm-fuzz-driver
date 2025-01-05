#include <stdlib.h>
#include <string.h>
//add testfunction lib

// LibFuzzer 测试入口
int LLVMFuzzerTestOneInput(const uint8_t* data, size_t size) {
    if (data == NULL || size == 0) {
        return 0;
    }

    return 0;
}
