#include <stdlib.h>
#include <stdint.h>
#include <stdio.h>   // 定义 FILE 类型
#include <string.h>
#include "jpeglib.h" // libjpeg 库的主头文件

// LibFuzzer 测试入口点
int LLVMFuzzerTestOneInput(const uint8_t *data, size_t size) {
    if (data == NULL || size == 0) {
        return 0;
    }

    // 初始化 JPEG 解压缩结构体
    struct jpeg_decompress_struct cinfo;
    struct jpeg_error_mgr jerr;

    // 设置默认错误处理程序
    cinfo.err = jpeg_std_error(&jerr);

    // 创建解压缩对象
    jpeg_create_decompress(&cinfo);

    // 将输入数据包装为内存输入流
    jpeg_mem_src(&cinfo, data, size);

    // 尝试读取 JPEG 文件头
    if (jpeg_read_header(&cinfo, TRUE) != JPEG_HEADER_OK) {
        jpeg_destroy_decompress(&cinfo);
        return 0;
    }

    // 开始解压缩
    if (!jpeg_start_decompress(&cinfo)) {
        jpeg_destroy_decompress(&cinfo);
        return 0;
    }

    // 创建缓冲区以保存解压缩的扫描线
    int row_stride = cinfo.output_width * cinfo.output_components;
    JSAMPARRAY buffer = (*cinfo.mem->alloc_sarray)
        ((j_common_ptr)&cinfo, JPOOL_IMAGE, row_stride, 1);

    // 解压每一行
    while (cinfo.output_scanline < cinfo.output_height) {
        jpeg_read_scanlines(&cinfo, buffer, 1);
        // 您可以在这里处理扫描线数据（buffer[0]）
    }

    // 结束解压缩并清理
    jpeg_finish_decompress(&cinfo);
    jpeg_destroy_decompress(&cinfo);

    return 0;
}
