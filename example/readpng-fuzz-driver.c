#include <stdint.h>
#include <stdlib.h>
#include <string.h>
#include "png.h"
#include <setjmp.h>

struct read_data {
    const uint8_t *data;
    size_t size;
    size_t offset;
};

void custom_read_fn(png_structp png_ptr, png_bytep outBytes, png_size_t byteCountToRead) {
    struct read_data *read_data = (struct read_data*)png_get_io_ptr(png_ptr);

    if (read_data->offset + byteCountToRead > read_data->size) {
        png_error(png_ptr, "Read Error");
        return;
    }

    memcpy(outBytes, read_data->data + read_data->offset, byteCountToRead);
    read_data->offset += byteCountToRead;
}

int LLVMFuzzerTestOneInput(const uint8_t *data, size_t size) {
    if (data == NULL || size < 8) {
        return 0;
    }

    // 检查PNG文件签名
    if (png_sig_cmp(data, 0, 8)) {
        return 0;
    }

    png_structp png_ptr = NULL;
    png_infop info_ptr = NULL;
    png_byte *row = NULL;

    // 创建PNG读结构
    png_ptr = png_create_read_struct(PNG_LIBPNG_VER_STRING, NULL, NULL, NULL);
    if (!png_ptr) {
        return 0;
    }

    // 创建PNG信息结构
    info_ptr = png_create_info_struct(png_ptr);
    if (!info_ptr) {
        png_destroy_read_struct(&png_ptr, NULL, NULL);
        return 0;
    }

    // 设置错误处理
    if (setjmp(png_jmpbuf(png_ptr))) {
        png_destroy_read_struct(&png_ptr, &info_ptr, NULL);
        free(row);
        return 0;
    }

    // 设置自定义读取函数
    struct read_data read_data = {data, size, 8}; // 跳过PNG签名
    png_set_read_fn(png_ptr, &read_data, custom_read_fn);

    // 读取PNG信息
    png_read_info(png_ptr, info_ptr);

    // 获取图片信息
    png_uint_32 width, height;
    int bit_depth, color_type;
    if (!png_get_IHDR(png_ptr, info_ptr, &width, &height, &bit_depth, &color_type, NULL, NULL, NULL)) {
        png_destroy_read_struct(&png_ptr, &info_ptr, NULL);
        return 0;
    }

    // 分配行缓冲区
    png_size_t rowbytes = png_get_rowbytes(png_ptr, info_ptr);
    row = (png_byte*)malloc(rowbytes);
    if (!row) {
        png_destroy_read_struct(&png_ptr, &info_ptr, NULL);
        return 0;
    }

    // 设置隔行处理
    png_set_interlace_handling(png_ptr);

    // 开始读取图片
    png_start_read_image(png_ptr);

    // 读取行数据
    for (png_uint_32 y = 0; y < height; y++) {
        png_read_row(png_ptr, row, NULL);
    }

    // 完成读取
    png_read_end(png_ptr, info_ptr);

    // 清理
    free(row);
    png_destroy_read_struct(&png_ptr, &info_ptr, NULL);

    return 0;
}
