import os
from os import listdir
from os.path import isfile, join, abspath

import logging
import shutil
import subprocess
from typing import List, Tuple

import jinja2


class BuildFolder(object):
    def __init__(self, build_folder):
        self.build_folder = build_folder
        try:
            os.mkdir(self.build_folder)
        except:
            pass

    def __enter__(self):
        pass

    def __exit__(self, *_):
        shutil.rmtree(self.build_folder)


class Config:
    build_folder = "temp-build"
    pdf_folder = os.path.join(build_folder, "temp-pdf")
    mscz_folder = "MsczFiles"
    target_folder = "RealBook"

    pdflatex_cmd = "pdflatex"
    musescore_cmd = "MuseScore3"
    latex_template = "realbook.template.tex"

    output_pdf = ""
    key = "C"


class Files:
    @classmethod
    def get_files(cls, folder):
        return [join(folder, f) for f in listdir(folder) if isfile(join(folder, f))]


class Controller:
    def __init__(self):
        self.version = "0.1.2"

    def render_mscz_parts(self, mscz_file, pdf_file):
        import sys
        import os
        import json
        import subprocess
        import xml.etree.ElementTree as et

        if len(sys.argv) < 2:
            print("Usage: getPartNames.py <filename>")
            exit

        inFile = sys.argv[1]
        filename, fileExtention = os.path.splitext(inFile)
        mscx = filename + ".mscx"

        if fileExtention not in [".mscx", ".mscz"]:
            print("Unknown file extention: " + fileExtention)
            exit

        if fileExtention == ".mscz":
            proc = subprocess.Popen(["musescore", "-o", mscx, "-P", inFile])
            proc.wait()

        tree = et.parse(mscx)

        scoreList = []

        for score in tree.iter("Score"):
            scoreList.append(score)

        data = []
        partList = []

        for i in range(len(scoreList) - 1):
            name = ""
            for trackName in scoreList[i + 1].iter("trackName"):
                name = trackName.text
                partList.append(trackName)
                break

            tree.getroot().remove(scoreList[i])
            tree.getroot().append(scoreList[i + 1])

            partFileBase = filename + "-" + name
            partFile = partFileBase + ".mscx"
            entry = {}
            entry["in"] = partFile
            entry["out"] = partFileBase + ".pdf"
            data.append(entry)
            tree.write(partFile)

        jsonfile = filename + ".json"
        with open(jsonfile, "w") as outfile:
            json.dump(data, outfile)

        proc = subprocess.Popen(["musescore", "-j", jsonfile])
        proc.wait()

    def create_latex(self, latex_template, pdfs):
        latex_jinja_env = jinja2.Environment(
            block_start_string="\\BLOCK{",
            block_end_string="}",
            variable_start_string="\\VAR{",
            variable_end_string="}",
            comment_start_string="\\#{",
            comment_end_string="}",
            line_statement_prefix="%%",
            line_comment_prefix="%#",
            trim_blocks=True,
            autoescape=False,
            loader=jinja2.FileSystemLoader(os.path.abspath(".")),
        )
        template = latex_jinja_env.get_template(latex_template)
        latex_rendered = template.render(pdfs=pdfs, key=Config.key)
        return latex_rendered

    def render_latex(self, latex_rendered, pdf_output_filename):
        rendered_filename = os.path.abspath(
            os.path.join(Config.build_folder, f"RealBook-{self.version}.tex")
        )
        with open(rendered_filename, "w") as f:
            f.write(latex_rendered)

        cmd = [
            Config.pdflatex_cmd,
            "-output-directory",
            Config.build_folder,
            rendered_filename,
        ]
        logging.debug("Running Cmd: " + " ".join(cmd))
        result = subprocess.run(cmd)
        result = subprocess.run(cmd)
        if result.returncode != 0:
            raise Exception(f"Cmd failed: {cmd}")

        shutil.copy(rendered_filename.replace(".tex", ".pdf"), pdf_output_filename)

    def render_mscz(self) -> List[Tuple[str, str]]:
        mscz_files = Files.get_files(Config.mscz_folder)
        pdf_files = []
        for mscz_file in mscz_files:
            pdf_file = mscz_file.replace(Config.mscz_folder, Config.pdf_folder).replace(
                ".mscz", ".pdf"
            )
            song_name = (
                pdf_file.split("\\")[-1].replace(".pdf", "").replace("_", " ").title()
            )

            cmd = [Config.musescore_cmd, mscz_file, "-o", pdf_file]
            logging.info(f"Exporting PDF: {mscz_file} -> {pdf_file}")
            logging.debug("Running Cmd: " + " ".join(cmd))
            result = subprocess.run(cmd)
            if result.returncode != 0:
                raise Exception(f"Cmd failed: {cmd}")
            pdf_file = pdf_file.replace("\\", "/")
            pdf_files.append((pdf_file, song_name))

            # self.render_mscz_parts()

        return pdf_files

    def main(self):
        logging.basicConfig(level=logging.DEBUG)

        latex_output_filename = os.path.abspath(
            os.path.join(Config.build_folder, f"RealBook-{self.version}.tex")
        )
        pdf_output_filename = latex_output_filename.replace(".tex", ".pdf").replace(
            Config.build_folder, Config.target_folder
        )

        build_folder = abspath(Config.build_folder)
        pdf_folder = abspath(Config.pdf_folder)
        with BuildFolder(build_folder), BuildFolder(pdf_folder):
            pdfs = self.render_mscz()
            latex_rendered = self.create_latex(Config.latex_template, pdfs)
            self.render_latex(latex_rendered, pdf_output_filename)
            logging.info("DONE!")


if __name__ == "__main__":
    Controller().main()
