import subprocess
import sys
import os


def convert_ipynb_to_pdf(notebook_path):
    if not os.path.exists(notebook_path):
        print(f"错误: 找不到文件 {notebook_path}")
        return

    print(f"开始转换: {notebook_path}")
    print("正在生成 PDF 中，请稍候...")

    # 组装转换命令：调用当前 Python 环境下的 jupyter nbconvert
    # 使用 webpdf 引擎可以完美支持中文排版
    cmd = [
        sys.executable,
        "-m",
        "jupyter",
        "nbconvert",
        "--to",
        "webpdf",
        "--allow-chromium-download",  # 允许自动下载所需的无头浏览器
        notebook_path,
    ]

    try:
        # 执行命令
        subprocess.run(cmd, check=True)

        pdf_path = notebook_path.replace(".ipynb", ".pdf")
        print(f"\n✅ 转换成功！PDF 文件已生成: {pdf_path}")

    except subprocess.CalledProcessError as e:
        print("\n❌ 转换失败。")
        print("请检查是否安装了相关依赖，你可以在终端运行以下命令来安装：")
        print("pip install nbconvert[webpdf]")
    except FileNotFoundError:
        print("\n❌ 找不到 jupyter 命令，请确保你在正确的 Python 环境中并安装了 jupyter。")


if __name__ == "__main__":
    # 指定需要转换的 Notebook 文件名
    target_notebook = "Lab2-MongoDB.ipynb"
    convert_ipynb_to_pdf(target_notebook)
