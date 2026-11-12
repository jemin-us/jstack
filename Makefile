.PHONY: test validate verify-generated regenerate

# CI 跑的就是这个目标
test: validate verify-generated

validate:
	python3 scripts/validate.py

# 生成文件与 VERSION、skills/ 不一致时失败
verify-generated:
	python3 scripts/build_metadata.py --check

# 改了 VERSION 或 skills/ 后运行，生成结果和源文件一起提交
regenerate:
	python3 scripts/build_metadata.py
