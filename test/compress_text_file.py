import gzip

def compress_text_file(input_file, output_file):
    with open(input_file, 'rb') as f_in:
        with gzip.open(output_file, 'wb') as f_out:
            f_out.writelines(f_in)

# 示例用法
input_file = '../assets/_config.example.yml'
output_file = '../assets/template.gz'

compress_text_file(input_file, output_file)