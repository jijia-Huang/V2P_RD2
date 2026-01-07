# -*- coding: utf-8 -*-
"""
檢查 Gradio 的所有依賴和子模組
用於 PyInstaller 打包配置
"""
import sys
import importlib
from pathlib import Path
from PyInstaller.utils.hooks import collect_submodules, collect_data_files

def check_module_deps(module_name):
    """檢查模組的所有依賴和子模組"""
    separator = "=" * 60
    print("\n" + separator)
    print("檢查模組: " + module_name)
    print(separator)
    
    try:
        # 收集子模組
        submodules = collect_submodules(module_name)
        print("\n子模組數量: " + str(len(submodules)))
        print("前 20 個子模組:")
        for i, submod in enumerate(sorted(submodules)[:20], 1):
            print("  " + str(i) + ". " + submod)
        if len(submodules) > 20:
            print("  ... 還有 " + str(len(submodules) - 20) + " 個子模組")
        
        # 收集數據檔案
        datas = collect_data_files(module_name)
        print("\n數據檔案數量: " + str(len(datas)))
        if datas:
            print("數據檔案列表:")
            for i, (src, dst) in enumerate(datas[:10], 1):
                print("  " + str(i) + ". " + str(src) + " -> " + str(dst))
            if len(datas) > 10:
                print("  ... 還有 " + str(len(datas) - 10) + " 個數據檔案")
        
        # 檢查版本檔案
        try:
            module = importlib.import_module(module_name)
            if hasattr(module, '__file__') and module.__file__:
                module_path = Path(module.__file__).parent
                print("\n模組路徑: " + str(module_path))
                
                # 檢查常見的版本檔案
                version_files = ['version.txt', 'types.json', 'VERSION', '__version__.py']
                print("\n版本檔案檢查:")
                for vf in version_files:
                    vf_path = module_path / vf
                    if vf_path.exists():
                        print("  ✓ " + vf + " 存在")
                    else:
                        print("  ✗ " + vf + " 不存在")
        except Exception as e:
            print("\n無法檢查模組路徑: " + str(e))
        
        return submodules, datas
        
    except Exception as e:
        print("\n錯誤: " + str(e))
        return [], []

def check_package_deps(package_name):
    """檢查套件的依賴"""
    try:
        import pkg_resources
        dist = pkg_resources.get_distribution(package_name)
        print("\n套件版本: " + dist.version)
        print("\n直接依賴:")
        for req in dist.requires():
            print("  - " + str(req))
    except Exception as e:
        print("\n無法檢查套件依賴: " + str(e))

if __name__ == "__main__":
    # 檢查 Gradio 相關模組
    gradio_modules = [
        'gradio',
        'gradio_client',
        'safehttpx',
        'groovy',
    ]
    
    all_submodules = {}
    all_datas = {}
    
    for module_name in gradio_modules:
        submodules, datas = check_module_deps(module_name)
        all_submodules[module_name] = submodules
        all_datas[module_name] = datas
        
        # 檢查套件依賴
        check_package_deps(module_name)
    
    # 總結
    separator = "=" * 60
    print("\n\n" + separator)
    print("總結")
    print(separator)
    print("\n建議的 hiddenimports 配置:")
    print("hiddenimports = [")
    for module_name in gradio_modules:
        print("    '" + module_name + "',")
    print("] + \\")
    for module_name in gradio_modules:
        print("    collect_submodules('" + module_name + "') + \\")
    print("    [")
    print("    # 其他模組...")
    print("    ]")
    
    print("\n建議的 datas 配置:")
    print("datas = [")
    for module_name in gradio_modules:
        print("    # " + module_name + " 數據檔案")
        print("    *collect_data_files('" + module_name + "'),")
    print("    # 其他數據檔案...")
    print("]")

