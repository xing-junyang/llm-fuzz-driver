# src/generator/candidate_gen.py
from typing import Dict, List, Optional
import re
import logging


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

            return code

        except Exception as e:
            self.logger.error(f"Error generating driver: {str(e)}")
            return None

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
        for header in api_info.get('required_headers', []):
            headers += f'#include "{header}"\n'

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
为了生成一个测试驱动（fuzz target）用于与 libfuzzer 一起使用，你需要编写一个函数，该函数接收一个字节序列作为输入，并将其传递给你想要测试的函数。下面是一个简单的测试驱动示例，它将与上面的 `string_to_int` 函数一起使用。

```cpp
// my_fuzz_target.cpp
#include <cstdint>
#include <cstddef>
#include <string>
#include "my_source.cpp"  // 包含上面提供的 string_to_int 函数

// 这个函数是 libfuzzer 调用的目标函数
// 它接收一个字节序列，并尝试将其转换为字符串，然后传递给 string_to_int 函数
extern "C" int LLVMFuzzerTestOneInput(const uint8_t *data, size_t size) {
    // 确保输入数据不为空
    if (size == 0) {
        return 0;
    }

    // 将输入数据转换为字符串
    // 注意：这里简单地将字节序列转换为字符串，没有进行任何错误检查
    // 在实际应用中，你可能需要更复杂的处理来确保输入是有效的
    std::string input(reinterpret_cast<const char*>(data), size);

    // 尝试调用 string_to_int 函数
    try {
        int result = string_to_int(input);
        // 这里可以添加额外的逻辑来验证结果或进行其他操作
        // 例如，检查 result 是否在预期的范围内
    } catch (const std::exception& e) {
        // 捕获并处理异常，例如打印错误信息
        std::cerr << "Exception caught: " << e.what() << std::endl;
    }

    // 返回 0 表示测试用例被认为是有效的，但未发现错误
    return 0;
}
```

要编译这个测试驱动并链接 libfuzzer，你可以使用以下命令：

```bash
clang++ -fsanitize=fuzzer,address -o my_fuzz_target my_fuzz_target.cpp my_source.cpp
```

这里使用了 `-fsanitize=fuzzer,address` 选项，它不仅启用了 fuzzer，还启用了地址sanitizer，这有助于检测内存错误。

一旦编译完成，你就可以运行生成的可执行文件，并让 libfuzzer 开始模糊测试：

```bash
./my_fuzz_target
```

libfuzzer 将自动生成随机输入并传递给 `LLVMFuzzerTestOneInput` 函数。如果 `string_to_int` 函数抛出异常或导致其他错误，libfuzzer 将捕获这些错误，并可能发现潜在的问题。
"""
    api_info = {
        "required_headers": ["my_header.h"]
    }

    generator = CandidateGenerator()
    driver_code = generator.generate_driver(llm_response, api_info)
    print(driver_code)
    variants = generator.generate_multiple_variants(llm_response, api_info)
    for i, variant in enumerate(variants):
        print(f"Variant {i + 1}:\n{variant}")