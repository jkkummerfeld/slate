name=acl19slate
tex=pdflatex
bib=bibtex

all: paper

paper: *.tex *.bib
	$(tex) ${name}
	${bib} ${name}
	$(tex) ${name}
	$(tex) ${name}

tex: *.tex
	$(tex) ${name}

note: post-publish-supp.tex
	${tex} post-publish-supp
	${bib} post-publish-supp
	${tex} post-publish-supp
	${tex} post-publish-supp

clean:
	rm ${name}.aux ${name}.bbl ${name}.bcf ${name}.blg ${name}.lof ${name}.log ${name}.lot ${name}.run.xml ${name}.toc ${name}.out

