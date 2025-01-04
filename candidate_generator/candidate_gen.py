# src/generator/candidate_gen.py
from typing import Dict, List, Optional
import re
import logging

import os


class CandidateGenerator:
    def __init__(self):
        self.logger = logging.getLogger(__name__)

    def generate_driver(self, llm_response: str, api_info: Dict) -> Optional[str]:
        """
        从LLM响应生成fuzzing驱动代码

        Args:
            llm_response: LLM生成的原始代码响应
            api_info: API相关信息字典

        Returns:
            str: 处理后的fuzzing驱动代码
        """
        try:
            # 提取代码部分
            code = self._extract_code(llm_response)
            if not code:
                return None

            # 添加必要的头文件
            code = self._add_headers(code, api_info)

            # 确保存在LLVMFuzzerTestOneInput函数
            code = self._ensure_fuzzer_entry(code)

            # 添加错误处理和资源清理
            code = self._add_error_handling(code)

            # 格式化代码
            code = self._format_code(code)

            # 将代码写入文件
            output_path = '../outputs/temp/candidate_fuzz_drivers/raw.c'
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            with open(output_path, 'w') as file:
                file.write(code)

            return code

        except Exception as e:
            self.logger.error(f"Error generating driver: {str(e)}")
            return None

    # 其他方法保持不变

    def _extract_code(self, llm_response: str) -> Optional[str]:
        """提取LLM响应中的代码部分"""
        code_pattern = r"```(?:cpp|c)?\s*([\s\S]*?)\s*```"
        matches = re.findall(code_pattern, llm_response)
        return matches[0] if matches else llm_response

    def _add_headers(self, code: str, api_info: Dict) -> str:
        """添加必要的头文件"""
        headers = """
#include <stdint.h>
#include <stddef.h>
#include <stdlib.h>
#include <string.h>
"""
        # 添加项目特定的头文件
        # for header in api_info.get('required_headers', []):
        #     headers += f'#include "{header}"\n'

        return headers + "\n" + code

    def _ensure_fuzzer_entry(self, code: str) -> str:
        """确保代码包含LLVMFuzzerTestOneInput入口函数"""
        if 'LLVMFuzzerTestOneInput' not in code:
            entry_function = """
extern "C" int LLVMFuzzerTestOneInput(const uint8_t *data, size_t size) {
    // Add fuzzing logic here
    return 0;
}
"""
            code += "\n" + entry_function
        return code

    def _add_error_handling(self, code: str) -> str:
        """添加错误处理和资源清理代码"""
        # 添加全局错误处理宏
        error_handling = """
#define CHECK_NULL(ptr) if (ptr == NULL) { return 0; }
#define CLEANUP_AND_RETURN(code) { cleanup(); return code; }

static void cleanup() {
    // Add cleanup logic here
}
"""
        return error_handling + "\n" + code

    def _format_code(self, code: str) -> str:
        """格式化代码，确保一致的风格"""
        # 移除多余的空行
        code = re.sub(r'\n\s*\n', '\n\n', code)

        # 确保正确的大括号样式
        code = re.sub(r'\)\s*\n\s*{', ') {', code)

        return code

    def generate_multiple_variants(self, llm_response: str, api_info: Dict, num_variants: int = 3) -> List[str]:
        """生成多个驱动变体"""
        variants = []
        base_driver = self.generate_driver(llm_response, api_info)

        if base_driver:
            variants.append(base_driver)

            # 生成不同的变体
            for i in range(1, num_variants):
                variant = self._create_variant(base_driver, i)
                if variant:
                    variants.append(variant)

        return variants

    def _create_variant(self, base_driver: str, variant_num: int) -> Optional[str]:
        """创建驱动代码的变体"""
        try:
            # 根据变体号添加不同的模糊测试策略
            strategies = [
                self._add_mutation_strategy,
                self._add_structure_aware_strategy,
                self._add_dictionary_strategy
            ]

            if variant_num <= len(strategies):
                return strategies[variant_num - 1](base_driver)

            return None

        except Exception as e:
            self.logger.error(f"Error creating variant {variant_num}: {str(e)}")
            return None

    def _add_mutation_strategy(self, code: str) -> str:
        """添加基本的变异策略"""
        mutation_code = """
    // Basic mutation strategy
    if (size >= 4) {
        uint32_t* ptr = (uint32_t*)data;
        *ptr = *ptr ^ 0xFFFFFFFF;  // Bit flipping
    }
"""
        return self._insert_into_fuzzer_function(code, mutation_code)

    def _add_structure_aware_strategy(self, code: str) -> str:
        """添加结构感知的策略"""
        structure_code = """
    // Structure-aware strategy
    struct FuzzInput {
        uint32_t magic;
        uint16_t length;
        uint8_t type;
        uint8_t data[];
    };

    if (size >= sizeof(struct FuzzInput)) {
        struct FuzzInput* input = (struct FuzzInput*)data;
        if (input->magic == 0x46555A5A) {  // "FUZZ"
            // Process structured input
        }
    }
"""
        return self._insert_into_fuzzer_function(code, structure_code)

    def _add_dictionary_strategy(self, code: str) -> str:
        """添加字典策略"""
        dictionary_code = """
    // Dictionary-based strategy
    static const uint8_t dict[] = {
        0xFF, 0x00, 0x55, 0xAA,  // Common magic values
        0x7F, 0xFF, 0xFF, 0xFF   // MAX_INT
    };

    if (size >= sizeof(dict)) {
        memcpy((void*)data, dict, sizeof(dict));
    }
"""
        return self._insert_into_fuzzer_function(code, dictionary_code)

    def _insert_into_fuzzer_function(self, code: str, insert_code: str) -> str:
        """在LLVMFuzzerTestOneInput函数中插入代码"""
        fuzzer_pattern = r'(LLVMFuzzerTestOneInput\s*\([^)]*\)\s*{)'
        return re.sub(fuzzer_pattern, f'\\1\n{insert_code}', code)


