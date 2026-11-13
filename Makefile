.PHONY: test validate verify-generated regenerate test-tools

# CI 跑的就是这个目标
test: validate verify-generated test-tools

validate:
	python3 scripts/validate.py

# 生成文件与 VERSION、skills/ 不一致时失败
verify-generated:
	python3 scripts/build_metadata.py --check

# 改了 VERSION 或 skills/ 后运行，生成结果和源文件一起提交
regenerate:
	python3 scripts/build_metadata.py

# 确定性脚本测试，不调用模型或真实远端
test-tools:
	python3 -m unittest discover -s tests -v
