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

    def _extract_code(self, llm_response: str) -> Optional[str]:
        """提取LLM响应中的代码部分"""
        code_pattern = r"```(?:cpp|c|C)?\s*([\s\S]*?)\s*```"
        matches = re.findall(code_pattern, llm_response)
        return matches[0] if matches else llm_response

    def _add_headers(self, code: str, api_info: Dict) -> str:
        """添加必要的头文件"""
        headers = """"""
        # 添加项目特定的头文件
        required_headers = [
            "#include <stdint.h>",
            "#include <stddef.h>",
            "#include <stdlib.h>",
            "#include <string.h>"
        ]

        # 检查是否已经存在头文件
        for header in required_headers:
            if header not in code:
                headers += f"{header}\n"

        # 添加项目特定的头文件
        # for header in api_info.get('required_headers', []):
        #     if f'#include "{header}"' not in code:
        #         headers += f'#include "{header}"\n'

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
        if(error_handling not in code):
            code =error_handling+"\n"+code
        return code

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
To create a test driver program, you would have to properly implement all the functions and calls as needed by your project. Below is an example of how such a driver could look like. Please note that due to the specificity and the complexity of the issue, the code provided might need extensive adaptations to reflect correctly your environment. 

```c

#define CHECK_NULL(ptr) if (ptr == NULL) { return 0; }
#define CLEANUP_AND_RETURN(code) { cleanup(); return code; }

static void cleanup() {
    // Add cleanup logic here
}

#include <stdint.h>
#include <stddef.h>

#include <stdlib.h>
#include <string.h>
#include <jerror.h>

// add custom headers
#include "jpeglib.h"
#include "jconfig.h"

#define MAX_BUF_SIZE 1024

int LLVMFuzzerTestOneInput(const uint8_t* data, size_t size) {
    if (data == NULL || size == 0) {
        return 0;
    }

    // create decompression structure
    struct jpeg_decompress_struct *cinfo;
    cinfo = malloc(sizeof(struct jpeg_decompress_struct));
    jpeg_CreateDecompress(cinfo, JPEG_LIB_VERSION, sizeof(struct jpeg_decompress_struct));

    // allocate some space
    JOCTET *outbuffer = malloc(MAX_BUF_SIZE);
    if (outbuffer == NULL) {
        exit(EXIT_FAILURE);
    }

    // calling jpeg_mem_src
    jpeg_mem_src(cinfo, outbuffer, MAX_BUF_SIZE);

    jpeg_read_header(cinfo, TRUE);
    jpeg_start_decompress(cinfo);

    IOCTET *icc_profile;
    unsigned int icc_profile_size;
    jpeg_read_icc_profile(cinfo, &icc_profile, &icc_profile_size);

    // Processing while can continue to read scanlines
    while (cinfo->output_scanline < cinfo->output_height) {
        // Allocate memory for buffers
        JSAMPARRAY buffer = (*cinfo->mem->alloc_sarray)
                ((j_common_ptr) &cinfo, JPOOL_IMAGE, cinfo->output_width * cinfo->output_components, 1);
        jpeg_read_scanlines(cinfo, buffer, 1);
    }

    jpeg_finish_decompress(cinfo);
    jpeg_destroy_decompress(cinfo);
    fclose(outbuffer);
    free(outbuffer);

    return 0;
}
```
This simple example does not cover all functions but should illustrate how fuzz testing with LibFuzzer might be implemented for the libjpeg-turbo project.
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