# LaTeX（XeLaTeX）一键编译并清理中间产物
# 用法：cd docs && make              # 默认主文件见 MAIN
#       cd docs && make MAIN=report  # 编译其它主文件（不含 .tex 后缀）

MAIN ?= prof-finder-tech-selection-architecture

LATEX_INTERMEDIATE := \
	$(MAIN).aux \
	$(MAIN).log \
	$(MAIN).out \
	$(MAIN).toc \
	$(MAIN).synctex.gz \
	$(MAIN).fdb_latexmk \
	$(MAIN).fls \
	$(MAIN).nav \
	$(MAIN).snm \
	$(MAIN).vrb

.PHONY: all pdf clean distclean

all pdf: $(MAIN).pdf

$(MAIN).pdf: $(MAIN).tex
	xelatex -interaction=nonstopmode $(MAIN)
	xelatex -interaction=nonstopmode $(MAIN)
	$(RM) $(LATEX_INTERMEDIATE)

clean:
	$(RM) $(LATEX_INTERMEDIATE)

distclean: clean
	$(RM) $(MAIN).pdf