if __name__ == "__main__":
    # Example usage
    llm_response = """
```cpp
extern "C" {
    int LLVMFuzzerTestOneInput(const uint8_t *Data, size_t Size);

    /* 
    * Declare and initialize components to handle functions 
    * This examples will only contain the skeletons required to create a fuzzer
    */

    // Function Declarations
    void usage(FILE * stderr, const char * parameter);
    void *__errno_location(void);
    int parseInteger(const char*, const char*, unsigned long, unsigned long);
    int skipArgs(const char*);
    void xmlMemSetup(void (*)(void *), void *(*)(size_t), void *(*)(void *, size_t), char *(*)(const char *));
    void xmlSetExternalEntityLoader(<dependent type>);
    void startTimer(void);
    void testSAX(const char*);
    void endTimer(char *, int);
    void xmlCleanupParser(void);

    // Generate the Mock Functions

    void myFreeFunc(void *Ptr) { free(Ptr); }
    void *myMallocFunc(size_t Size) { return malloc(Size); }
    void *myReallocFunc(void *Ptr, size_t Size) { return realloc(Ptr, Size); }
    char *myStrdupFunc(const char *Str) { return strdup(Str); }

    <dependent type> xmllintExternalEntityLoader;
}

int LLVMFuzzerTestOneInput(const uint8_t *Data, size_t Size) {
    if (Size < 3) return 0;  // Ensure there is enough data provided

    char* NewData = (char*)malloc(Size+1);  // Create space for data copy
    memcpy(NewData, Data, Size);            // Copy data
    NewData[Size] = '\0';                   // Null-terminate the string

    /* 
    * Function Calls Here - pass fuzzed data.
    * New data or part of it can be passed to the functions as required.
    */

    usage(NULL, NewData);  // Mock function without actual definition here

    __errno_location();

    int result  = sscanf(NewData, "%u", &val);
    if (result > 0) // check to make sure a number was actually found in the data
        parseInteger("maxmem", NewData, 0, INT_MAX);

    skipArgs(NewData);

    xmlMemSetup(myFreeFunc, myMallocFunc, myReallocFunc, myStrdupFunc);

    // the procedure for xmlSetExternalEntityLoader function will be similar after appropriate extraction of right type from the NewData

    startTimer();

    testSAX(NewData);

    endTimer("%d iterations", 1);

    xmlCleanupParser();

    free(NewData); // Always clean up created data to avoid any memory leaks

    return 0;  // Non-zero return values are reserved for future use.
}
```
Please note that:
- Before using this code, you need to fill in the correct dependent type and implementation of `xmlSetExternalEntityLoader` and `xmllintExternalEntityLoader`.
- Also, this code assumes that implementations of all these functions are written somewhere in your code or module.
- The example does not cover wrapping up C functions in extern "C" in C++ code, please do so if you use C++ instead of C.
"""
    api_info = {
        "required_headers": ["my_header.h"]
    }

    generator = CandidateGenerator()
    driver_code = generator.generate_driver(llm_response, api_info)
    print(driver_code)
    # variants = generator.generate_multiple_variants(llm_response, api_info)
    # for i, variant in enumerate(variants):
    #     print(f"Variant {i + 1}:\n{variant}")