# Build the technical report.
#
#   make          build report.pdf
#   make figures  regenerate the figures from the analysis data
#   make clean    remove LaTeX build artefacts
#   make cleanall also remove report.pdf

VENV_PYTHON := ../.venv/bin/python3

.PHONY: all figures clean cleanall

all: report.pdf

report.pdf: report.tex references.bib $(wildcard figures/*.pdf)
	pdflatex -interaction=nonstopmode report.tex
	bibtex report
	pdflatex -interaction=nonstopmode report.tex
	pdflatex -interaction=nonstopmode report.tex

figures:
	$(VENV_PYTHON) make_figures.py

clean:
	rm -f report.aux report.bbl report.blg report.log report.out report.toc

cleanall: clean
	rm -f report.pdf
